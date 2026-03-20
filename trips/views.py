from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from .models import Trip
from network.models import Node
from network.utils import find_path
from .forms import CreateTripForm


def driver_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_driver():
            messages.error(request, 'Only drivers can access this.')
            return redirect('/requests/dashboard/')
        return view_func(request, *args, **kwargs)
    return wrapper


@driver_required
def driver_dashboard(request):
    trips = Trip.objects.filter(driver=request.user).order_by('-created_at')
    active = [t for t in trips if t.status == 'active']
    pending = [t for t in trips if t.status == 'pending']
    past = [t for t in trips if t.status in ('completed', 'cancelled')]
    return render(request, 'trips/dashboard.html', {
        'active_trips': active,
        'pending_trips': pending,
        'past_trips': past,
    })


@driver_required
def create_trip(request):
    if request.method == 'POST':
        form = CreateTripForm(request.POST)
        if form.is_valid():
            start_node = form.cleaned_data['start_node']
            end_node = form.cleaned_data['end_node']
            max_passengers = form.cleaned_data['max_passengers']
            path = find_path(start_node, end_node)
            if not path:
                messages.error(request, f'No route found between {start_node} and {end_node}.')
                return render(request, 'trips/create_trip.html', {'form': form})
            Trip.objects.create(
                driver=request.user,
                start_node=start_node,
                end_node=end_node,
                route_nodes=[n.id for n in path],
                max_passengers=max_passengers,
                status='pending',
            )
            route_str = ' -> '.join(n.name for n in path)
            messages.success(request, f'Trip created! Route: {route_str}')
            return redirect('driver-dashboard')
    else:
        form = CreateTripForm()
    return render(request, 'trips/create_trip.html', {'form': form})


@driver_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    all_nodes = []
    if trip.route_nodes:
        nodes_map = {n.id: n for n in Node.objects.filter(id__in=trip.route_nodes)}
        all_nodes = [(i, nodes_map.get(nid), i < trip.current_node_index) for i, nid in enumerate(trip.route_nodes)]
    accepted_offers = trip.carpools.filter(status='accepted').select_related(
        'carpool_request__passenger', 'carpool_request__pickup_node', 'carpool_request__dropoff_node'
    )
    offered_offers = trip.carpools.filter(status='offered').select_related(
        'carpool_request__passenger', 'carpool_request__pickup_node', 'carpool_request__dropoff_node'
    )
    return render(request, 'trips/trip_detail.html', {
        'trip': trip,
        'all_nodes': all_nodes,
        'accepted_offers': accepted_offers,
        'offered_offers': offered_offers,
        'passenger_count': accepted_offers.count(),
    })


@driver_required
def cancel_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    if trip.status == 'pending':
        trip.status = 'cancelled'
        trip.save()
        messages.success(request, 'Trip cancelled.')
    else:
        messages.error(request, 'Only pending trips can be cancelled.')
    return redirect('driver-dashboard')


@driver_required
def start_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    if trip.status == 'pending':
        trip.status = 'active'
        trip.save()
        messages.success(request, 'Trip started!')
    else:
        messages.error(request, 'Cannot start this trip.')
    return redirect('trip-detail', trip_id=trip_id)


class UpdateNodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id, driver=request.user, status='active')
        except Trip.DoesNotExist:
            return Response({'error': 'Trip not found'}, status=404)
        next_index = trip.current_node_index + 1
        if next_index < len(trip.route_nodes):
            trip.current_node_index = next_index
            trip.save()
            try:
                node_name = Node.objects.get(id=trip.route_nodes[next_index]).name
            except Node.DoesNotExist:
                node_name = str(trip.route_nodes[next_index])
            return Response({
                'status': 'updated',
                'current_node': node_name,
                'current_index': next_index,
                'remaining_hops': len(trip.route_nodes) - next_index - 1,
            })
        else:
            trip.status = 'completed'
            trip.save()
            return Response({'status': 'trip completed'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carpool_requests_api(request, trip_id):
    from requests_app.models import CarpoolRequest
    from network.utils import get_nodes_within_hops
    try:
        trip = Trip.objects.get(id=trip_id, driver=request.user, status__in=['pending', 'active'])
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=404)
    remaining_ids = trip.get_remaining_node_ids()
    nearby_ids = get_nodes_within_hops(remaining_ids, max_hops=2)
    requests_qs = CarpoolRequest.objects.filter(
        status='pending',
        pickup_node_id__in=nearby_ids,
        dropoff_node_id__in=nearby_ids,
    ).select_related('passenger', 'pickup_node', 'dropoff_node')
    data = [{'id': cr.id, 'passenger': cr.passenger.username, 'pickup': cr.pickup_node.name, 'dropoff': cr.dropoff_node.name} for cr in requests_qs]
    return Response({'requests': data})
