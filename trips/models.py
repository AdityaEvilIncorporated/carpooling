from django.db import models
from django.conf import settings
from network.models import Node


class Trip(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips')
    start_node = models.ForeignKey(Node, related_name='trip_starts', on_delete=models.CASCADE)
    end_node = models.ForeignKey(Node, related_name='trip_ends', on_delete=models.CASCADE)
    route_nodes = models.JSONField(default=list)
    current_node_index = models.IntegerField(default=0)
    max_passengers = models.IntegerField(default=3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.driver.username}: {self.start_node} to {self.end_node} [{self.status}]"

    def get_remaining_node_ids(self):
        return self.route_nodes[self.current_node_index:]

    def get_remaining_nodes(self):
        remaining_ids = self.get_remaining_node_ids()
        if not remaining_ids:
            return []
        nodes = Node.objects.filter(id__in=remaining_ids)
        node_map = {n.id: n for n in nodes}
        return [node_map[nid] for nid in remaining_ids if nid in node_map]

    def is_full(self):
        return self.carpools.filter(status='accepted').count() >= self.max_passengers
