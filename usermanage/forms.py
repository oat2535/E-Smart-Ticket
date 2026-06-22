from django import forms
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from members.models import Members

class UserStaffStatusForm(forms.ModelForm):
    is_staff = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Staff Status'
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Active Status'
    )

    class Meta:
        model = Members
        fields = ['is_staff', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # แปลงค่า is_staff และ is_active จาก 0 หรือ 1 เป็น True หรือ False ในฟอร์ม
        if 'is_staff' in self.initial:
            self.initial['is_staff'] = bool(self.initial['is_staff'])
        if 'is_active' in self.initial:
            self.initial['is_active'] = bool(self.initial['is_active'])

    def save(self, commit=True):
        instance = super().save(commit=False)
        # แปลงค่า is_staff และ is_active จาก True/False เป็น 1 หรือ 0 ก่อนบันทึก
        instance.is_staff = 1 if instance.is_staff else 0
        instance.is_active = 1 if instance.is_active else 0
        if commit:
            instance.save()
        return instance