from django.db import models
from django.conf import settings
from network.models import Node
from trips.models import Trip


class CarpoolRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carpool_requests')
    pickup_node = models.ForeignKey(Node, related_name='pickups', on_delete=models.CASCADE)
    dropoff_node = models.ForeignKey(Node, related_name='dropoffs', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmed_offer = models.OneToOneField('DriverOffer', null=True, blank=True, on_delete=models.SET_NULL, related_name='confirmed_for')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.passenger.username}: {self.pickup_node} to {self.dropoff_node} [{self.status}]"


class DriverOffer(models.Model):
    STATUS_CHOICES = [
        ('offered', 'Offered'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    carpool_request = models.ForeignKey(CarpoolRequest, on_delete=models.CASCADE, related_name='offers')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='carpools')
    detour_hops = models.IntegerField(default=0)
    fare = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offered')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer by {self.trip.driver.username} - ${self.fare}"
