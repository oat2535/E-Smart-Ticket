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
        fields = ['name', 'category', 'total_quantity', 'available_quantity', 'image', 'description', 'serial_number', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        new_avail = cleaned_data.get('available_quantity', 0)
        new_total = cleaned_data.get('total_quantity', 0)
        
        if self.instance and self.instance.pk:
            if 'available_quantity' in self.changed_data and 'total_quantity' not in self.changed_data:
                category = cleaned_data.get('category')
                is_consumable = category and category.name in ['Consumable Parts', 'Consumble Parts']
                if not is_consumable:
                    from django.db.models import Sum
                    borrowed = self.instance.requisition_set.filter(
                        status__in=['PENDING', 'APPROVED']
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                    
                    cleaned_data['total_quantity'] = new_avail + borrowed
                    self.instance.total_quantity = cleaned_data['total_quantity']
        else:
            # If it's a new instance, and user fills available but not total
            if 'available_quantity' in self.changed_data and 'total_quantity' not in self.changed_data:
                cleaned_data['total_quantity'] = new_avail
                
        return cleaned_data

from .models import Category
class RequisitionFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'text', 'class': 'form-control datepicker', 'placeholder': 'Select Date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'text', 'class': 'form-control datepicker', 'placeholder': 'Select Date'}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}), empty_label="All Categories")
