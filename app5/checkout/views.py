from decimal import Decimal

from django.shortcuts import redirect, render

from cart.cart import CART_SESSION_KEY, CartSession, format_price

from .forms import CheckoutForm
from .models import Order, OrderItem


def _get_checkout_summary(request):
    cart = CartSession(request)
    cart_items = cart.items()
    cart_total = cart.total()
    return cart_items, cart_total


def checkout_view(request):
    cart_items, cart_total = _get_checkout_summary(request)
    if not cart_items:
        return redirect('cart_view')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=form.cleaned_data['full_name'],
                phone=form.cleaned_data['phone'],
                region=form.cleaned_data['region'],
                city=form.cleaned_data['city'],
                address=form.cleaned_data['address'],
                total=Decimal(cart_total),
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        product_id=item['id'],
                        name=item['name'],
                        quantity=item['quantity'],
                        price=Decimal(item['unit_price']),
                    )
                    for item in cart_items
                ]
            )
            request.session.pop(CART_SESSION_KEY, None)
            request.session.modified = True
            return redirect('checkout_success')
    else:
        form = CheckoutForm()

    context = {
        'form': form,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_total_display': format_price(cart_total),
    }
    return render(request, 'checkout/checkout.html', context)


def checkout_success_view(request):
    return render(request, 'checkout/success.html')
