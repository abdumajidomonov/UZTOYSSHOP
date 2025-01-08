from paycomuz import Paycom
import json
import uuid
import base64
from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import F, Sum
from django.utils.timezone import localtime
from .models import Cart, CartItem, Product, ProductColor, Address, Order, OrderItem
from bot.loader import notify_seller
from .sms import send_sms_verification




def cart_view(request):
    # Foydalanuvchining savatchasi
    cart_items = CartItem.objects.filter(cart=get_or_create_cart(request))  
    total_price = sum(
        item.product.final_price * item.quantity 
        for item in cart_items 
        if item.color.stock_quantity > 0
    )  # Umumiy narxni hisoblash
    second_total_price = sum(
        item.product.price * item.quantity 
        for item in cart_items 
        if item.color.stock_quantity > 0
    )  
    saving_money = second_total_price - total_price
    total_quantity = sum(item.quantity for item in cart_items if item.color.stock_quantity > 0)  # Umumiy mahsulotlar soni
    total_price = f"{int(total_price):,}".replace(",", " ")
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_quantity': total_quantity,
        'second_total_price':f"{int(second_total_price):,}".replace(",", " "),
        "saving_money":f"{int(saving_money):,}".replace(",", " "),
    }
    return render(request, 'cart.html', context)
def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # Foydalanuvchi tizimga kirmasa, yangi xarid savatini yaratish
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = get_object_or_404(Cart, id=cart_id)
        else:
            cart = Cart.objects.create()  # Yangi xarid savatini yaratish
            request.session['cart_id'] = cart.id  # Sessiyaga saqlash
    return cart
def calculate_cart_totals(cart):
    # Cart'dagi mahsulotlar soni va narxini optimallashtirilgan holda olish
    totals = cart.items.aggregate(
        total_count=Sum('quantity'),  # Mahsulotlar soni
        total_price=Sum(F('product__final_price') * F('quantity')),  # Mahsulotlar narxi
        second_total_price=Sum(F('product__price') * F('quantity'))  # Mahsulotlar narxi
    )

    # Agar totals bo'sh bo'lsa (masalan, savat bo'sh bo'lsa), 0 qiymatlarni qaytaramiz
    cart_count = cart.items.count()  # Savatdagi umumiy mahsulotlar soni
    total_price = totals['total_price'] or Decimal(0)  # Umumiy narx
    second_total_price =  totals['second_total_price'] or Decimal(0)
    savin_money = second_total_price - total_price
    total_price = f"{int(total_price):,}".replace(",", " "),
    second_total_price = f"{int(second_total_price):,}".replace(",", " "),
    savin_money = f"{int(savin_money):,}".replace(",", " "),
    
    return cart_count, total_price, second_total_price, savin_money
def add_to_cart(request):
    # JSON ma'lumotni olish
    data = json.loads(request.body)
    product_id = data.get('product_id')
    color_id = data.get('color_id')
    quantity = int(data.get('quantity', 1))  # Agar quantity berilmasa, uni 1 deb olamiz
    color = ProductColor.objects.get(id=color_id)
    # Mahsulotni olish
    product = get_object_or_404(Product, id=product_id)
    
    # Foydalanuvchi uchun yoki umumiy savat yaratish
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        cart = get_or_create_cart(request)  # Session yaratish

    # CartItem qo'shish yoki mavjudini yangilash
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product,color=color)
    if created:
        cart_item.quantity = quantity  # Agar yangi bo'lsa, berilgan miqdorni o'rnatamiz
    else:
        cart_item.quantity += quantity  # Mavjud bo'lsa, miqdorni oshiramiz
    cart_item.save()
    cart_count, cart_total_price, second_total_price, savin_money = calculate_cart_totals(cart)
    return JsonResponse({'message': 'Mahsulot savatga qo\'shildi','cart_count':cart_count,'cart_total_price':cart_total_price,'second_total_price':second_total_price,'savin_money':savin_money})

def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        # Xarid savatidan mahsulotni o'chirish
        CartItem.objects.filter(id=cart_item_id).delete()
        cart_count, cart_total_price, second_total_price, savin_money = calculate_cart_totals(get_or_create_cart(request))

        context = {
            'message': 'Mahsulot xarid savatidan o\'chirildi',
            'total_price': cart_total_price,
            'total_quantity': cart_count,
            'second_total_price':second_total_price,
            'savin_money':savin_money
        }
        return JsonResponse(context)
    return JsonResponse({'error': 'Noto‘g‘ri so‘rov'}, status=400)
def update_cart_item_quantity(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        new_quantity = data.get('quantity')

        # CartItem ni yangilash
        try:
            cart_item = CartItem.objects.get(id=cart_item_id)
            if cart_item.color.stock_quantity < round(float(new_quantity)):
                return JsonResponse({'success':False,'message': f'Mahsulot bazada yetarlik emas. Hozirda {cart_item.color.stock_quantity} mavjud'}, status=200)
            cart_item.quantity = round(float(new_quantity))  # Yangi miqdorni o'rnatamiz
            cart_item.save()
            cart_count, cart_total_price, second_total_price, savin_money = calculate_cart_totals(get_or_create_cart(request))

            context = {
                'success':True,
                'message': 'Miqdor yangilandi',
                'total_price': cart_total_price,
                'total_quantity': cart_count,
                'second_total_price':second_total_price,
                'savin_money':savin_money
            }
            return JsonResponse(context)
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'CartItem topilmadi'}, status=404)

    return JsonResponse({'error': 'Noto‘g‘ri so‘rov'}, status=400)
def checkout(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request,'Buyurtma uchun avval tizimga kiring!')
            return redirect('/cart/?next=/cart/#login')
        cart_items = CartItem.objects.filter(id__in=list(map(int, request.POST.getlist('product'))))  
        if cart_items:
            total_price = sum(item.product.final_price * item.quantity for item in cart_items)  # Umumiy narxni hisoblash
            total_quantity = sum(item.quantity for item in cart_items)  # Umumiy mahsulotlar soni
            total_price = f"{int(total_price):,}".replace(",", " ")
            context = {
                'cart_items': cart_items,
                'total_price': total_price,
                'total_quantity': total_quantity,
            }
            return render(request,'checkout.html',context)
        else:
            messages.error(request, "Mahsulot tanlanmagan!")
            return redirect('cart:cart')
    return redirect('main:home')

@login_required
def creat_order(request):
    if request.method == 'POST':
        if request.POST.get('payment_method') == "cash":
            address = Address.objects.create(latitude=request.POST.get('latitude'),longitude=request.POST.get('longitude'))  # "addressCode" maydonini olish
            product_ids = request.POST.getlist('product_id')  # "product_id" maydonini olish (ro'yxat shaklida)
            product_quantities = request.POST.getlist('product_quantity')  # "product_quantity" maydonini olish (ro'yxat shaklida)
            product_colors = request.POST.getlist('product_color')  # "product_color" maydonini olish (ro'yxat shaklida)
            
            # Ensure total_price is cleaned of any spaces and converted to Decimal
            total_price_str = request.POST.get('total_price')  # Get the total price as a string
            total_price = Decimal(total_price_str.replace(' ', ''))  # Remove spaces and convert to Decimal
            product = Product.objects.filter(id=product_ids[0]).first()

                # Create the Order object
            order = Order.objects.create(
                address=address,
                user=request.user,
                status="P",
                total_price=total_price,
            )
                
            # Create OrderItem objects for each product
            for product_id, quantity, color_id in zip(product_ids, product_quantities, product_colors):
                product = get_object_or_404(Product, id=product_id)  # Get the product or return 404 if not found
                color = get_object_or_404(ProductColor, id=color_id) if color_id else None  # Get the product color or None
                # Create the OrderItem for each product
                try:
                    CartItem.objects.filter(cart=get_or_create_cart(request),product=product,color=color).delete()
                except:
                    pass    
                product.order_count = product.order_count + 1
                if int(color.stock_quantity) >= int(quantity):
                    color.stock_quantity = int(color.stock_quantity) - int(quantity)
                else:
                    order.delete()
                    return JsonResponse({'error': f'Mahsulot bazada yetarli emas - {product.name}'}, status=400)
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=int(quantity),  # Ensure quantity is an integer
                    color=color,
                    price=product.price  # Assuming `price` is an attribute of the `Product` model
                )
            product_details = ', '.join([f"{item.product.name} ({item.color.color.name if item.color else 'No Color'}, {item.quantity})\n" for item in order.items.all()])
            message = f"""🎉 Yangi buyurtma qabul qilindi! 🎉
📄 ID: {order.id}
👤 Buyurtmachi: {order.user.first_name} {order.user.last_name}
📞 Telefon: +{order.user.phone_number}
🕒 Buyurtma vaqti: {localtime(order.created_at).strftime('%d.%m.%Y %H:%M')}
🛍️ Mahsulot: \n{product_details}
🏷️ Toifasi: {order.get_all_categories()}
🔢 Soni: {order.total_quantity()} ta
💰 Narx: {order.get_format_price()} so'm
📍 Yetkazib berish joyi: <a href="https://www.google.com/maps/search/{order.address.latitude}+{order.address.longitude}">Manzil</a>
💳 To'lov holati: To'lanmagan❌"""
            notify_seller(get_object_or_404(Product, id=product_id).seller.telegram_id,message,order_id=order.id)
            messages.success(request,'Buyurtma tekshiruvga yuborildi')
            return redirect('main:my-orders')
        else:
            address = Address.objects.create(latitude=request.POST.get('latitude'),longitude=request.POST.get('longitude'))  # "addressCode" maydonini olish
            product_ids = request.POST.getlist('product_id')  # "product_id" maydonini olish (ro'yxat shaklida)
            product_quantities = request.POST.getlist('product_quantity')  # "product_quantity" maydonini olish (ro'yxat shaklida)
            product_colors = request.POST.getlist('product_color')  # "product_color" maydonini olish (ro'yxat shaklida)
            
            # Ensure total_price is cleaned of any spaces and converted to Decimal
            total_price_str = request.POST.get('total_price')  # Get the total price as a string
            total_price = Decimal(total_price_str.replace(' ', ''))  # Remove spaces and convert to Decimal
            product = Product.objects.filter(id=product_ids[0]).first()

                # Create the Order object
            order = Order.objects.create(
                address=address,
                user=request.user,
                status="P",
                total_price=total_price,
                payment_method="payme"
            )
            # Create OrderItem objects for each product
            for product_id, quantity, color_id in zip(product_ids, product_quantities, product_colors):
                product = get_object_or_404(Product, id=product_id)  # Get the product or return 404 if not found
                color = get_object_or_404(ProductColor, id=color_id) if color_id else None  # Get the product color or None
                # Create the OrderItem for each product
                # try:
                #     CartItem.objects.filter(cart=get_or_create_cart(request),product=product,color=color).delete()
                # except:
                #     pass    
                product.order_count = product.order_count + 1
                if int(color.stock_quantity) >= int(quantity):
                    color.stock_quantity = int(color.stock_quantity) - int(quantity)
                else:
                    order.delete()
                    return JsonResponse({'error': f'Mahsulot bazada yetarli emas - {product.name}'}, status=400)
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=int(quantity),  # Ensure quantity is an integer
                    color=color,
                    price=product.price  # Assuming `price` is an attribute of the `Product` model
                )
            LINK = 'https://checkout.paycom.uz'

            # print(order.total_price, "_________________________________")
            amount = order.total_price * 100
            print(amount, "________________________________")
            params = f"m={'675b22e4b42aa8a5ada9d7a6'};ac.{'order_id'}={order.id};a={amount};c={'https://f839-213-230-88-234.ngrok-free.app/profile'}"
            encode_params = base64.b64encode(params.encode("utf-8"))
            encode_params = str(encode_params, 'utf-8')
            url = f"{LINK}/{encode_params}"
            print(url)

            # print(amount_price,order.id,type(order.total_price), "_______________________")
            # url = paycom.create_initialization(amount=amount_price, order_id=str(order.id), return_url='')
            return redirect(url)
    return JsonResponse({'error': 'Noto‘g‘ri so‘rov'}, status=400)


@csrf_exempt
def save_order_date(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # JSON formatida kelgan ma'lumotni o'qish
            order_id = data.get('order_id')  # Order ID
            order_date = data.get('order_date')  # Sana (YYYY-MM-DD formatida)

            # Sana va ID ni tekshirish
            order_date_obj = datetime.strptime(order_date, '%Y-%m-%d').date()

            order = Order.objects.get(id=order_id)
            if order.payment_method == "payme" and order.payment_status == "pending":
                return JsonResponse({"status": "error", "message": "Hali Buyurma puli to'lanmagan!"})
            order_items = OrderItem.objects.filter(
                order=order,
                quantity__gt=F('color__stock_quantity')  # quantity product_color__quantity'dan katta bo'lishi kerak
            ).exists()

            if not order_items:
                for item in order.items.all():
                    color = ProductColor.objects.get(id=item.color.id)
                    color.stock_quantity -= item.quantity
                    color.save()

                order.date = order_date_obj
                order.status = "M"
                order.save()
                send_sms_verification(order.user.phone_number,f"Sizning buyurtmangiz № {order.id} tasdiqlandi. {order_date_obj} sanasida yetkazib beriladi")
                import locale
                locale.setlocale(locale.LC_TIME, 'uz_UZ.UTF-8')
                formatted_date = order_date_obj.strftime('%d-%B, %Y-yil')
                return JsonResponse({"status": "success", "message": "Order date updated successfully",'formatted_date':formatted_date})
            else:
                return JsonResponse({"status": "error", "message": "Mahsulot bazada tugab qoldi"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request method"})
@csrf_exempt
def cancel_order(request):
    data = json.loads(request.body)  # JSON formatida kelgan ma'lumotni o'qish
    order_id = data.get('order_id')
    reason = data.get('reason')
    # Buyurtmani ID bo'yicha topamiz
    order = get_object_or_404(Order, id=order_id)
    order.status = 'F'
    order.save()
    send_sms_verification(order.user.phone_number,f"""Hurmatli foydalanuvchi, sizning № {order.id} buyurtmangiz bekor qilindi. Sabab: {reason}. Agar bu xato bo'lsa yoki qayta buyurtma bermoqchi bo'lsangiz, iltimos, biz bilan bog'laning. Tushunganingiz uchun rahmat!""")
    return JsonResponse({"status": "success", "message": "Order date updated successfully"})