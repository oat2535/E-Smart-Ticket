from django.contrib import admin
from .models import SubCategory

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')  # แสดงคอลัมน์ในหน้า list view
    search_fields = ('name', 'category__name')  # ให้สามารถค้นหาจากชื่อ subcategory หรือชื่อ category ได้
    list_filter = ('category',)  # Filter ด้านข้างตาม category
