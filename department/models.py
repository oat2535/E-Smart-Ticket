from django.db import models

# Create your models here.
class Department(models.Model):
    department_id = models.CharField(max_length=255,primary_key=True)
    department_name = models.CharField(max_length=255,unique=True)

    class Meta:
        db_table = "base_department"  # กำหนดชื่อ table ในฐานข้อมูล

    def __str__(self):
        return self.department_name