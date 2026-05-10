from django.shortcuts import get_object_or_404, render

from cart.cart import CartSession, serialize_product, serialize_products

from .models import Category, Product


def catalog_view(request):
    categories = Category.objects.all()
    category_slug = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()

    products = Product.objects.select_related('category').filter(in_stock=True)

    cart_quantities = CartSession(request).get_quantities()
    serialized_products = serialize_products(products, cart_quantities)

    context = {
        'products': serialized_products,
        'categories': categories,
        'active_category': category_slug,
        'results_count': len(serialized_products),
        'search_query': search_query,
    }
    return render(request, 'catalog/catalog.html', context)


def product_detail_view(request, slug):
    cart_quantities = CartSession(request).get_quantities()
    product_obj = get_object_or_404(Product.objects.select_related('category'), slug=slug, in_stock=True)
    product = serialize_product(product_obj, cart_quantities.get(str(product_obj.pk), 0))
    related = serialize_products(
        Product.objects.select_related('category')
        .filter(category=product_obj.category, in_stock=True)
        .exclude(pk=product_obj.pk)[:4],
        cart_quantities,
    )
    context = {
        'product': product,
        'related_products': related,
    }
    return render(request, 'catalog/product_detail.html', context)
