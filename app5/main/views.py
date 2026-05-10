from django.shortcuts import redirect, render

from cart.cart import (
    DEFAULT_PRODUCT_ID,
    CartSession,
    get_catalog_products,
    get_product,
    get_related_products,
)


def index(request):
    return render(request, 'main/index.html')


def create(request):
    return render(request, 'main/create.html')


def basket(request):
    return redirect('cart_view')


def order(request):
    return render(request, 'main/order.html')


def legacy_register(request):
    return redirect('register')


def legacy_login(request):
    return redirect('login')


def catalog(request):
    cart_quantities = CartSession(request).get_quantities()
    products = get_catalog_products(cart_quantities)
    context = {
        'products': products,
        'results_count': len(products),
    }
    return render(request, 'main/catalog.html', context)


def product_detail(request):
    product_id = request.GET.get('product') or DEFAULT_PRODUCT_ID
    cart_quantities = CartSession(request).get_quantities()
    product = get_product(product_id) or get_product(DEFAULT_PRODUCT_ID)
    product['quantity'] = cart_quantities.get(product['id'], 0)
    product['in_cart'] = product['quantity'] > 0
    related_products = get_related_products(product['id'], cart_quantities)
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'main/product_detail.html', context)
