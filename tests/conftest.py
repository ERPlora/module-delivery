"""
Pytest fixtures for Delivery module tests.
"""

import pytest
from decimal import Decimal
from django.conf import settings

# Disable debug toolbar during tests
if 'debug_toolbar' in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS = [
        app for app in settings.INSTALLED_APPS if app != 'debug_toolbar'
    ]
if hasattr(settings, 'MIDDLEWARE'):
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE
        if 'debug_toolbar' not in m
    ]

from django.contrib.auth.hashers import make_password
from apps.accounts.models import LocalUser
from apps.configuration.models import StoreConfig

from delivery.models import (
    DeliverySettings,
    DeliveryZone,
    Driver,
    DeliveryOrder,
    DeliveryOrderItem,
)


@pytest.fixture
def local_user(db):
    """Create a test user."""
    return LocalUser.objects.create(
        name='Test User',
        email='test@example.com',
        role='admin',
        pin_hash=make_password('1234'),
        is_active=True,
    )


@pytest.fixture
def user(local_user):
    """Alias for local_user fixture."""
    return local_user


@pytest.fixture
def store_config(db):
    """Create store config for tests."""
    config = StoreConfig.get_config()
    config.is_configured = True
    config.name = 'Test Store'
    config.save()
    return config


@pytest.fixture
def auth_client(client, local_user, store_config):
    """Return an authenticated client."""
    session = client.session
    session['local_user_id'] = str(local_user.id)
    session['user_name'] = local_user.name
    session['user_email'] = local_user.email
    session['user_role'] = local_user.role
    session['store_config_checked'] = True
    session.save()
    return client


@pytest.fixture
def delivery_settings(db):
    """Create delivery settings."""
    return DeliverySettings.get_settings()


@pytest.fixture
def zone_centro(db):
    """Create a Centro delivery zone."""
    return DeliveryZone.objects.create(
        name='Centro',
        delivery_fee=Decimal('2.50'),
        min_order=Decimal('10.00'),
        estimated_time=20,
        zip_codes=['28001', '28002', '28003'],
        max_radius_km=Decimal('3.00'),
        sort_order=1,
    )


@pytest.fixture
def zone_periferia(db):
    """Create a Periferia delivery zone."""
    return DeliveryZone.objects.create(
        name='Periferia',
        delivery_fee=Decimal('4.00'),
        min_order=Decimal('15.00'),
        estimated_time=40,
        zip_codes=['28010', '28011'],
        max_radius_km=Decimal('8.00'),
        sort_order=2,
    )


@pytest.fixture
def driver_carlos(db):
    """Create a driver."""
    return Driver.objects.create(
        name='Carlos',
        phone='+34600111222',
        vehicle_type='Motorcycle',
    )


@pytest.fixture
def driver_maria(db):
    """Create a second driver."""
    return Driver.objects.create(
        name='Maria',
        phone='+34600333444',
        vehicle_type='Bicycle',
        is_external=True,
    )


@pytest.fixture
def delivery_order(db, zone_centro, driver_carlos):
    """Create a basic delivery order."""
    return DeliveryOrder.objects.create(
        number=DeliveryOrder.generate_number(),
        order_type='delivery',
        customer_name='Juan Garcia',
        customer_phone='+34600555666',
        delivery_address='Calle Mayor 10, Madrid',
        delivery_zone=zone_centro,
        driver=driver_carlos,
        delivery_fee=Decimal('2.50'),
    )


@pytest.fixture
def takeaway_order(db):
    """Create a takeaway order."""
    return DeliveryOrder.objects.create(
        number=DeliveryOrder.generate_number(),
        order_type='takeaway',
        customer_name='Ana Lopez',
        customer_phone='+34600777888',
    )


@pytest.fixture
def order_with_items(db, delivery_order):
    """Create a delivery order with items."""
    DeliveryOrderItem.objects.create(
        order=delivery_order,
        product_name='Pizza Margherita',
        quantity=2,
        unit_price=Decimal('9.50'),
    )
    DeliveryOrderItem.objects.create(
        order=delivery_order,
        product_name='Coca-Cola',
        quantity=2,
        unit_price=Decimal('2.00'),
    )
    delivery_order.calculate_totals()
    delivery_order.save(update_fields=['subtotal', 'total'])
    return delivery_order
