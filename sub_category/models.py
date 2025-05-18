from django.db import models
from category.models import Category

class SubCategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,blank=True,null=True)

    class Meta:
        db_table = "base_sub_category"  # ตั้งชื่อ table ในฐานข้อมูล

    def __str__(self):
        return f"{self.name} ({self.category.name})"
