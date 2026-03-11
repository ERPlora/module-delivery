"""
AI context for the Delivery module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Delivery

### Models

**DeliverySettings** (singleton per hub)
- `default_prep_time` (int minutes, default 20), `auto_assign_zone` (bool, default True)
- Use `DeliverySettings.get_settings(hub_id)` to retrieve or create.

**DeliveryZone**
- `name` (str), `min_order` (decimal), `delivery_fee` (decimal), `estimated_time` (int minutes, default 30)
- `is_active` (bool), `zip_codes` (JSONField, list of strings), `max_radius_km` (decimal, optional)
- `sort_order` (int, for display ordering)

**Driver**
- `name` (str), `phone` (str), `is_active` (bool), `vehicle_type` (str), `is_external` (bool), `notes`

**DeliveryOrder**
- `number` (str, unique) — generated via `DeliveryOrder.generate_number(hub_id)` → format `DEL-0001`
- `order_type`: takeaway | delivery (default: delivery)
- `customer_name`, `customer_phone` (required), `delivery_address` (text, blank for takeaway)
- `delivery_zone` (FK → DeliveryZone, nullable), `driver` (FK → Driver, nullable)
- `status` choices: pending | preparing | ready | in_transit | delivered | picked_up | cancelled
- `promised_at` (datetime, optional), `completed_at` (datetime, optional)
- `subtotal`, `delivery_fee`, `total` (decimals) — call `calculate_totals()` after adding items
- `payment_method` (str), `paid` (bool, default False)

**DeliveryOrderItem**
- `order` (FK → DeliveryOrder, CASCADE, related_name='items')
- `product_name` (str), `quantity` (int), `unit_price` (decimal), `notes`
- `line_total` property = quantity × unit_price

### Key Flows

1. **Setup**: configure DeliverySettings (prep time), create DeliveryZones with fees and ZIP codes, add Drivers.
2. **New delivery order**: generate number, set order_type, fill customer info and delivery_address, assign zone.
3. **Add items**: create DeliveryOrderItem records linked to the order.
4. **Calculate totals**: call `order.calculate_totals()` then save.
5. **Assign driver & progress**: assign driver FK, advance status (pending → preparing → ready → in_transit → delivered).
6. **Takeaway flow**: order_type='takeaway', no delivery_address needed, status goes pending → preparing → ready → picked_up.

### Relationships

- DeliveryOrderItem → DeliveryOrder (CASCADE).
- DeliveryOrder → DeliveryZone (SET_NULL), DeliveryOrder → Driver (SET_NULL).
"""
