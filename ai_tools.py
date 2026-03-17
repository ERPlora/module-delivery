"""AI tools for the Delivery module."""
from assistant.tools import AssistantTool, register_tool


# ==============================================================================
# DELIVERY ZONES
# ==============================================================================

@register_tool
class ListDeliveryZones(AssistantTool):
    name = "list_delivery_zones"
    description = "List all delivery zones with their name, fee, minimum order, estimated time, and active status."
    module_id = "delivery"
    required_permission = "delivery.view_deliveryzone"
    parameters = {
        "type": "object",
        "properties": {
            "active_only": {
                "type": "boolean",
                "description": "If true, return only active zones. Default is false (all zones).",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryZone
        qs = DeliveryZone.objects.all()
        if args.get("active_only"):
            qs = qs.filter(is_active=True)
        return {
            "zones": [
                {
                    "id": str(z.id),
                    "name": z.name,
                    "is_active": z.is_active,
                    "min_order": str(z.min_order),
                    "delivery_fee": str(z.delivery_fee),
                    "estimated_time": z.estimated_time,
                    "zip_codes": z.zip_codes,
                    "max_radius_km": str(z.max_radius_km) if z.max_radius_km is not None else None,
                    "sort_order": z.sort_order,
                }
                for z in qs
            ],
            "total": qs.count(),
        }


@register_tool
class GetDeliveryZone(AssistantTool):
    name = "get_delivery_zone"
    description = "Get full details of a specific delivery zone by ID."
    module_id = "delivery"
    required_permission = "delivery.view_deliveryzone"
    parameters = {
        "type": "object",
        "properties": {
            "zone_id": {
                "type": "string",
                "description": "UUID of the delivery zone.",
            },
        },
        "required": ["zone_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryZone
        try:
            z = DeliveryZone.objects.get(id=args["zone_id"])
        except DeliveryZone.DoesNotExist:
            return {"error": "Delivery zone not found"}
        return {
            "id": str(z.id),
            "name": z.name,
            "is_active": z.is_active,
            "min_order": str(z.min_order),
            "delivery_fee": str(z.delivery_fee),
            "estimated_time": z.estimated_time,
            "zip_codes": z.zip_codes,
            "max_radius_km": str(z.max_radius_km) if z.max_radius_km is not None else None,
            "sort_order": z.sort_order,
        }


@register_tool
class CreateDeliveryZone(AssistantTool):
    name = "create_delivery_zone"
    description = "Create a new delivery zone with pricing and coverage settings."
    module_id = "delivery"
    required_permission = "delivery.change_deliveryzone"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the zone (e.g. 'City Centre', 'Zone A').",
            },
            "min_order": {
                "type": "number",
                "description": "Minimum order amount required for this zone. Default 0.",
            },
            "delivery_fee": {
                "type": "number",
                "description": "Delivery fee charged for this zone. Default 0.",
            },
            "estimated_time": {
                "type": "integer",
                "description": "Estimated delivery time in minutes. Default 30.",
            },
            "is_active": {
                "type": "boolean",
                "description": "Whether the zone is active. Default true.",
            },
            "zip_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ZIP codes covered by this zone.",
            },
            "max_radius_km": {
                "type": "number",
                "description": "Maximum delivery radius in kilometres (optional).",
            },
            "sort_order": {
                "type": "integer",
                "description": "Display sort order. Default 0.",
            },
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryZone
        z = DeliveryZone.objects.create(
            name=args["name"],
            min_order=args.get("min_order", 0),
            delivery_fee=args.get("delivery_fee", 0),
            estimated_time=args.get("estimated_time", 30),
            is_active=args.get("is_active", True),
            zip_codes=args.get("zip_codes", []),
            max_radius_km=args.get("max_radius_km"),
            sort_order=args.get("sort_order", 0),
        )
        return {"id": str(z.id), "name": z.name, "created": True}


@register_tool
class UpdateDeliveryZone(AssistantTool):
    name = "update_delivery_zone"
    description = "Update one or more fields of an existing delivery zone; omitted fields are unchanged."
    module_id = "delivery"
    required_permission = "delivery.change_deliveryzone"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "zone_id": {
                "type": "string",
                "description": "UUID of the delivery zone to update.",
            },
            "name": {"type": "string"},
            "min_order": {"type": "number"},
            "delivery_fee": {"type": "number"},
            "estimated_time": {"type": "integer", "description": "Minutes."},
            "is_active": {"type": "boolean"},
            "zip_codes": {
                "type": "array",
                "items": {"type": "string"},
            },
            "max_radius_km": {"type": "number"},
            "sort_order": {"type": "integer"},
        },
        "required": ["zone_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryZone
        try:
            z = DeliveryZone.objects.get(id=args["zone_id"])
        except DeliveryZone.DoesNotExist:
            return {"error": "Delivery zone not found"}
        for field in ["name", "min_order", "delivery_fee", "estimated_time", "is_active", "zip_codes", "max_radius_km", "sort_order"]:
            if field in args:
                setattr(z, field, args[field])
        z.save()
        return {"id": str(z.id), "name": z.name, "updated": True}


@register_tool
class DeleteDeliveryZone(AssistantTool):
    name = "delete_delivery_zone"
    description = "Delete a delivery zone by ID."
    module_id = "delivery"
    required_permission = "delivery.delete_deliveryzone"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "zone_id": {"type": "string", "description": "UUID of the zone to delete."},
        },
        "required": ["zone_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryZone
        try:
            z = DeliveryZone.objects.get(id=args["zone_id"])
        except DeliveryZone.DoesNotExist:
            return {"error": "Delivery zone not found"}
        name = z.name
        z.delete()
        return {"deleted": True, "name": name}


# ==============================================================================
# DRIVERS
# ==============================================================================

@register_tool
class ListDrivers(AssistantTool):
    name = "list_drivers"
    description = "List all delivery drivers with name, phone, vehicle type, and active status."
    module_id = "delivery"
    required_permission = "delivery.view_driver"
    parameters = {
        "type": "object",
        "properties": {
            "active_only": {
                "type": "boolean",
                "description": "If true, return only active drivers. Default false.",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import Driver
        qs = Driver.objects.all()
        if args.get("active_only"):
            qs = qs.filter(is_active=True)
        return {
            "drivers": [
                {
                    "id": str(d.id),
                    "name": d.name,
                    "phone": d.phone,
                    "vehicle_type": d.vehicle_type,
                    "is_active": d.is_active,
                    "is_external": d.is_external,
                    "notes": d.notes,
                }
                for d in qs
            ],
            "total": qs.count(),
        }


@register_tool
class GetDriver(AssistantTool):
    name = "get_driver"
    description = "Get full details of a specific driver by ID."
    module_id = "delivery"
    required_permission = "delivery.view_driver"
    parameters = {
        "type": "object",
        "properties": {
            "driver_id": {"type": "string", "description": "UUID of the driver."},
        },
        "required": ["driver_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import Driver
        try:
            d = Driver.objects.get(id=args["driver_id"])
        except Driver.DoesNotExist:
            return {"error": "Driver not found"}
        return {
            "id": str(d.id),
            "name": d.name,
            "phone": d.phone,
            "vehicle_type": d.vehicle_type,
            "is_active": d.is_active,
            "is_external": d.is_external,
            "notes": d.notes,
        }


@register_tool
class CreateDriver(AssistantTool):
    name = "create_driver"
    description = "Register a new delivery driver."
    module_id = "delivery"
    required_permission = "delivery.change_driver"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Full name of the driver."},
            "phone": {"type": "string", "description": "Contact phone number."},
            "vehicle_type": {
                "type": "string",
                "description": "Vehicle type (e.g. 'bicycle', 'motorbike', 'car'). Optional.",
            },
            "is_active": {"type": "boolean", "description": "Active status. Default true."},
            "is_external": {
                "type": "boolean",
                "description": "True if this is an external/contractor driver. Default false.",
            },
            "notes": {"type": "string", "description": "Internal notes about the driver."},
        },
        "required": ["name", "phone"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import Driver
        d = Driver.objects.create(
            name=args["name"],
            phone=args["phone"],
            vehicle_type=args.get("vehicle_type", ""),
            is_active=args.get("is_active", True),
            is_external=args.get("is_external", False),
            notes=args.get("notes", ""),
        )
        return {"id": str(d.id), "name": d.name, "created": True}


@register_tool
class UpdateDriver(AssistantTool):
    name = "update_driver"
    description = "Update one or more fields of an existing driver; omitted fields are unchanged."
    module_id = "delivery"
    required_permission = "delivery.change_driver"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "driver_id": {"type": "string", "description": "UUID of the driver to update."},
            "name": {"type": "string"},
            "phone": {"type": "string"},
            "vehicle_type": {"type": "string"},
            "is_active": {"type": "boolean"},
            "is_external": {"type": "boolean"},
            "notes": {"type": "string"},
        },
        "required": ["driver_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import Driver
        try:
            d = Driver.objects.get(id=args["driver_id"])
        except Driver.DoesNotExist:
            return {"error": "Driver not found"}
        for field in ["name", "phone", "vehicle_type", "is_active", "is_external", "notes"]:
            if field in args:
                setattr(d, field, args[field])
        d.save()
        return {"id": str(d.id), "name": d.name, "updated": True}


@register_tool
class DeleteDriver(AssistantTool):
    name = "delete_driver"
    description = "Delete a driver by ID."
    module_id = "delivery"
    required_permission = "delivery.delete_driver"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "driver_id": {"type": "string", "description": "UUID of the driver to delete."},
        },
        "required": ["driver_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import Driver
        try:
            d = Driver.objects.get(id=args["driver_id"])
        except Driver.DoesNotExist:
            return {"error": "Driver not found"}
        name = d.name
        d.delete()
        return {"deleted": True, "name": name}


# ==============================================================================
# DELIVERY ORDERS
# ==============================================================================

@register_tool
class ListDeliveryOrders(AssistantTool):
    name = "list_delivery_orders"
    description = "List delivery/takeaway orders, optionally filtered by status or order type."
    module_id = "delivery"
    required_permission = "delivery.view_deliveryorder"
    parameters = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status: 'pending', 'preparing', 'ready', 'in_transit', 'delivered', 'picked_up', 'cancelled'.",
            },
            "order_type": {
                "type": "string",
                "description": "Filter by type: 'delivery' or 'takeaway'.",
            },
            "search": {
                "type": "string",
                "description": "Search by customer name, phone, or order number.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return. Default 20.",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryOrder
        from django.db.models import Q
        qs = DeliveryOrder.objects.all()
        if args.get("status"):
            qs = qs.filter(status=args["status"])
        if args.get("order_type"):
            qs = qs.filter(order_type=args["order_type"])
        if args.get("search"):
            s = args["search"]
            qs = qs.filter(
                Q(customer_name__icontains=s) |
                Q(customer_phone__icontains=s) |
                Q(number__icontains=s)
            )
        limit = args.get("limit", 20)
        return {
            "orders": [
                {
                    "id": str(o.id),
                    "number": o.number,
                    "order_type": o.order_type,
                    "customer_name": o.customer_name,
                    "customer_phone": o.customer_phone,
                    "status": o.status,
                    "total": str(o.total),
                    "paid": o.paid,
                    "ordered_at": str(o.ordered_at),
                }
                for o in qs[:limit]
            ],
            "total": qs.count(),
        }


@register_tool
class GetDeliveryOrder(AssistantTool):
    name = "get_delivery_order"
    description = "Get full details of a delivery order including all line items."
    module_id = "delivery"
    required_permission = "delivery.view_deliveryorder"
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "UUID of the delivery order."},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryOrder
        try:
            o = DeliveryOrder.objects.get(id=args["order_id"])
        except DeliveryOrder.DoesNotExist:
            return {"error": "Order not found"}
        return {
            "id": str(o.id),
            "number": o.number,
            "order_type": o.order_type,
            "customer_name": o.customer_name,
            "customer_phone": o.customer_phone,
            "delivery_address": o.delivery_address,
            "delivery_zone": str(o.delivery_zone_id) if o.delivery_zone_id else None,
            "driver": str(o.driver_id) if o.driver_id else None,
            "status": o.status,
            "ordered_at": str(o.ordered_at),
            "promised_at": str(o.promised_at) if o.promised_at else None,
            "completed_at": str(o.completed_at) if o.completed_at else None,
            "subtotal": str(o.subtotal),
            "delivery_fee": str(o.delivery_fee),
            "total": str(o.total),
            "payment_method": o.payment_method,
            "paid": o.paid,
            "notes": o.notes,
            "items": [
                {
                    "id": str(item.id),
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "line_total": str(item.line_total),
                    "notes": item.notes,
                }
                for item in o.items.filter(is_deleted=False)
            ],
        }


@register_tool
class CreateDeliveryOrder(AssistantTool):
    name = "create_delivery_order"
    description = "Create a new delivery or takeaway order with optional line items."
    module_id = "delivery"
    required_permission = "delivery.change_deliveryorder"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "order_type": {
                "type": "string",
                "description": "Order type: 'delivery' (default) or 'takeaway'.",
            },
            "customer_name": {"type": "string", "description": "Customer full name."},
            "customer_phone": {"type": "string", "description": "Customer phone number."},
            "delivery_address": {
                "type": "string",
                "description": "Delivery address (required for delivery orders).",
            },
            "delivery_zone_id": {
                "type": "string",
                "description": "UUID of the delivery zone (optional).",
            },
            "driver_id": {
                "type": "string",
                "description": "UUID of the assigned driver (optional).",
            },
            "delivery_fee": {
                "type": "number",
                "description": "Delivery fee amount. Default 0.",
            },
            "payment_method": {
                "type": "string",
                "description": "Payment method (e.g. 'cash', 'card'). Optional.",
            },
            "notes": {"type": "string", "description": "Internal notes."},
            "items": {
                "type": "array",
                "description": "Line items to add to the order.",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "unit_price": {"type": "number"},
                        "notes": {"type": "string"},
                    },
                    "required": ["product_name", "quantity", "unit_price"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["customer_name", "customer_phone"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryOrder, DeliveryOrderItem
        number = DeliveryOrder.generate_number(hub_id=request.hub_id)
        order = DeliveryOrder(
            number=number,
            order_type=args.get("order_type", "delivery"),
            customer_name=args["customer_name"],
            customer_phone=args["customer_phone"],
            delivery_address=args.get("delivery_address", ""),
            delivery_fee=args.get("delivery_fee", 0),
            payment_method=args.get("payment_method", ""),
            notes=args.get("notes", ""),
        )
        if args.get("delivery_zone_id"):
            order.delivery_zone_id = args["delivery_zone_id"]
        if args.get("driver_id"):
            order.driver_id = args["driver_id"]
        order.save()
        for item_data in args.get("items", []):
            DeliveryOrderItem.objects.create(
                order=order,
                product_name=item_data["product_name"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                notes=item_data.get("notes", ""),
            )
        order.calculate_totals()
        order.save(update_fields=["subtotal", "total", "updated_at"])
        return {"id": str(order.id), "number": order.number, "created": True}


@register_tool
class UpdateDeliveryOrder(AssistantTool):
    name = "update_delivery_order"
    description = "Update fields or status of an existing delivery order; omitted fields are unchanged."
    module_id = "delivery"
    required_permission = "delivery.change_deliveryorder"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "UUID of the order to update."},
            "status": {
                "type": "string",
                "description": "New status: 'pending', 'preparing', 'ready', 'in_transit', 'delivered', 'picked_up', 'cancelled'.",
            },
            "driver_id": {"type": "string", "description": "UUID of the assigned driver."},
            "delivery_zone_id": {"type": "string"},
            "delivery_address": {"type": "string"},
            "delivery_fee": {"type": "number"},
            "payment_method": {"type": "string"},
            "paid": {"type": "boolean"},
            "notes": {"type": "string"},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryOrder
        from django.utils import timezone
        try:
            o = DeliveryOrder.objects.get(id=args["order_id"])
        except DeliveryOrder.DoesNotExist:
            return {"error": "Order not found"}
        for field in ["status", "delivery_address", "delivery_fee", "payment_method", "paid", "notes"]:
            if field in args:
                setattr(o, field, args[field])
        if "driver_id" in args:
            o.driver_id = args["driver_id"] or None
        if "delivery_zone_id" in args:
            o.delivery_zone_id = args["delivery_zone_id"] or None
        if args.get("status") in ("delivered", "picked_up") and not o.completed_at:
            o.completed_at = timezone.now()
        o.calculate_totals()
        o.save()
        return {"id": str(o.id), "number": o.number, "status": o.status, "updated": True}


@register_tool
class DeleteDeliveryOrder(AssistantTool):
    name = "delete_delivery_order"
    description = "Delete a delivery order by ID."
    module_id = "delivery"
    required_permission = "delivery.delete_deliveryorder"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "UUID of the order to delete."},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from delivery.models import DeliveryOrder
        try:
            o = DeliveryOrder.objects.get(id=args["order_id"])
        except DeliveryOrder.DoesNotExist:
            return {"error": "Order not found"}
        number = o.number
        o.delete()
        return {"deleted": True, "number": number}
