from django.db import models

# Create your models here.
class Branch(models.Model):
    branch_id = models.CharField(max_length=255,primary_key=True)
    branch_name = models.CharField(max_length=255,unique=True)

    class Meta:
        db_table = "base_branch"  # กำหนดชื่อ table ในฐานข้อมูล

    def __str__(self):
        return self.branch_name