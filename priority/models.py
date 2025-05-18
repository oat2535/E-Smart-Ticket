from django.db import models

# Create your models here.
class Priority(models.Model):
    priority_name = models.CharField(max_length=255,unique=True)

    class Meta:
        db_table = "base_priority"  # กำหนดชื่อ table ในฐานข้อมูล

    def __str__(self):
        return self.priority_name