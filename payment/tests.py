import requests

# Paycomga yuboriladigan ma'lumotlar
data = {
    'merchant': '675b22e4b42aa8a5ada9d7a6',  # Sizning merchant ID
    'amount': '100000',  # To'lov miqdori (TIINlarda)
    'account[order_id]': '{68}',  # Account obyekti uchun kerakli maydon
    'lang': 'ru',  # Til (ru, uz, en)
    'callback': 'https://youtube.com',  # URL, qaytgan to'lovdan keyin redirect bo'ladigan manzil
    'callback_timeout': '15000',  # To'lovdan keyin qachon redirect bo'lishini belgilovchi vaqt (ms)
    'description': 'hechnima',  # To'lov haqida qisqacha ma'lumot
    'detail': 'something'  # To'lovning batafsil ma'lumotlari (BASE64 formatida)
}

# Paycomga POST so'rovini yuborish
url = "https://checkout.paycom.uz/api/"
response = requests.post(url, data=data)

# Javobni tekshirish
if response.status_code == 200:
    print("So'rov muvaffaqiyatli yuborildi.")
    print("Javob:")
    print(response.text)  # Paycomdan kelgan javobni chiqarish
else:
    print("So'rov yuborishda xatolik yuz berdi.")
    print("Xatolik kodi:", response.status_code)
