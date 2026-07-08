from django.db import models
from django.conf import settings
from branch.models import Branch
from sub_branch.models import SubBranch
class AssetCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class AssetLocation(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class MasterAsset(models.Model):
    image = models.ImageField(upload_to='assets_images/', null=True, blank=True, verbose_name='รูปภาพ')
    category = models.CharField(max_length=255, null=True, blank=True, verbose_name='หมวด')
    asset_code = models.CharField(max_length=50, verbose_name='รหัสทรัพย์สิน')
    name = models.CharField(max_length=255, verbose_name='ชื่อ')
    company = models.CharField(max_length=100, null=True, blank=True, verbose_name='บริษัท')
    branch = models.CharField(max_length=100, null=True, blank=True, verbose_name='สาขา')
    department = models.CharField(max_length=100, null=True, blank=True, verbose_name='แผนก')
    building = models.CharField(max_length=100, null=True, blank=True, verbose_name='อาคาร')
    floor = models.CharField(max_length=50, null=True, blank=True, verbose_name='ชั้น')
    responsible_person = models.CharField(max_length=200, null=True, blank=True, verbose_name='ผู้รับผิดชอบ')
    serial_number = models.CharField(max_length=100, null=True, blank=True, verbose_name='หมายเลขเครื่อง')
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='ราคา')
    purchase_date = models.DateTimeField(null=True, blank=True, verbose_name='วันที่ซื้อ')
    supplier = models.CharField(max_length=255, null=True, blank=True, verbose_name='บริษัท(ขาย)')
    warranty = models.DateTimeField(null=True, blank=True, verbose_name='ประกัน')
    maintenance_unit = models.CharField(max_length=100, null=True, blank=True, verbose_name='หน่วยช่าง')
    
    STATUS_CHOICES = [
        ('available', 'ปกติ (Normal)'),
        ('in_use', 'กำลังใช้งาน (In-Use)'),
        ('maintenance', 'ส่งซ่อม (Under Maintenance)'),
        ('written_off', 'ชำรุด (Written-off)'),
        ('disposed', 'จำหน่ายแล้ว (Disposed)'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='available', verbose_name='สถานะ')
    old_asset_code = models.CharField(max_length=50, null=True, blank=True, verbose_name='รหัสทรัพย์สินเดิม')
    remark = models.TextField(null=True, blank=True, verbose_name='หมายเหตุ')

    ax_status = models.IntegerField(null=True, blank=True, verbose_name='AX Status')
    ax_reason = models.TextField(null=True, blank=True, verbose_name='AX Reason')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.asset_code}] {self.name}"

class SubAsset(models.Model):
    master_asset = models.ForeignKey(MasterAsset, on_delete=models.CASCADE, related_name='sub_assets')
    name = models.CharField(max_length=255) # e.g. "RAM 16GB"
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.master_asset.asset_code} - {self.name}"

class AssetTransfer(models.Model):
    asset = models.ForeignKey(MasterAsset, on_delete=models.CASCADE, related_name='transfers')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='transfers_from')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_to')
    
    from_company = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_from_company', verbose_name='บริษัทต้นทาง')
    from_branch = models.ForeignKey(SubBranch, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_from_branch', verbose_name='สาขาต้นทาง')
    
    to_company = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='บริษัทที่โอนย้ายถึง')
    to_branch = models.ForeignKey(SubBranch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='สาขาที่โอนย้ายถึง')
    
    reason = models.TextField()
    reject_reason = models.TextField(null=True, blank=True, verbose_name="เหตุผลที่ไม่อนุมัติ")
    
    STATUS_CHOICES = [
        ('pending_source_head', 'รอหัวหน้าสาขาต้นทางอนุมัติ'),
        ('pending_destination_receive', 'รอสาขาปลายทางรับสินค้า'),
        ('pending_destination_head', 'รอหัวหน้าสาขาปลายทางอนุมัติ'),
        ('pending_accounting', 'รอบัญชีอนุมัติ'),
        ('approved', 'อนุมัติแล้ว'),
        ('rejected', 'ไม่อนุมัติ'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending_source_head')
    
    head_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_head_approvals', verbose_name='ผู้จัดการสาขาต้นทางที่อนุมัติ')
    destination_received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_dest_receivers', verbose_name='พนักงานสาขาปลายทางที่รับสินค้า')
    destination_head_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_dest_head_approvals', verbose_name='ผู้จัดการสาขาปลายทางที่อนุมัติ')
    accounting_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_acc_approvals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class MaintenanceRecord(models.Model):
    asset = models.ForeignKey(MasterAsset, on_delete=models.CASCADE, related_name='maintenances')
    sub_asset = models.ForeignKey(SubAsset, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenances')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    issue_description = models.TextField()
    reject_reason = models.TextField(null=True, blank=True, verbose_name="เหตุผลที่ไม่อนุมัติ")
    
    STATUS_CHOICES = [
        ('pending_it_approval', 'รอ IT อนุมัติ'),
        ('pending', 'รอดำเนินการ'),
        ('in_progress', 'กำลังซ่อม'),
        ('completed', 'ซ่อมเสร็จสิ้น'),
        ('rejected', 'ไม่อนุมัติ'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending_it_approval')
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    service_job = models.CharField(max_length=50, null=True, blank=True, verbose_name="Service Job (Ticket)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class MaintenanceImage(models.Model):
    maintenance = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to='maintenance_images/')
    created_at = models.DateTimeField(auto_now_add=True)

class AssetWriteOff(models.Model):
    asset = models.ForeignKey(MasterAsset, on_delete=models.CASCADE, related_name='write_offs')
    assessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='writeoff_assessments', verbose_name="IT ประเมิน")
    reason = models.TextField()
    reject_reason = models.TextField(null=True, blank=True, verbose_name="เหตุผลที่ไม่อนุมัติ")
    
    STATUS_CHOICES = [
        ('pending_staff', 'รอ Staff รับทราบ'),
        ('pending_head', 'รอหัวหน้าอนุมัติ'),
        ('pending_accounting', 'บัญชีทำรายการออก'),
        ('completed', 'เสร็จสิ้น'),
        ('rejected', 'ปฏิเสธ'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_staff')
    
    staff_acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='writeoff_staff_acks')
    head_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='writeoff_head_approvals')
    accounting_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='writeoff_acc_approvals')

    created_at = models.DateTimeField(auto_now_add=True)

class AssetDisposal(models.Model):
    asset = models.ForeignKey(MasterAsset, on_delete=models.CASCADE, related_name='disposals')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='disposal_requests')
    reason = models.TextField()
    reject_reason = models.TextField(null=True, blank=True, verbose_name="เหตุผลที่ไม่อนุมัติ")
    
    STATUS_CHOICES = [
        ('pending_head', 'รอหัวหน้าอนุมัติ'),
        ('pending_accounting', 'รอบัญชีอนุมัติ'),
        ('approved', 'อนุมัติแล้ว'),
        ('rejected', 'ปฏิเสธ'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_head')
    
    head_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='disposal_head_approvals')
    accounting_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='disposal_acc_approvals')

    created_at = models.DateTimeField(auto_now_add=True)

class DisposalImage(models.Model):
    disposal = models.ForeignKey(AssetDisposal, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='disposal_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class AssetImage(models.Model):
    asset = models.ForeignKey(MasterAsset, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='assets_additional_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class AssetInventory(models.Model):
    asset = models.ForeignKey(MasterAsset, on_delete=models.CASCADE, related_name='inventories')
    scanned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    STATUS_CHOICES = [
        ('normal', 'ปกติ (Normal)'),
        ('damaged_repairable', 'ชำรุด-ซ่อมได้ (Damaged - Repairable)'),
        ('damaged_unrepairable', 'ชำรุด-ซ่อมไม่ได้ (Damaged - Unrepairable)'),
        ('missing', 'สูญหาย (Missing)'),
    ]
    asset_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal', verbose_name='สภาพทรัพย์สิน')
    location_scanned = models.CharField(max_length=255, null=True, blank=True, verbose_name='สถานที่ตรวจพบ')
    note = models.TextField(blank=True, null=True, verbose_name='หมายเหตุ')
    scanned_at = models.DateTimeField(auto_now_add=True)
