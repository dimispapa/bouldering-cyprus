from django.shortcuts import render
from .models import Product


def shop_view(request):
    products = Product.objects.filter(is_active=True)
    context = {"products": products}

    return render(request, "shop/shop.html", context)
