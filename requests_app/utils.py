from network.models import Edge


def get_nodes_within_hops(node_ids, max_hops=2):
    reachable = set(node_ids)
    frontier = set(node_ids)
    for _ in range(max_hops):
        forward = set(Edge.objects.filter(from_node_id__in=frontier).values_list('to_node_id', flat=True))
        backward = set(Edge.objects.filter(to_node_id__in=frontier).values_list('from_node_id', flat=True))
        new_nodes = (forward | backward) - reachable
        reachable |= new_nodes
        frontier = new_nodes
    return reachable


def find_matching_trips(pickup_node_id, dropoff_node_id):
    from trips.models import Trip
    matching = []
    active_trips = Trip.objects.filter(status__in=['pending', 'active']).select_related('driver', 'start_node', 'end_node')
    for trip in active_trips:
        if trip.is_full():
            continue
        remaining_ids = trip.get_remaining_node_ids()
        if not remaining_ids:
            continue
        nearby = get_nodes_within_hops(remaining_ids, max_hops=2)
        if pickup_node_id in nearby and dropoff_node_id in nearby:
            matching.append(trip)
    return matching
