from .models import Cart
from decimal import Decimal
from .views import get_or_create_cart

def cart_count(request):
    # Savatdagi mahsulotlar sonini va jami narxni hisoblash
    cart_count = 0
    cart_total_price = Decimal(0)
    try:
        # Foydalanuvchi uchun savatni olish
        cart = get_or_create_cart(request)
        cart_count = cart.items.count()
        cart_total_price = sum(item.product.final_price * item.quantity for item in cart.items.all())
    except Cart.DoesNotExist:
        pass

    # Decimal qiymatini to'liq butun son sifatida ko'rsatish
    cart_total_price = str(cart_total_price).split('.')[0]
    cart_total_price = f"{int(cart_total_price):,}"
    return {'cart_count': cart_count, 'cart_total_price': cart_total_price}

