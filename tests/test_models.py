"""
Delivery Module Model Tests
"""

import pytest
from decimal import Decimal

from delivery.models import (
    DeliverySettings,
    DeliveryZone,
    Driver,
    DeliveryOrder,
    DeliveryOrderItem,
)


@pytest.mark.django_db
class TestDeliverySettings:
    def test_get_settings_creates_default(self):
        settings = DeliverySettings.get_settings()
        assert settings.pk is not None
        assert settings.default_prep_time == 20
        assert settings.auto_assign_zone is True

    def test_get_settings_returns_existing(self):
        s1 = DeliverySettings.get_settings()
        s2 = DeliverySettings.get_settings()
        assert s1.pk == s2.pk

    def test_str(self):
        settings = DeliverySettings.get_settings()
        assert 'DeliverySettings' in str(settings)


@pytest.mark.django_db
class TestDeliveryZone:
    def test_create_zone(self, zone_centro):
        assert zone_centro.name == 'Centro'
        assert zone_centro.delivery_fee == Decimal('2.50')
        assert zone_centro.is_active is True
        assert len(zone_centro.zip_codes) == 3

    def test_str(self, zone_centro):
        assert str(zone_centro) == 'Centro'

    def test_ordering(self, zone_centro, zone_periferia):
        zones = list(DeliveryZone.objects.all())
        assert zones[0].name == 'Centro'
        assert zones[1].name == 'Periferia'


@pytest.mark.django_db
class TestDriver:
    def test_create_driver(self, driver_carlos):
        assert driver_carlos.name == 'Carlos'
        assert driver_carlos.phone == '+34600111222'
        assert driver_carlos.is_active is True
        assert driver_carlos.is_external is False

    def test_external_driver(self, driver_maria):
        assert driver_maria.is_external is True

    def test_str(self, driver_carlos):
        assert str(driver_carlos) == 'Carlos'


@pytest.mark.django_db
class TestDeliveryOrder:
    def test_create_delivery_order(self, delivery_order):
        assert delivery_order.number.startswith('DEL-')
        assert delivery_order.order_type == 'delivery'
        assert delivery_order.status == 'pending'
        assert delivery_order.customer_name == 'Juan Garcia'

    def test_create_takeaway_order(self, takeaway_order):
        assert takeaway_order.order_type == 'takeaway'
        assert takeaway_order.delivery_address == ''
        assert takeaway_order.driver is None

    def test_generate_number_sequential(self):
        n1 = DeliveryOrder.generate_number()
        DeliveryOrder.objects.create(
            number=n1,
            customer_name='Test',
            customer_phone='123',
        )
        n2 = DeliveryOrder.generate_number()
        num1 = int(n1.split('-')[1])
        num2 = int(n2.split('-')[1])
        assert num2 == num1 + 1

    def test_str(self, delivery_order):
        assert 'DEL-' in str(delivery_order)
        assert 'Juan Garcia' in str(delivery_order)

    def test_calculate_totals(self, order_with_items):
        # 2 * 9.50 + 2 * 2.00 = 23.00 subtotal
        assert order_with_items.subtotal == Decimal('23.00')
        # 23.00 + 2.50 delivery fee = 25.50
        assert order_with_items.total == Decimal('25.50')

    def test_item_count(self, order_with_items):
        assert order_with_items.item_count == 2


@pytest.mark.django_db
class TestDeliveryOrderItem:
    def test_create_item(self, delivery_order):
        item = DeliveryOrderItem.objects.create(
            order=delivery_order,
            product_name='Burger',
            quantity=1,
            unit_price=Decimal('8.00'),
        )
        assert item.product_name == 'Burger'
        assert item.line_total == Decimal('8.00')

    def test_line_total_with_quantity(self, delivery_order):
        item = DeliveryOrderItem.objects.create(
            order=delivery_order,
            product_name='Fries',
            quantity=3,
            unit_price=Decimal('3.50'),
        )
        assert item.line_total == Decimal('10.50')

    def test_str(self, delivery_order):
        item = DeliveryOrderItem.objects.create(
            order=delivery_order,
            product_name='Pizza',
            quantity=2,
            unit_price=Decimal('10.00'),
        )
        assert str(item) == '2x Pizza'
