from django.db import models
from branch.models import Branch

# Create your models here.
class SubBranch(models.Model):
    sub_branch_id = models.CharField(max_length=255,primary_key=True)
    sub_branch_name = models.CharField(max_length=255,blank=True,null=True)
    branch_id = models.ForeignKey(Branch, on_delete=models.CASCADE,blank=True,null=True)

    class Meta:
        db_table = "base_sub_branch"  # กำหนดชื่อ table ในฐานข้อมูล

    def __str__(self):
        return self.sub_branch_name 