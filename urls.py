"""Delivery Module URL Configuration"""

from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),

    # Orders
    path('orders/', views.orders, name='orders'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<uuid:order_id>/edit/', views.order_edit, name='order_edit'),
    path('orders/<uuid:order_id>/delete/', views.order_delete, name='order_delete'),
    path('orders/<uuid:order_id>/status/', views.order_update_status, name='order_update_status'),
    path('orders/<uuid:order_id>/assign-driver/', views.order_assign_driver, name='order_assign_driver'),

    # Order items
    path('orders/<uuid:order_id>/items/add/', views.order_add_item, name='order_add_item'),
    path('orders/<uuid:order_id>/items/<uuid:item_id>/remove/', views.order_remove_item, name='order_remove_item'),

    # Zones
    path('zones/', views.zones, name='zones'),
    path('zones/create/', views.zone_create, name='zone_create'),
    path('zones/<uuid:zone_id>/edit/', views.zone_edit, name='zone_edit'),
    path('zones/<uuid:zone_id>/delete/', views.zone_delete, name='zone_delete'),

    # Drivers
    path('drivers/', views.drivers, name='drivers'),
    path('drivers/create/', views.driver_create, name='driver_create'),
    path('drivers/<uuid:driver_id>/edit/', views.driver_edit, name='driver_edit'),
    path('drivers/<uuid:driver_id>/delete/', views.driver_delete, name='driver_delete'),

    # Settings
    path('settings/', views.settings, name='settings'),
    path('settings/toggle/', views.settings_toggle, name='settings_toggle'),
    path('settings/input/', views.settings_input, name='settings_input'),
]
