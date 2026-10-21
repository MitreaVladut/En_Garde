from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import RegisterForm, LoginForm, AddressForm
from .models import Address
from apps.cart.utils import merge_guest_cart


def register_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:product_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            old_session_key = request.session.session_key
            user = form.save()
            # Log in the new user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # Merge guest session cart if present (Requirement A3)
            merge_guest_cart(request, user, old_session_key=old_session_key)
            messages.success(request, f'Welcome to En Garde Gear, {user.name}!')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('catalog:product_list')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:product_list')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            old_session_key = request.session.session_key
            user = form.get_user()
            login(request, user)
            # Requirement A3: Merge guest session cart into user cart at login
            merge_guest_cart(request, user, old_session_key=old_session_key)
            messages.success(request, f'Welcome back, {user.name}!')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            if user.is_staff and not next_url:
                return redirect('manage:dashboard')
            return redirect('catalog:product_list')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been safely logged out.')
    return redirect('catalog:product_list')


@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses': addresses})


@login_required
def address_create_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'New shipping address saved successfully.')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('accounts:address_list')
    else:
        form = AddressForm()

    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add New Address'})


@login_required
def address_update_view(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully.')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address', 'address': address})


@login_required
@require_POST
def address_delete_view(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)
    address.delete()
    messages.info(request, 'Address removed.')
    return redirect('accounts:address_list')
