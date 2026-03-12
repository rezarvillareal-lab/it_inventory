from django import forms
from django.forms import inlineformset_factory
from .models import Inventory, EquipmentComponent


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        
        fields = [
            'control_number',
            'office_or_hospital',
            'user_name',
            'computer_name',
            'assigned_ip',
            'received_by',
            'position',
            'date_received',
            'created_at',
            'created_by',
            'status',
        ]
    
        widgets = {
            'date_received': forms.DateInput(attrs={'type': 'date'}),
            'created_at': forms.DateInput(attrs={'type': 'date'}),
        }



ComponentFormSet = inlineformset_factory(
    Inventory,
    EquipmentComponent,
    fields=[
        'original_model',
        'original_serial',
        'replacement_model',
        'replacement_serial',
        'remarks'
    ],
    extra=0,
    can_delete=False
)
