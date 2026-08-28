from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import Inventory, EquipmentComponent


class InventoryForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if not self.instance.pk and user is not None:
            full_name = user.get_full_name().strip() or user.username
            self.fields['created_by'].initial = full_name
            self.fields['created_at'].initial = timezone.now().date()

        self.fields['created_by'].disabled = True
        self.fields['created_at'].disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)

        if not instance.pk and self.user is not None:
            instance.created_by = self.user.get_full_name().strip() or self.user.username
            instance.created_at = timezone.now().date()

        if commit:
            instance.save()

        return instance

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
        'remarks'
    ],
    extra=0,
    can_delete=False
)
