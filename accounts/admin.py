from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Wallet, Transaction


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (('Role', {'fields': ('role',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Role', {'fields': ('role',)}),)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type']
    readonly_fields = ['created_at']
