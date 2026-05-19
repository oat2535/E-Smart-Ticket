from django import forms
from .models import Requisition, Equipment

class RequisitionForm(forms.ModelForm):
    borrower_name = forms.CharField(
        label="ชื่อผู้ยืม",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อผู้ยืม'}),
    )

    class Meta:
        model = Requisition
        fields = ['quantity', 'borrower_name', 'reason', 'return_date']
        widgets = {
            'return_date': forms.DateInput(attrs={'type': 'text', 'class': 'form-control datepicker', 'placeholder': 'Select Date'}),
        }

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'category', 'total_quantity', 'image', 'description', 'serial_number', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

from .models import Category
class RequisitionFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'text', 'class': 'form-control datepicker', 'placeholder': 'Select Date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'text', 'class': 'form-control datepicker', 'placeholder': 'Select Date'}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}), empty_label="All Categories")
