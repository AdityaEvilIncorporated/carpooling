from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal


class User(AbstractUser):
    ROLE_CHOICES = [('driver', 'Driver'), ('passenger', 'Passenger')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='passenger')

    def __str__(self):
        return f"{self.username} ({self.role})"

    def is_driver(self):
        return self.role == 'driver'

    def is_passenger(self):
        return self.role == 'passenger'

    def get_wallet(self):
        wallet, created = Wallet.objects.get_or_create(user=self)
        if not created:
            wallet.refresh_from_db()
        return wallet


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.user.username} - ${self.balance}"

    def can_afford(self, amount):
        return self.balance >= Decimal(str(amount))

    def deduct(self, amount):
        from django.db.models import F
        amount = Decimal(str(amount))
        updated = Wallet.objects.filter(id=self.id, balance__gte=amount).update(
            balance=F('balance') - amount
        )
        if not updated:
            self.refresh_from_db()
            raise ValueError(f"Not enough balance. Have ${self.balance}, need ${amount}")
        self.refresh_from_db()

    def credit(self, amount):
        from django.db.models import F
        amount = Decimal(str(amount))
        Wallet.objects.filter(id=self.id).update(balance=F('balance') + amount)
        self.refresh_from_db()


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('topup', 'Top Up'),
        ('fare_deduction', 'Fare Deduction'),
        ('driver_earning', 'Driver Earning'),
        ('refund', 'Refund'),
    ]
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    trip = models.ForeignKey('trips.Trip', null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} ${self.amount} - {self.wallet.user.username}"

    class Meta:
        ordering = ['-created_at']
