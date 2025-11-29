from django.contrib import admin
from .models import SecondSubCategory

@admin.register(SecondSubCategory)
class SecondSubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sub_category')  # แสดงคอลัมน์ในหน้า list view
    search_fields = ('name', 'sub_category__name')  # ให้สามารถค้นหาจากชื่อ subcategory หรือชื่อ category ได้
    list_filter = ('sub_category',)  # Filter ด้านข้างตาม category
