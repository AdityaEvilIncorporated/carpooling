from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from functools import wraps
from decimal import Decimal

from .models import CarpoolRequest, DriverOffer
from .forms import CarpoolRequestForm
from .utils import find_matching_trips
from .fare import build_passengers_per_hop, calculate_fare, calculate_detour


def passenger_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_passenger():
            messages.error(request, 'Only passengers can access this.')
            return redirect('/trips/dashboard/')
        return view_func(request, *args, **kwargs)
    return wrapper


def driver_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_driver():
            messages.error(request, 'Only drivers can access this.')
            return redirect('/requests/dashboard/')
        return view_func(request, *args, **kwargs)
    return wrapper


@passenger_required
def passenger_dashboard(request):
    all_requests = CarpoolRequest.objects.filter(
        passenger=request.user
    ).select_related('pickup_node', 'dropoff_node', 'confirmed_offer__trip__driver').order_by('-created_at')
    return render(request, 'requests_app/passenger_dashboard.html', {
        'pending_requests': [r for r in all_requests if r.status == 'pending'],
        'confirmed_requests': [r for r in all_requests if r.status == 'confirmed'],
        'past_requests': [r for r in all_requests if r.status in ('cancelled', 'completed')],
        'wallet': request.user.get_wallet(),
    })


@passenger_required
def submit_request(request):
    if request.method == 'POST':
        form = CarpoolRequestForm(request.POST)
        if form.is_valid():
            pickup = form.cleaned_data['pickup_node']
            dropoff = form.cleaned_data['dropoff_node']
            matching = find_matching_trips(pickup.id, dropoff.id)
            cr = CarpoolRequest.objects.create(
                passenger=request.user,
                pickup_node=pickup,
                dropoff_node=dropoff,
                status='pending',
            )
            if matching:
                messages.success(request, f'Request submitted! {len(matching)} driver(s) might offer you a ride.')
            else:
                messages.warning(request, 'Request submitted. No matching trips right now.')
            return redirect('view-offers', request_id=cr.id)
    else:
        form = CarpoolRequestForm()
    return render(request, 'requests_app/submit_request.html', {
        'form': form,
        'wallet': request.user.get_wallet(),
    })


@passenger_required
def view_offers(request, request_id):
    cr = get_object_or_404(CarpoolRequest, id=request_id, passenger=request.user)
    offered = list(cr.offers.filter(status='offered').select_related('trip__driver', 'trip__start_node', 'trip__end_node').order_by('-created_at'))
    accepted = cr.offers.filter(status='accepted').select_related('trip__driver', 'trip__start_node', 'trip__end_node').first()
    wallet = request.user.get_wallet()
    offers_with_afford = [{'offer': o, 'can_afford': wallet.can_afford(o.fare)} for o in offered]
    return render(request, 'requests_app/view_offers.html', {
        'carpool_request': cr,
        'offers_with_afford': offers_with_afford,
        'accepted_offer': accepted,
        'wallet': wallet,
    })


@passenger_required
def confirm_offer(request, offer_id):
    offer = get_object_or_404(DriverOffer, id=offer_id, carpool_request__passenger=request.user, status='offered')
    cr = offer.carpool_request
    wallet = request.user.get_wallet()
    if cr.status != 'pending':
        messages.error(request, 'This request is no longer pending.')
        return redirect('passenger-dashboard')
    if not wallet.can_afford(offer.fare):
        messages.error(request, f'Not enough balance. You have ${wallet.balance} but fare is ${offer.fare}.')
        return redirect('topup')
    with transaction.atomic():
        offer.status = 'accepted'
        offer.save()
        DriverOffer.objects.filter(carpool_request=cr).exclude(id=offer.id).update(status='rejected')
        cr.confirmed_offer = offer
        cr.status = 'confirmed'
        cr.save()
    messages.success(request, f'Confirmed! {offer.trip.driver.username} will pick you up. Fare: ${offer.fare}')
    return redirect('passenger-dashboard')


@passenger_required
def cancel_request(request, request_id):
    cr = get_object_or_404(CarpoolRequest, id=request_id, passenger=request.user)
    if cr.status not in ('pending', 'confirmed'):
        messages.error(request, 'Cannot cancel this request.')
        return redirect('passenger-dashboard')
    with transaction.atomic():
        cr.offers.filter(status='offered').update(status='rejected')
        cr.status = 'cancelled'
        cr.save()
    messages.success(request, 'Request cancelled.')
    return redirect('passenger-dashboard')


@passenger_required
def request_detail(request, request_id):
    cr = get_object_or_404(CarpoolRequest, id=request_id, passenger=request.user)
    all_offers = cr.offers.select_related('trip__driver', 'trip__start_node', 'trip__end_node').order_by('-created_at')
    return render(request, 'requests_app/request_detail.html', {
        'carpool_request': cr,
        'all_offers': all_offers,
        'wallet': request.user.get_wallet(),
    })


@driver_required
def driver_requests_view(request, trip_id):
    from trips.models import Trip
    from network.utils import get_nodes_within_hops
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    remaining_ids = trip.get_remaining_node_ids()
    remaining_nodes = trip.get_remaining_nodes()
    nearby_ids = get_nodes_within_hops(remaining_ids, max_hops=2)
    visible_requests = CarpoolRequest.objects.filter(
        status='pending',
        pickup_node_id__in=nearby_ids,
        dropoff_node_id__in=nearby_ids,
    ).select_related('passenger', 'pickup_node', 'dropoff_node').order_by('-created_at')
    request_data = []
    for cr in visible_requests:
        already_offered = DriverOffer.objects.filter(carpool_request=cr, trip=trip).exists()
        pph = build_passengers_per_hop(remaining_nodes, cr.pickup_node_id, cr.dropoff_node_id, existing_passengers=0)
        fare = calculate_fare(pph) if pph else None
        detour = calculate_detour(remaining_ids, cr.pickup_node_id, cr.dropoff_node_id)
        can_afford = True
        if fare:
            try:
                can_afford = cr.passenger.get_wallet().can_afford(fare)
            except Exception:
                can_afford = False
        request_data.append({
            'request': cr,
            'fare': fare,
            'detour': detour if detour is not None else 0,
            'already_offered': already_offered,
            'can_afford': can_afford,
        })
    return render(request, 'requests_app/driver_requests.html', {
        'trip': trip,
        'request_data': request_data,
        'my_offered': list(DriverOffer.objects.filter(trip=trip, status='offered').select_related('carpool_request__passenger', 'carpool_request__pickup_node', 'carpool_request__dropoff_node')),
        'my_accepted': list(DriverOffer.objects.filter(trip=trip, status='accepted').select_related('carpool_request__passenger', 'carpool_request__pickup_node', 'carpool_request__dropoff_node')),
        'my_rejected': list(DriverOffer.objects.filter(trip=trip, status='rejected').select_related('carpool_request__passenger')),
        'remaining_nodes': remaining_nodes,
        'driver_wallet': request.user.get_wallet(),
    })


@driver_required
def make_offer(request, request_id, trip_id):
    from trips.models import Trip
    cr = get_object_or_404(CarpoolRequest, id=request_id, status='pending')
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    if DriverOffer.objects.filter(carpool_request=cr, trip=trip).exists():
        messages.warning(request, 'You already made an offer for this.')
        return redirect('driver-requests', trip_id=trip_id)
    remaining_nodes = trip.get_remaining_nodes()
    remaining_ids = trip.get_remaining_node_ids()
    pph = build_passengers_per_hop(remaining_nodes, cr.pickup_node_id, cr.dropoff_node_id, existing_passengers=0)
    if not pph:
        messages.error(request, 'Passenger nodes are not on your remaining route.')
        return redirect('driver-requests', trip_id=trip_id)
    fare = calculate_fare(pph)
    detour = calculate_detour(remaining_ids, cr.pickup_node_id, cr.dropoff_node_id)
    DriverOffer.objects.create(
        carpool_request=cr,
        trip=trip,
        detour_hops=detour if detour is not None else 0,
        fare=fare,
        status='offered',
    )
    messages.success(request, f'Offer sent to {cr.passenger.username}! Fare: ${fare}')
    return redirect('driver-requests', trip_id=trip_id)


@driver_required
def withdraw_offer(request, offer_id):
    offer = get_object_or_404(DriverOffer, id=offer_id, trip__driver=request.user, status='offered')
    trip_id = offer.trip.id
    offer.delete()
    messages.success(request, 'Offer withdrawn.')
    return redirect('driver-requests', trip_id=trip_id)


@driver_required
def complete_trip_view(request, trip_id):
    from trips.models import Trip
    from accounts.models import Wallet, Transaction
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user, status='active')
    confirmed_offers = list(DriverOffer.objects.filter(trip=trip, status='accepted').select_related('carpool_request__passenger'))
    if not confirmed_offers:
        with transaction.atomic():
            trip.status = 'completed'
            trip.current_node_index = len(trip.route_nodes) - 1
            trip.save()
        messages.success(request, 'Trip completed with no passengers.')
        return redirect('driver-dashboard')
    problems = []
    for offer in confirmed_offers:
        p = offer.carpool_request.passenger
        w = p.get_wallet()
        if not w.can_afford(offer.fare):
            problems.append(f"{p.username} needs ${offer.fare} but only has ${w.balance}")
    if problems:
        messages.error(request, 'Cannot complete - insufficient balance: ' + ' | '.join(problems))
        return redirect('trip-detail', trip_id=trip_id)
    total_earned = Decimal('0.00')
    with transaction.atomic():
        driver_wallet = Wallet.objects.select_for_update().get(user=request.user)
        for offer in confirmed_offers:
            passenger = offer.carpool_request.passenger
            fare = Decimal(str(offer.fare))
            p_wallet = Wallet.objects.select_for_update().get(user=passenger)
            p_wallet.deduct(fare)
            Transaction.objects.create(
                wallet=p_wallet,
                amount=fare,
                transaction_type='fare_deduction',
                description=f'Fare for trip {trip.id}: {trip.start_node} to {trip.end_node}',
                trip=trip,
            )
            driver_wallet.credit(fare)
            Transaction.objects.create(
                wallet=driver_wallet,
                amount=fare,
                transaction_type='driver_earning',
                description=f'Earned from {passenger.username} trip {trip.id}',
                trip=trip,
            )
            total_earned += fare
            offer.carpool_request.status = 'completed'
            offer.carpool_request.save()
        trip.status = 'completed'
        trip.current_node_index = len(trip.route_nodes) - 1
        trip.save()
    driver_wallet.refresh_from_db()
    messages.success(request, f'Trip done! Earned ${total_earned}. Balance: ${driver_wallet.balance}')
    return redirect('driver-dashboard')
