from django.db import models
from sub_category.models import SubCategory

class SecondSubCategory(models.Model):
    name = models.CharField(max_length=255)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE,blank=True,null=True)

    class Meta:
        db_table = "base_second_sub_category"  # ตั้งชื่อ table ในฐานข้อมูล

    def __str__(self):
        return f"{self.name} ({self.sub_category.name})"