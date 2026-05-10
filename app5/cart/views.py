from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .cart import CartSession, format_price


def cart_view(request):
    cart = CartSession(request)
    cart_items = cart.items()
    cart_total = cart.total()
    context = {
        "cart_items": cart_items,
        "cart_total": cart_total,
        "cart_total_display": format_price(cart_total),
    }
    return render(request, "cart/cart.html", context)


@require_POST
def cart_add(request):
    CartSession(request).add(
        product_id=request.POST.get("product_id"),
        quantity=request.POST.get("quantity", 1),
    )
    return redirect("cart_view")


@require_POST
def cart_remove(request):
    CartSession(request).remove(request.POST.get("product_id"))
    return redirect("cart_view")


@require_POST
def cart_update(request):
    CartSession(request).update(
        product_id=request.POST.get("product_id"),
        quantity=request.POST.get("quantity", 1),
    )
    return redirect("cart_view")
