from django.contrib import admin
from .models import AssetCategory, AssetLocation, MasterAsset, SubAsset, AssetTransfer, MaintenanceRecord, AssetWriteOff, AssetDisposal, DisposalImage, AssetInventory

admin.site.register(AssetCategory)
admin.site.register(AssetLocation)
admin.site.register(SubAsset)
admin.site.register(AssetTransfer)
admin.site.register(MaintenanceRecord)
admin.site.register(AssetWriteOff)
admin.site.register(AssetDisposal)
admin.site.register(DisposalImage)
admin.site.register(AssetInventory)

@admin.register(MasterAsset)
class MasterAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_code', 'name', 'status', 'responsible_person')
    search_fields = ('asset_code', 'name')
