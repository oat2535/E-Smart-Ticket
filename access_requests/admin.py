from django.contrib import admin
from .models import AccessRequest, System, Position, AccessRequestLog

# Register your models here.
@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'request_code', 'user', 'employee_id', 'email', 
        'prefix', 'prefix_other', 'prefix_th', 'prefix_en', 
        'firstname_th', 'lastname_th', 'firstname_en', 'lastname_en', 
        'department', 'position', 'status', 'created_at', 'updated_at', 
        'manager_approver', 'manager_approval_date', 'it_approver', 'it_approval_date', 
        'reject_reason', 'rejected_by', 'rejected_at'
    )
@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
admin.site.register(AccessRequestLog)
