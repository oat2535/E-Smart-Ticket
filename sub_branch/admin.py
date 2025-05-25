from django.contrib import admin
from sub_branch.models import SubBranch

@admin.register(SubBranch)
class SubBranchAdmin(admin.ModelAdmin):
    list_display = ('sub_branch_id', 'sub_branch_name', 'get_branch_name')
    search_fields = ('sub_branch_name', 'branch_id__branch_id')  # ใช้ __ เพื่อเข้าถึง field ของ ForeignKey
    list_filter = ('branch_id',)

    @admin.display(description='Branch ID')
    def get_branch_name(self, obj):
        return obj.branch_id.branch_id if obj.branch_id else "-"
