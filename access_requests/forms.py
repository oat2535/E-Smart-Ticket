from django import forms
from .models import AccessRequest, System

class AccessRequestForm(forms.ModelForm):
    systems = forms.ModelMultipleChoiceField(
        queryset=System.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'custom-control-input'}),
        required=True,
        label="Select Systems"
    )

    # Explicitly define prefix to remove the empty "---------" choice
    prefix = forms.ChoiceField(
        choices=AccessRequest.PREFIX_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'custom-control-input'}),
        label="คำนำหน้าชื่อ"
    )

    class Meta:
        model = AccessRequest
        fields = [
            'employee_id', 'email', 'prefix', 'prefix_other',
            'firstname_th', 'lastname_th', 'firstname_en', 'lastname_en', 'department', 'position',
            'systems', 'reason'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            # prefix widget is defined in the field above
            'prefix_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ระบุอื่นๆ'}),
            'firstname_th': forms.TextInput(attrs={'class': 'form-control'}),
            'lastname_th': forms.TextInput(attrs={'class': 'form-control'}),
            'firstname_en': forms.TextInput(attrs={'class': 'form-control'}),
            'lastname_en': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
