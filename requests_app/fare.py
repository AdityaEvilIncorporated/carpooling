from django.conf import settings


def calculate_fare(passengers_per_hop, unit_price=None, base_fee=None):
    if unit_price is None:
        unit_price = getattr(settings, 'FARE_UNIT_PRICE', 5.0)
    if base_fee is None:
        base_fee = getattr(settings, 'FARE_BASE_FEE', 2.0)
    if not passengers_per_hop:
        return round(base_fee, 2)
    fare = sum(unit_price / n for n in passengers_per_hop) + base_fee
    return round(fare, 2)


def build_passengers_per_hop(remaining_route, pickup_node_id, dropoff_node_id, existing_passengers=0):
    route_ids = [n.id for n in remaining_route]
    try:
        pickup_idx = route_ids.index(pickup_node_id)
        dropoff_idx = route_ids.index(dropoff_node_id)
    except ValueError:
        return None
    if pickup_idx >= dropoff_idx:
        return None
    return [existing_passengers + 1] * (dropoff_idx - pickup_idx)


def calculate_detour(remaining_route_ids, pickup_node_id, dropoff_node_id):
    try:
        pickup_idx = remaining_route_ids.index(pickup_node_id)
        dropoff_idx = remaining_route_ids.index(dropoff_node_id)
    except ValueError:
        return None
    if pickup_idx >= dropoff_idx:
        return None
    return 0
