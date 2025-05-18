from django.db import models

# Create your models here.
class Status(models.Model):
    name = models.CharField(max_length=255,unique=True)

    class Meta:
        db_table = "base_status"  # กำหนดชื่อ table ในฐานข้อมูล

    def __str__(self):
        return self.name