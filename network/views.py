from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Node, Edge


@staff_member_required
def graph_view(request):
    nodes = Node.objects.all().order_by('name')
    edges = Edge.objects.select_related('from_node', 'to_node').all()
    return render(request, 'network/graph.html', {'nodes': nodes, 'edges': edges})


@staff_member_required
def active_trips_view(request):
    from trips.models import Trip
    active_trips = Trip.objects.filter(status='active').select_related('driver', 'start_node', 'end_node').order_by('-created_at')
    trip_data = []
    for trip in active_trips:
        try:
            current_node = Node.objects.get(id=trip.route_nodes[trip.current_node_index])
            current_node_name = current_node.name
        except Exception:
            current_node_name = 'Unknown'
        trip_data.append({
            'trip': trip,
            'current_node_name': current_node_name,
            'confirmed_passengers': trip.carpools.filter(status='accepted').count(),
            'remaining_hops': len(trip.route_nodes) - trip.current_node_index - 1,
        })
    return render(request, 'network/active_trips.html', {'trip_data': trip_data, 'total': len(trip_data)})
