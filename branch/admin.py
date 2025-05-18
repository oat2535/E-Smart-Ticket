from django.contrib import admin
from .models import Branch

class TaskBranch(admin.ModelAdmin):
    list_display=["branch_id","branch_name"]


# Register your models here.
admin.site.register(Branch,TaskBranch) #นำข้อมูล Class ใน Model มาแสดงที่หน้า Admin