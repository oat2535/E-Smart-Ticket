from django.contrib import admin
from .models import Case


class TaskCase(admin.ModelAdmin):
    list_display=["name","case_detail","ip_address","category","status","assign_name","date_created"]


# Register your models here.
admin.site.register(Case) #นำข้อมูล Class ใน Model มาแสดงที่หน้า Admin