from django.contrib import admin
from .models import Members

class TaskMembers(admin.ModelAdmin):
    list_display=["username","first_name","last_name","email","phone_number","branch_id"] #แสดงข้อมูลในหน้า Admin


# Register your models here.
admin.site.register(Members,TaskMembers) #นำข้อมูล Class ใน Model มาแสดงที่หน้า Admin