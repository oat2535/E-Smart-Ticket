from django.contrib import admin
from .models import Category, Department

class TaskCategory(admin.ModelAdmin):
    list_display = ["name", "department_id"]


admin.site.register(Category, TaskCategory)