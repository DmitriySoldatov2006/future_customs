from decimal import Decimal

from django.db import transaction
from django.shortcuts import redirect, render

from cart.cart import CART_SESSION_KEY, CartSession, format_price
from catalog.models import Product

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
            with transaction.atomic():
                products = {
                    str(product.pk): product
                    for product in Product.objects.select_for_update().filter(
                        pk__in=[item['pk'] for item in cart_items],
                    )
                }

                unavailable_items = []
                for item in cart_items:
                    product = products.get(str(item['pk']))
                    available_quantity = product.stock_quantity if product and product.in_stock else 0
                    if available_quantity < item['quantity']:
                        unavailable_items.append(item['name'])

                if unavailable_items:
                    form.add_error(
                        None,
                        'Некоторые товары недоступны в нужном количестве. Обновите корзину и попробуйте снова.',
                    )
                else:
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

                    for item in cart_items:
                        product = products[str(item['pk'])]
                        product.stock_quantity = max(0, product.stock_quantity - item['quantity'])
                        product.in_stock = product.stock_quantity > 0

                    Product.objects.bulk_update(products.values(), ['stock_quantity', 'in_stock'])
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
