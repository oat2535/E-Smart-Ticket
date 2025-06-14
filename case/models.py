from django.db import models,connection
from category.models import Category
from sub_category.models import SubCategory
from status.models import Status
from branch.models import Branch
from sub_branch.models import SubBranch
from department.models import Department
from priority.models import Priority
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Case(models.Model):
    
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    ticket_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=255)
    case_detail = models.TextField(blank=True)
    subject_detail = models.CharField(max_length=255,blank=True)
    ip_address = models.CharField(max_length=255)
    email = models.CharField(max_length=255,blank=True)
    computer_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="blogImages",blank=True,null=True)
    create_username = models.CharField(max_length=255)
    date_created = models.DateTimeField()
    assign_name = models.CharField(max_length=255,blank=True)
    update_note = models.TextField(blank=True)
    modify_date = models.DateTimeField()
    modify_username = models.CharField(max_length=255,blank=True)
    complete_date = models.DateTimeField(null=True, blank=True, default=None)
    receive_date = models.DateTimeField(null=True, blank=True, default=None)
    satisfied_date = models.DateTimeField(null=True, blank=True, default=None)
    satisfied_name = models.CharField(max_length=255,blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True, blank=True, default=None)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL,null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.CASCADE,default=1,null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    sub_branch = models.ForeignKey(SubBranch, on_delete=models.SET_NULL,null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    priority = models.ForeignKey(Priority, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=255,blank=True)
    score = models.IntegerField(null=True, blank=True, default=0)
    feedback = models.TextField(null=True, blank=True)
    cancel_date = models.DateTimeField(null=True, blank=True, default=None)
    cancel_name = models.CharField(max_length=255,blank=True)
    product_receive_date = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        db_table = "case_list"  # กำหนดชื่อ table ในฐานข้อมูล

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
    # ลบ microsecond ออกจากฟิลด์วันที่ หากมีค่า
        if self.date_created:
            self.date_created = self.date_created.replace(microsecond=0)
        if self.modify_date:
            self.modify_date = self.modify_date.replace(microsecond=0)
        if self.complete_date:
            self.complete_date = self.complete_date.replace(microsecond=0)
        if self.receive_date:
            self.receive_date = self.receive_date.replace(microsecond=0)
        if self.satisfied_date:
            self.satisfied_date = self.satisfied_date.replace(microsecond=0)
        
        # เช็คถ้า date_created ยังไม่ได้กำหนด ให้ตั้งเป็นเวลาปัจจุบัน
        if not self.date_created:
            self.date_created = timezone.now().replace(microsecond=0)
        
        # เช็คถ้า modify_date ยังไม่ได้กำหนด ให้ตั้งเป็นเวลาปัจจุบัน
        if not self.modify_date:
            self.modify_date = timezone.now().replace(microsecond=0)
        
        super().save(*args, **kwargs)   


        