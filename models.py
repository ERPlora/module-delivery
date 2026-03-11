"""
Delivery Module Models

Delivery zones, drivers, delivery/takeaway orders and line items.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


class DeliverySettings(HubBaseModel):
    """Per-hub delivery settings."""
    default_prep_time = models.PositiveIntegerField(
        default=20,
        verbose_name=_('Default prep time'),
        help_text=_('Minutes'),
    )
    auto_assign_zone = models.BooleanField(
        default=True,
        verbose_name=_('Auto assign zone'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'delivery_settings'
        verbose_name = _('Delivery Settings')
        verbose_name_plural = _('Delivery Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return f'DeliverySettings (hub={self.hub_id})'

    @classmethod
    def get_settings(cls, hub_id=None):
        """Get or create settings for the given hub."""
        obj, _ = cls.objects.get_or_create(hub_id=hub_id)
        return obj


class DeliveryZone(HubBaseModel):
    """Geographic delivery zone with pricing."""
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    min_order = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name=_('Minimum order'),
    )
    delivery_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name=_('Delivery fee'),
    )
    estimated_time = models.PositiveIntegerField(
        verbose_name=_('Estimated time'),
        help_text=_('Minutes'),
        default=30,
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    zip_codes = models.JSONField(default=list, blank=True, verbose_name=_('ZIP codes'))
    max_radius_km = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name=_('Max radius (km)'),
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Sort order'))

    class Meta(HubBaseModel.Meta):
        db_table = 'delivery_zone'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Driver(HubBaseModel):
    """Delivery driver."""
    name = models.CharField(max_length=150, verbose_name=_('Name'))
    phone = models.CharField(max_length=30, verbose_name=_('Phone'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    vehicle_type = models.CharField(
        max_length=30, blank=True,
        verbose_name=_('Vehicle type'),
    )
    is_external = models.BooleanField(
        default=False,
        verbose_name=_('External driver'),
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta(HubBaseModel.Meta):
        db_table = 'delivery_driver'
        ordering = ['name']

    def __str__(self):
        return self.name


class DeliveryOrder(HubBaseModel):
    """Takeaway or delivery order."""
    ORDER_TYPE_CHOICES = [
        ('takeaway', _('Takeaway')),
        ('delivery', _('Delivery')),
    ]
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('preparing', _('Preparing')),
        ('ready', _('Ready')),
        ('in_transit', _('In Transit')),
        ('delivered', _('Delivered')),
        ('picked_up', _('Picked Up')),
        ('cancelled', _('Cancelled')),
    ]

    number = models.CharField(max_length=20, unique=True, verbose_name=_('Number'))
    order_type = models.CharField(
        max_length=20, choices=ORDER_TYPE_CHOICES, default='delivery',
        verbose_name=_('Order type'),
    )
    customer_name = models.CharField(max_length=150, verbose_name=_('Customer name'))
    customer_phone = models.CharField(max_length=30, verbose_name=_('Customer phone'))
    delivery_address = models.TextField(blank=True, verbose_name=_('Delivery address'))
    delivery_zone = models.ForeignKey(
        DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Delivery zone'),
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Driver'),
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name=_('Status'),
    )
    ordered_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Ordered at'))
    promised_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Promised at'),
    )
    completed_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Completed at'),
    )
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name=_('Subtotal'),
    )
    delivery_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name=_('Delivery fee'),
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name=_('Total'),
    )
    payment_method = models.CharField(
        max_length=30, blank=True,
        verbose_name=_('Payment method'),
    )
    paid = models.BooleanField(default=False, verbose_name=_('Paid'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta(HubBaseModel.Meta):
        db_table = 'delivery_order'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.number} - {self.customer_name}'

    @classmethod
    def generate_number(cls, hub_id=None):
        """Generate next order number for this hub."""
        qs = cls.all_objects.filter(hub_id=hub_id) if hub_id else cls.all_objects.all()
        last = qs.order_by('-number').first()
        if last and last.number.startswith('DEL-'):
            try:
                num = int(last.number.split('-')[1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f'DEL-{num:04d}'

    def calculate_totals(self):
        """Recalculate subtotal and total from items."""
        from django.db.models import Sum, F
        agg = self.items.filter(is_deleted=False).aggregate(
            subtotal=Sum(F('unit_price') * F('quantity'))
        )
        self.subtotal = agg['subtotal'] or 0
        self.total = self.subtotal + self.delivery_fee

    @property
    def item_count(self):
        return self.items.filter(is_deleted=False).count()


class DeliveryOrderItem(HubBaseModel):
    """Line item in a delivery order."""
    order = models.ForeignKey(
        DeliveryOrder, on_delete=models.CASCADE, related_name='items',
        verbose_name=_('Order'),
    )
    product_name = models.CharField(max_length=200, verbose_name=_('Product name'))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Quantity'))
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name=_('Unit price'),
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta(HubBaseModel.Meta):
        db_table = 'delivery_order_item'

    def __str__(self):
        return f'{self.quantity}x {self.product_name}'

    @property
    def line_total(self):
        return self.quantity * self.unit_price
