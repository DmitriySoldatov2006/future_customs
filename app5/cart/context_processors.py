def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(item.get('quantity', 0) for item in cart.values() if isinstance(item, dict))
    return {'cart_count': count}
