from django.db import models
from django.conf import settings
from department.models import Department

class System(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class AccessRequest(models.Model):
    STATUS_CHOICES = [
        ('pending_manager', 'รอหัวหน้าอนุมัติ (Wait for Manager)'),
        ('pending_it', 'รอ IT อนุมัติ (Wait for IT)'),
        ('approved', 'อนุมัติแล้ว (Approved)'),
        ('rejected', 'ไม่อนุมัติ (Rejected)'),
    ]
    



    # Info
    request_code = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='access_requests', null=True, blank=True)
    
    PREFIX_CHOICES = [
        ('mr', 'นาย/Mr.'),
        ('mrs', 'นาง/Mrs.'),
        ('miss', 'นางสาว/Miss'),
        ('dr_m', 'น.สพ./Dr.'),
        ('dr_f', 'สพ.ญ./Dr.'),
        ('other', 'อื่นๆ'),
    ]

    # Personnel Details
    employee_id = models.CharField(max_length=20, verbose_name="รหัสพนักงาน")
    email = models.EmailField(verbose_name="E-mail")
    prefix = models.CharField(max_length=20, choices=PREFIX_CHOICES, verbose_name="คำนำหน้าชื่อ")
    prefix_other = models.CharField(max_length=100, blank=True, null=True, verbose_name="คำนำหน้าชื่อ (อื่นๆ)")
    prefix_th = models.CharField(max_length=20, blank=True, null=True, verbose_name="คำนำหน้า (ไทย)")
    prefix_en = models.CharField(max_length=20, blank=True, null=True, verbose_name="คำนำหน้า (อังกฤษ)")
    firstname_th = models.CharField(max_length=150, verbose_name="ชื่อ (ไทย)", default="")
    lastname_th = models.CharField(max_length=150, verbose_name="นามสกุล (ไทย)", default="")
    firstname_en = models.CharField(max_length=150, verbose_name="ชื่อ (อังกฤษ)", default="")
    lastname_en = models.CharField(max_length=150, verbose_name="นามสกุล (อังกฤษ)", default="")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name="แผนก")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, verbose_name="ตำแหน่ง")

    # Request Details
    systems = models.ManyToManyField(System)
    reason = models.TextField()
    
    # State
    # State
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_manager')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Approval Tracking
    manager_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_approvals', verbose_name="ผู้อนุมัติ (Manager)")
    manager_approval_date = models.DateTimeField(null=True, blank=True)
    manager_comment = models.TextField(blank=True, null=True, verbose_name="ความเห็น Manager")
    
    it_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='it_approvals', verbose_name="ผู้อนุมัติ (IT)")
    it_approval_date = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True, null=True, verbose_name="เหตุผลที่ปฏิเสธ")
    rejected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_requests', verbose_name="ผู้ปฏิเสธ")
    rejected_at = models.DateTimeField(null=True, blank=True, verbose_name="วันที่ปฏิเสธ")

    def save(self, *args, **kwargs):
        prefix_map = {
            'mr': ('นาย', 'Mr.'),
            'mrs': ('นาง', 'Mrs.'),
            'miss': ('นางสาว', 'Miss'),
            'dr_m': ('น.สพ.', 'Dr.'),
            'dr_f': ('สพ.ญ.', 'Dr.'),
        }
        if self.prefix in prefix_map:
            self.prefix_th, self.prefix_en = prefix_map[self.prefix]
            
        if not self.request_code:
            # Find the last created request to determine the next code
            last_request = AccessRequest.objects.all().order_by('id').last()
            if last_request and last_request.request_code.startswith('REQ-'):
                try:
                    last_id = int(last_request.request_code.split('-')[1])
                    new_id = last_id + 1
                except (IndexError, ValueError):
                    # Fallback if format is unexpected
                    new_id = AccessRequest.objects.count() + 1
            else:
                new_id = 1
            
            self.request_code = f"REQ-{new_id:04d}"
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_code} - {self.firstname_en} {self.lastname_en}"

class AccessRequestLog(models.Model):
    access_request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE, related_name='logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="ผู้ดำเนินการ")
    action = models.CharField(max_length=50, verbose_name="การกระทำ")
    details = models.TextField(blank=True, null=True, verbose_name="รายละเอียด")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.timestamp} - {self.actor} - {self.action}"
