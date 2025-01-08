from paycomuz.views import MerchantAPIView
from paycomuz import Paycom
from django.shortcuts import  get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from cart.models import Order
from main.models import Product
from bot.loader import notify_seller
from django.http import JsonResponse
from django.utils.timezone import localtime
import requests
import json

class CheckOrder(Paycom):
    def check_order(self, amount, account, *args, **kwargs):
        print(account)
        order = Order.objects.filter(id=account['order_id'], payment_status="pending").first()
        print(order)
        if not order:
            return self.ORDER_NOT_FOND
        if order.total_price * 100 != amount:
            return self.INVALID_AMOUNT
        return self.ORDER_FOUND

    def successfully_payment(self, account, transaction, *args, **kwargs):
        order = Order.objects.filter(id=transaction.order_key).first()
        print(order)
        
        if not order:
            return self.ORDER_NOT_FOUND
        order.payment_status = "completed"
        order.save()
        product_details = ', '.join([f"{item.product.name} ({item.color.color.name if item.color else 'No Color'}, {item.quantity})\n" for item in order.items.all()])
        print(product_details)
        print(order.items.first().product.seller.telegram_id)
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
💳 To'lov holati: To'langan"""
        notify_seller(order.items.first().product.seller.telegram_id,message,order_id=order.id)

    def cancel_payment(self, account, transaction, *args, **kwargs):
        pass


class TestView(MerchantAPIView):
    VALIDATE_CLASS = CheckOrder



def create_payment(order_id, amount):
    url = "https://payme.uz/api/v1/checkout"
    headers = {
        'Authorization': f"Bearer {'9V1C8bOP2yF2pRzG&w#wEiIsq0DMPWO9&J4f'}"
    }
    data = {
        'merchant_id': '675b22e4b42aa8a5ada9d7a6',
        'order_id': order_id,  # order_id ni o'zgartirish
        'amount': amount,
        'description': 'Buyurtma uchun to\'lov',
    }
    response = requests.post(url, json=data, headers=headers)
    return response.text
