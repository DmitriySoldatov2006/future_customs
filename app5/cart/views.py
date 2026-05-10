from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .cart import CartSession, format_price


def _wants_json(request):
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )


def _cart_payload(cart, product_id):
    product_key = str(product_id or "")
    return {
        "cart_count": cart.count(),
        "product_id": product_key,
        "quantity": cart.get_quantities().get(product_key, 0),
    }


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
    cart = CartSession(request)
    product_id = request.POST.get("product_id")
    cart.add(product_id=product_id, quantity=request.POST.get("quantity", 1))
    if _wants_json(request):
        return JsonResponse(_cart_payload(cart, product_id))
    return redirect("cart_view")


@require_POST
def cart_remove(request):
    cart = CartSession(request)
    product_id = request.POST.get("product_id")
    cart.remove(product_id)
    if _wants_json(request):
        return JsonResponse(_cart_payload(cart, product_id))
    return redirect("cart_view")


@require_POST
def cart_update(request):
    cart = CartSession(request)
    product_id = request.POST.get("product_id")
    cart.update(product_id=product_id, quantity=request.POST.get("quantity", 1))
    if _wants_json(request):
        return JsonResponse(_cart_payload(cart, product_id))
    return redirect("cart_view")
