"""
Delivery Module Views

Delivery and takeaway order management, zones, drivers and settings.
"""

from decimal import Decimal

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Sum, Count

from apps.core.htmx import htmx_view
from apps.accounts.decorators import login_required, permission_required
from apps.modules_runtime.navigation import with_module_nav

from .models import DeliverySettings, DeliveryZone, Driver, DeliveryOrder, DeliveryOrderItem
from .forms import (
    DeliveryZoneForm, DriverForm, DeliveryOrderForm,
    DeliveryOrderItemForm, DeliverySettingsForm,
)


def _hub_id(request):
    return request.session.get('hub_id')


# =============================================================================
# Dashboard
# =============================================================================

@login_required
@with_module_nav('delivery', 'dashboard')
@htmx_view('delivery/pages/index.html', 'delivery/partials/dashboard.html')
def index(request):
    hub = _hub_id(request)
    today = timezone.now().date()

    orders_today = DeliveryOrder.objects.filter(
        hub_id=hub, is_deleted=False, created_at__date=today,
    )

    status_counts = orders_today.values('status').annotate(count=Count('id'))
    counts = {item['status']: item['count'] for item in status_counts}

    # Kanban columns
    pending_orders = DeliveryOrder.objects.filter(
        hub_id=hub, is_deleted=False, status='pending',
    ).order_by('-created_at')[:20]
    preparing_orders = DeliveryOrder.objects.filter(
        hub_id=hub, is_deleted=False, status='preparing',
    ).order_by('-created_at')[:20]
    ready_orders = DeliveryOrder.objects.filter(
        hub_id=hub, is_deleted=False, status='ready',
    ).order_by('-created_at')[:20]
    in_transit_orders = DeliveryOrder.objects.filter(
        hub_id=hub, is_deleted=False, status='in_transit',
    ).order_by('-created_at')[:20]

    total_revenue = orders_today.filter(
        status__in=['delivered', 'picked_up'],
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')

    return {
        'pending_count': counts.get('pending', 0),
        'preparing_count': counts.get('preparing', 0),
        'ready_count': counts.get('ready', 0),
        'in_transit_count': counts.get('in_transit', 0),
        'delivered_count': counts.get('delivered', 0) + counts.get('picked_up', 0),
        'cancelled_count': counts.get('cancelled', 0),
        'total_today': orders_today.count(),
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'in_transit_orders': in_transit_orders,
    }


# =============================================================================
# Orders
# =============================================================================

@login_required
@with_module_nav('delivery', 'orders')
@htmx_view('delivery/pages/orders.html', 'delivery/partials/orders.html')
def orders(request):
    hub = _hub_id(request)
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('order_type', '')
    search = request.GET.get('q', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    qs = DeliveryOrder.objects.filter(
        hub_id=hub, is_deleted=False,
    ).select_related('delivery_zone', 'driver').order_by('-created_at')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if type_filter:
        qs = qs.filter(order_type=type_filter)
    if search:
        qs = qs.filter(
            Q(number__icontains=search)
            | Q(customer_name__icontains=search)
            | Q(customer_phone__icontains=search)
        )
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    return {
        'orders': qs[:100],
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': DeliveryOrder.STATUS_CHOICES,
        'type_choices': DeliveryOrder.ORDER_TYPE_CHOICES,
    }


@login_required
@with_module_nav('delivery', 'orders')
@htmx_view('delivery/pages/order_detail.html', 'delivery/partials/order_detail.html')
def order_detail(request, order_id):
    hub = _hub_id(request)
    order = get_object_or_404(DeliveryOrder, pk=order_id, hub_id=hub, is_deleted=False)
    items = order.items.filter(is_deleted=False)
    drivers = Driver.objects.filter(hub_id=hub, is_active=True, is_deleted=False)

    return {
        'order': order,
        'items': items,
        'drivers': drivers,
        'status_choices': DeliveryOrder.STATUS_CHOICES,
    }


@login_required
@with_module_nav('delivery', 'orders')
@htmx_view('delivery/pages/order_form.html', 'delivery/partials/order_form.html')
def order_create(request):
    hub = _hub_id(request)

    if request.method == 'POST':
        form = DeliveryOrderForm(request.POST, hub_id=hub)
        if form.is_valid():
            order = form.save(commit=False)
            order.hub_id = hub
            order.number = DeliveryOrder.generate_number(hub)
            # Auto-set delivery fee from zone
            if order.delivery_zone and order.order_type == 'delivery':
                order.delivery_fee = order.delivery_zone.delivery_fee
            order.save()
            return {
                'order': order,
                'items': order.items.filter(is_deleted=False),
                'drivers': Driver.objects.filter(hub_id=hub, is_active=True, is_deleted=False),
                'status_choices': DeliveryOrder.STATUS_CHOICES,
                'template': 'delivery/partials/order_detail.html',
            }
    else:
        form = DeliveryOrderForm(hub_id=hub)

    return {'form': form, 'is_new': True}


@login_required
@with_module_nav('delivery', 'orders')
@htmx_view('delivery/pages/order_form.html', 'delivery/partials/order_form.html')
def order_edit(request, order_id):
    hub = _hub_id(request)
    order = get_object_or_404(DeliveryOrder, pk=order_id, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = DeliveryOrderForm(request.POST, instance=order, hub_id=hub)
        if form.is_valid():
            order = form.save(commit=False)
            if order.delivery_zone and order.order_type == 'delivery':
                order.delivery_fee = order.delivery_zone.delivery_fee
            order.calculate_totals()
            order.save()
            return {
                'order': order,
                'items': order.items.filter(is_deleted=False),
                'drivers': Driver.objects.filter(hub_id=hub, is_active=True, is_deleted=False),
                'status_choices': DeliveryOrder.STATUS_CHOICES,
                'template': 'delivery/partials/order_detail.html',
            }
    else:
        form = DeliveryOrderForm(instance=order, hub_id=hub)

    return {'form': form, 'order': order, 'is_new': False}


@login_required
@require_POST
def order_update_status(request, order_id):
    """Update delivery order status via HTMX POST."""
    hub = _hub_id(request)
    order = get_object_or_404(DeliveryOrder, pk=order_id, hub_id=hub, is_deleted=False)
    new_status = request.POST.get('status')

    if new_status and new_status in dict(DeliveryOrder.STATUS_CHOICES):
        order.status = new_status
        update_fields = ['status', 'updated_at']
        if new_status in ('delivered', 'picked_up'):
            order.completed_at = timezone.now()
            update_fields.append('completed_at')
        order.save(update_fields=update_fields)
        return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'success': False, 'message': str(_('Invalid status'))}, status=400)


@login_required
@require_POST
def order_assign_driver(request, order_id):
    """Assign a driver to a delivery order."""
    hub = _hub_id(request)
    order = get_object_or_404(DeliveryOrder, pk=order_id, hub_id=hub, is_deleted=False)
    driver_id = request.POST.get('driver_id')

    if driver_id:
        driver = get_object_or_404(Driver, pk=driver_id, hub_id=hub, is_deleted=False)
        order.driver = driver
    else:
        order.driver = None
    order.save(update_fields=['driver', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def order_delete(request, order_id):
    hub = _hub_id(request)
    order = get_object_or_404(DeliveryOrder, pk=order_id, hub_id=hub, is_deleted=False)
    order.is_deleted = True
    order.deleted_at = timezone.now()
    order.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True, 'message': str(_('Order deleted'))})


# =============================================================================
# Order Items
# =============================================================================

@login_required
@require_POST
def order_add_item(request, order_id):
    """Add an item to a delivery order."""
    hub = _hub_id(request)
    order = get_object_or_404(DeliveryOrder, pk=order_id, hub_id=hub, is_deleted=False)

    form = DeliveryOrderItemForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.hub_id = hub
        item.order = order
        item.save()
        order.calculate_totals()
        order.save(update_fields=['subtotal', 'total', 'updated_at'])
        return JsonResponse({
            'success': True,
            'item_id': str(item.pk),
            'subtotal': str(order.subtotal),
            'total': str(order.total),
        })

    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_POST
def order_remove_item(request, order_id, item_id):
    """Remove an item from a delivery order."""
    hub = _hub_id(request)
    order = get_object_or_404(DeliveryOrder, pk=order_id, hub_id=hub, is_deleted=False)
    item = get_object_or_404(DeliveryOrderItem, pk=item_id, order=order, is_deleted=False)

    item.is_deleted = True
    item.deleted_at = timezone.now()
    item.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    order.calculate_totals()
    order.save(update_fields=['subtotal', 'total', 'updated_at'])

    return JsonResponse({
        'success': True,
        'subtotal': str(order.subtotal),
        'total': str(order.total),
    })


# =============================================================================
# Zones
# =============================================================================

@login_required
@with_module_nav('delivery', 'zones')
@htmx_view('delivery/pages/zones.html', 'delivery/partials/zones.html')
def zones(request):
    hub = _hub_id(request)
    zone_list = DeliveryZone.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('sort_order', 'name')
    return {'zones': zone_list}


@login_required
@with_module_nav('delivery', 'zones')
@htmx_view('delivery/pages/zone_form.html', 'delivery/partials/zone_form.html')
def zone_create(request):
    hub = _hub_id(request)

    if request.method == 'POST':
        form = DeliveryZoneForm(request.POST)
        if form.is_valid():
            zone = form.save(commit=False)
            zone.hub_id = hub
            zone.save()
            return {
                'zones': DeliveryZone.objects.filter(hub_id=hub, is_deleted=False),
                'template': 'delivery/partials/zones.html',
            }
    else:
        form = DeliveryZoneForm()

    return {'form': form, 'is_new': True}


@login_required
@with_module_nav('delivery', 'zones')
@htmx_view('delivery/pages/zone_form.html', 'delivery/partials/zone_form.html')
def zone_edit(request, zone_id):
    hub = _hub_id(request)
    zone = get_object_or_404(DeliveryZone, pk=zone_id, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = DeliveryZoneForm(request.POST, instance=zone)
        if form.is_valid():
            form.save()
            return {
                'zones': DeliveryZone.objects.filter(hub_id=hub, is_deleted=False),
                'template': 'delivery/partials/zones.html',
            }
    else:
        # Display zip_codes as comma-separated string for the input
        initial_data = None
        if zone.zip_codes:
            initial_data = {'zip_codes': ', '.join(zone.zip_codes)}
        form = DeliveryZoneForm(instance=zone, initial=initial_data)

    return {'form': form, 'zone': zone, 'is_new': False}


@login_required
@require_POST
def zone_delete(request, zone_id):
    hub = _hub_id(request)
    zone = get_object_or_404(DeliveryZone, pk=zone_id, hub_id=hub, is_deleted=False)
    zone.is_deleted = True
    zone.deleted_at = timezone.now()
    zone.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True, 'message': str(_('Zone deleted'))})


# =============================================================================
# Drivers
# =============================================================================

@login_required
@with_module_nav('delivery', 'drivers')
@htmx_view('delivery/pages/drivers.html', 'delivery/partials/drivers.html')
def drivers(request):
    hub = _hub_id(request)
    driver_list = Driver.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('name')

    # Count active deliveries per driver
    active_statuses = ['preparing', 'ready', 'in_transit']
    for d in driver_list:
        d.active_deliveries = DeliveryOrder.objects.filter(
            hub_id=hub, driver=d, is_deleted=False,
            status__in=active_statuses,
        ).count()

    return {'drivers': driver_list}


@login_required
@with_module_nav('delivery', 'drivers')
@htmx_view('delivery/pages/driver_form.html', 'delivery/partials/driver_form.html')
def driver_create(request):
    hub = _hub_id(request)

    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            driver = form.save(commit=False)
            driver.hub_id = hub
            driver.save()
            return {
                'drivers': Driver.objects.filter(hub_id=hub, is_deleted=False),
                'template': 'delivery/partials/drivers.html',
            }
    else:
        form = DriverForm()

    return {'form': form, 'is_new': True}


@login_required
@with_module_nav('delivery', 'drivers')
@htmx_view('delivery/pages/driver_form.html', 'delivery/partials/driver_form.html')
def driver_edit(request, driver_id):
    hub = _hub_id(request)
    driver = get_object_or_404(Driver, pk=driver_id, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            return {
                'drivers': Driver.objects.filter(hub_id=hub, is_deleted=False),
                'template': 'delivery/partials/drivers.html',
            }
    else:
        form = DriverForm(instance=driver)

    return {'form': form, 'driver': driver, 'is_new': False}


@login_required
@require_POST
def driver_delete(request, driver_id):
    hub = _hub_id(request)
    driver = get_object_or_404(Driver, pk=driver_id, hub_id=hub, is_deleted=False)
    driver.is_deleted = True
    driver.deleted_at = timezone.now()
    driver.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True, 'message': str(_('Driver deleted'))})


# =============================================================================
# Settings
# =============================================================================

@login_required
@permission_required('delivery.change_settings')
@with_module_nav('delivery', 'settings')
@htmx_view('delivery/pages/settings.html', 'delivery/partials/settings.html')
def settings(request):
    hub = _hub_id(request)
    config = DeliverySettings.get_settings(hub)
    today = timezone.now().date()

    today_orders = DeliveryOrder.objects.filter(
        hub_id=hub, is_deleted=False, created_at__date=today,
    )
    zones_count = DeliveryZone.objects.filter(hub_id=hub, is_deleted=False).count()
    drivers_count = Driver.objects.filter(hub_id=hub, is_deleted=False).count()

    return {
        'config': config,
        'today_orders_count': today_orders.count(),
        'today_revenue': today_orders.filter(
            status__in=['delivered', 'picked_up'],
        ).aggregate(total=Sum('total'))['total'] or Decimal('0'),
        'zones_count': zones_count,
        'drivers_count': drivers_count,
    }


@login_required
@permission_required('delivery.change_settings')
@require_POST
def settings_toggle(request):
    hub = _hub_id(request)
    config = DeliverySettings.get_settings(hub)
    name = request.POST.get('name')
    value = request.POST.get('value') == 'true'

    if hasattr(config, name) and isinstance(getattr(config, name), bool):
        setattr(config, name, value)
        config.save()

    return HttpResponse(status=204)


@login_required
@permission_required('delivery.change_settings')
@require_POST
def settings_input(request):
    hub = _hub_id(request)
    config = DeliverySettings.get_settings(hub)
    name = request.POST.get('name')
    value = request.POST.get('value')

    if hasattr(config, name):
        setattr(config, name, int(value))
        config.save()

    return HttpResponse(status=204)
