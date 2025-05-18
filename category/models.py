from django.db import models
from department.models import Department

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255,unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE,blank=True,null=True)

    class Meta:
        db_table = "base_category"  # กำหนดชื่อ table ในฐานข้อมูล

    def __str__(self):
        return self.name