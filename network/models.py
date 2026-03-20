from django.db import models


class Node(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class Edge(models.Model):
    from_node = models.ForeignKey(Node, related_name='outgoing', on_delete=models.CASCADE)
    to_node = models.ForeignKey(Node, related_name='incoming', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('from_node', 'to_node')

    def __str__(self):
        return f"{self.from_node} -> {self.to_node}"


class SiteSettings(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Site Settings'

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
