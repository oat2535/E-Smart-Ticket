from django import forms
from .models import AssetTransfer, MaintenanceRecord, AssetWriteOff, AssetDisposal, DisposalImage, AssetInventory
from sub_branch.models import SubBranch

class AssetInventoryForm(forms.ModelForm):
    class Meta:
        model = AssetInventory
        fields = ['asset_status', 'location_scanned', 'note']
        widgets = {
            'asset_status': forms.Select(attrs={'class': 'form-control'}),
            'location_scanned': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ระบุสถานที่ที่ตรวจพบทรัพย์สินนี้...'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'เพิ่มหมายเหตุ เช่น สภาพมีรอยถลอก หรือใช้งานไม่ได้'}),
        }

class BaseAssetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class AssetTransferForm(BaseAssetForm):
    class Meta:
        model = AssetTransfer
        fields = ['from_branch', 'to_branch', 'reason']

    def __init__(self, *args, asset_branch_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['to_branch'].queryset = SubBranch.objects.none()
        self.fields['to_branch'].required = False
        
        self.fields['from_branch'].queryset = SubBranch.objects.none()
        self.fields['from_branch'].required = False

        if asset_branch_id:
            try:
                # Find the SubBranch of the asset to get its company (branch_id)
                asset_sub_branch = SubBranch.objects.get(sub_branch_id=asset_branch_id)
                company_id = asset_sub_branch.branch_id_id
                
                if company_id:
                    self.fields['to_branch'].queryset = SubBranch.objects.filter(branch_id_id=company_id).order_by('sub_branch_name')
                    self.fields['from_branch'].queryset = SubBranch.objects.filter(branch_id_id=company_id).order_by('sub_branch_name')
            except SubBranch.DoesNotExist:
                pass
        
        # When form is submitted
        if 'to_branch' in self.data or 'from_branch' in self.data:
            try:
                # Optional: We could just let the queryset be all if we just want validation to pass
                # but since we restrict to the company, we should set the queryset so the chosen value is valid
                if asset_branch_id:
                    asset_sub_branch = SubBranch.objects.get(sub_branch_id=asset_branch_id)
                    company_id = asset_sub_branch.branch_id_id
                    if company_id:
                        self.fields['to_branch'].queryset = SubBranch.objects.filter(branch_id_id=company_id).order_by('sub_branch_name')
                        self.fields['from_branch'].queryset = SubBranch.objects.filter(branch_id_id=company_id).order_by('sub_branch_name')
            except (ValueError, TypeError, SubBranch.DoesNotExist):
                pass

class MaintenanceRecordForm(BaseAssetForm):
    class Meta:
        model = MaintenanceRecord
        fields = ['sub_asset', 'issue_description']

class AssetWriteOffForm(BaseAssetForm):
    class Meta:
        model = AssetWriteOff
        fields = ['reason']

class AssetDisposalForm(BaseAssetForm):
    class Meta:
        model = AssetDisposal
        fields = ['reason']

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-control-file'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result

class DisposalImageForm(forms.Form):
    images = MultipleFileField(
        required=False, 
        label="รูปภาพ (ไม่เกิน 5MB ต่อรูป)",
        widget=MultipleFileInput(attrs={'class': 'form-control-file', 'accept': '.pdf, image/*'})
    )

    def clean_images(self):
        images = self.cleaned_data.get('images', [])
        for image in images:
            # Check file type first
            content_type = getattr(image, 'content_type', '')
            file_name = getattr(image, 'name', '').lower()
            
            is_pdf = content_type == 'application/pdf' or file_name.endswith('.pdf')
            is_image = content_type.startswith('image/') or file_name.endswith(('.jpg', '.jpeg', '.png', '.gif'))
            
            if not is_image and not is_pdf:
                raise forms.ValidationError(f"ระบบรองรับเฉพาะไฟล์รูปภาพและไฟล์ PDF เท่านั้น (ไฟล์ {image.name} ไม่ถูกต้อง)")

            # Then check size
            if getattr(image, 'size', 0) > 5 * 1024 * 1024:
                raise forms.ValidationError(f"ขนาดไฟล์ {image.name} เกิน 5MB")
                
        return images
