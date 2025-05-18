from django.contrib.auth.models import AbstractUser
from django.db import models
from branch.models import Branch
from department.models import Department
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in


class Members(AbstractUser):
    # เพิ่ม field ใหม่
    phone_number = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, blank=True, null=True)

    is_staff = models.IntegerField(choices=[(0, 'False'), (1, 'True')], default=0)
    is_active = models.IntegerField(choices=[(0, 'False'), (1, 'True')], default=1)
    is_superuser = models.IntegerField(choices=[(0, 'False'), (1, 'True')], default=0)
    date_joined = models.DateTimeField()
    last_login = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        db_table = "members"  # กำหนดชื่อ table ในฐานข้อมูล

    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        if self.last_login:
            self.last_login = self.last_login.replace(microsecond=0)
        if self.date_joined:
            self.date_joined = self.date_joined.replace(microsecond=0)
        if not self.date_joined:
            self.date_joined = timezone.now().replace(microsecond=0)
             
        super().save(*args, **kwargs)   
    


