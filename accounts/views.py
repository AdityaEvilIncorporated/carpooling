from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction as db_transaction
from decimal import Decimal

from .models import User, Wallet, Transaction
from .forms import RegisterForm, LoginForm, TopUpForm, ChangeRoleForm


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome {user.username}!')
            if user.is_driver():
                return redirect('/trips/dashboard/')
            return redirect('/requests/dashboard/')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                if user.is_driver():
                    return redirect('/trips/dashboard/')
                return redirect('/requests/dashboard/')
            messages.error(request, 'Wrong username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')


@login_required
def profile_view(request):
    wallet = request.user.get_wallet()
    transactions = wallet.transactions.select_related('trip').all()[:20]
    role_form = ChangeRoleForm(initial={'role': request.user.role})
    return render(request, 'accounts/profile.html', {
        'wallet': wallet,
        'transactions': transactions,
        'role_form': role_form,
    })


@login_required
def change_role_view(request):
    if request.method == 'POST':
        form = ChangeRoleForm(request.POST)
        if form.is_valid():
            request.user.role = form.cleaned_data['role']
            request.user.save()
            messages.success(request, f'Role changed to {request.user.role}')
            if request.user.is_driver():
                return redirect('/trips/dashboard/')
            return redirect('/requests/dashboard/')
    return redirect('profile')


@login_required
def topup_view(request):
    wallet = request.user.get_wallet()
    if request.method == 'POST':
        form = TopUpForm(request.POST)
        if form.is_valid():
            amount = Decimal(str(form.cleaned_data['amount']))
            with db_transaction.atomic():
                wallet.credit(amount)
                Transaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    transaction_type='topup',
                    description=f'Added ${amount}',
                )
            wallet.refresh_from_db()
            messages.success(request, f'Added ${amount}! Balance: ${wallet.balance}')
            return redirect('profile')
    else:
        form = TopUpForm()
    return render(request, 'accounts/topup.html', {'form': form, 'wallet': wallet})


@login_required
def wallet_view(request):
    wallet = request.user.get_wallet()
    transactions = list(wallet.transactions.select_related('trip').all())
    total_in = sum(t.amount for t in transactions if t.transaction_type in ('topup', 'driver_earning', 'refund'))
    total_out = sum(t.amount for t in transactions if t.transaction_type == 'fare_deduction')
    return render(request, 'accounts/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
        'total_in': total_in,
        'total_out': total_out,
    })
