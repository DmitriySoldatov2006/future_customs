from django.shortcuts import redirect, render


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
    return redirect('/catalog/')


def product_detail(request):
    return redirect('/catalog/')
