"""
Delivery Module Forms
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import DeliveryZone, Driver, DeliveryOrder, DeliveryOrderItem, DeliverySettings


class DeliveryZoneForm(forms.ModelForm):
    class Meta:
        model = DeliveryZone
        fields = [
            'name', 'min_order', 'delivery_fee', 'estimated_time',
            'zip_codes', 'max_radius_km', 'sort_order', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Zone name'),
            }),
            'min_order': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'delivery_fee': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'estimated_time': forms.NumberInput(attrs={
                'class': 'input', 'min': '1',
            }),
            'zip_codes': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Comma-separated ZIP codes'),
            }),
            'max_radius_km': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'input', 'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }

    def clean_zip_codes(self):
        """Accept comma-separated string and convert to list."""
        value = self.cleaned_data.get('zip_codes')
        if isinstance(value, str):
            return [z.strip() for z in value.split(',') if z.strip()]
        if isinstance(value, list):
            return value
        return []


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'phone', 'vehicle_type', 'is_external', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Driver name'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Phone number'),
            }),
            'vehicle_type': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('e.g. Motorcycle, Car, Bicycle'),
            }),
            'is_external': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'notes': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 3,
                'placeholder': _('Additional notes'),
            }),
        }


class DeliveryOrderForm(forms.ModelForm):
    class Meta:
        model = DeliveryOrder
        fields = [
            'order_type', 'customer_name', 'customer_phone',
            'delivery_address', 'delivery_zone', 'driver',
            'promised_at', 'payment_method', 'notes',
        ]
        widgets = {
            'order_type': forms.Select(attrs={'class': 'select'}),
            'customer_name': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Customer name'),
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Phone number'),
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
                'placeholder': _('Delivery address'),
            }),
            'delivery_zone': forms.Select(attrs={'class': 'select'}),
            'driver': forms.Select(attrs={'class': 'select'}),
            'promised_at': forms.DateTimeInput(attrs={
                'class': 'input', 'type': 'datetime-local',
            }),
            'payment_method': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('e.g. Cash, Card'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
                'placeholder': _('Order notes'),
            }),
        }

    def __init__(self, *args, hub_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hub_id:
            self.fields['delivery_zone'].queryset = DeliveryZone.objects.filter(
                hub_id=hub_id, is_active=True, is_deleted=False,
            )
            self.fields['driver'].queryset = Driver.objects.filter(
                hub_id=hub_id, is_active=True, is_deleted=False,
            )
        self.fields['delivery_zone'].required = False
        self.fields['driver'].required = False
        self.fields['promised_at'].required = False


class DeliveryOrderItemForm(forms.ModelForm):
    class Meta:
        model = DeliveryOrderItem
        fields = ['product_name', 'quantity', 'unit_price', 'notes']
        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': 'input', 'placeholder': _('Product name'),
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'input', 'min': '1', 'value': '1',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
                'placeholder': _('Special instructions'),
            }),
        }


class DeliverySettingsForm(forms.ModelForm):
    class Meta:
        model = DeliverySettings
        fields = ['default_prep_time', 'auto_assign_zone']
        widgets = {
            'default_prep_time': forms.NumberInput(attrs={
                'class': 'input', 'min': '1',
            }),
            'auto_assign_zone': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }
