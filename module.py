"""
Delivery Module Configuration

Delivery and takeaway order management for restaurants, bars and food businesses.
"""
from django.utils.translation import gettext_lazy as _

MODULE_ID = "delivery"
MODULE_NAME = _("Delivery")
MODULE_ICON = 'material:delivery_dining'
MODULE_VERSION = '1.0.2'
MODULE_DESCRIPTION = _('Delivery order management, zones, and driver tracking')
MODULE_AUTHOR = 'ERPlora'
MODULE_CATEGORY = "pos"

MODULE_INDUSTRIES = ["restaurant", "bar", "pizzeria", "fast_food", "kebab_shop", "sushi_restaurant", "bakery", "food_truck"]

MENU = {
    "label": _("Delivery"),
    "icon": "bicycle-outline",
    "order": 46,
    "show": True,
}

NAVIGATION = [
    {"id": "dashboard", "label": _("Overview"), "icon": "grid-outline", "view": ""},
    {"id": "orders", "label": _("Orders"), "icon": "bicycle-outline", "view": "orders"},
    {"id": "zones", "label": _("Zones"), "icon": "map-outline", "view": "zones"},
    {"id": "drivers", "label": _("Drivers"), "icon": "person-outline", "view": "drivers"},
    {"id": "settings", "label": _("Settings"), "icon": "settings-outline", "view": "settings"},
]

DEPENDENCIES = ['commands', 'cash_register', 'customers']

SETTINGS = {
    "default_prep_time": 20,
    "auto_assign_zone": True,
}

PERMISSIONS = [
    ("view_delivery_order", _("Can view delivery orders")),
    ("add_delivery_order", _("Can add delivery orders")),
    ("change_delivery_order", _("Can change delivery orders")),
    ("delete_delivery_order", _("Can delete delivery orders")),
    ("manage_zones", _("Can manage delivery zones")),
    ("manage_drivers", _("Can manage drivers")),
    ("view_settings", _("Can view settings")),
    ("change_settings", _("Can change settings")),
]

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "manager": [
        "view_delivery_order", "add_delivery_order", "change_delivery_order",
        "delete_delivery_order", "manage_zones", "manage_drivers", "view_settings",
    ],
    "employee": ["view_delivery_order", "add_delivery_order", "change_delivery_order"],
}
