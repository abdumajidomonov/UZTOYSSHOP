import json
import requests
import re
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta, datetime
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.views.generic import ListView
from .models import Product, Category, Banner,Brend,Color,Rating, Favorite, FAQ
from .forms import ContactForm
from cart.models import Order


def get_current_season():
    month = datetime.now().month

    if month in [12, 1, 2]:
        return 10
    elif month in [3, 4, 5]:
        return 11
    elif month in [6, 7, 8]:
        return 12
    else:  # 9, 10, 11
        return 13
# Create your views here.
def home(request):
    # Баннерлар, категориялар ва маҳсулотларни олиш
    banners = Banner.objects.all().order_by('-id')  # Ҳамма баннерларни оламиз

    # Янги маҳсулотларни фильтрлаш (сўнгги 30 кун ичида яратилган)
    last_30_days = timezone.now() - timedelta(days=100)
    
    # Category, Brend ва рейтинг билан бирга маҳсулотларни олдиндан юклаш
    new_products = Product.objects.filter(created_at__gte=last_30_days, show_product=True)\
                              .select_related('brend') \
                              .prefetch_related('category', 'ratings').order_by('-id')[:12]
    
    # Қолган маҳсулотлар ҳам худди шундай усулда олинади
    products = Product.objects.filter(show_product=True,discount__gt=0)  \
                              .select_related('brend') \
                              .prefetch_related('category', 'ratings').order_by('-id')[:4]
    random_products = Product.objects.filter(show_product=True)\
        .exclude(Q(id__in=new_products.values_list('id', flat=True)) | Q(id__in=products.values_list('id', flat=True)))\
        .select_related('brend')\
        .prefetch_related('category', 'ratings')\
        .order_by('?')[:12] 
    # Категорияларни оламиз
    categories = Category.objects.all().order_by('-id')
    season_category = Category.objects.get(id=get_current_season())
    season_products = Product.objects.filter(category=season_category).order_by('-id')[:2]
    context = {
        'banners': banners,
        'categories': categories.exclude(id__in=[10,11,12,13]),
        'products': products,  # Қолган маҳсулотлар
        'season_products':season_products,
        'season_category':season_category,
        'new_products': new_products,  # Янги маҳсулотлар
        'random_products':random_products,
    }

    return render(request, 'home.html', context)
class FAQListView(ListView):
    model = FAQ
    template_name = 'faq.html'
    context_object_name = 'faqs'
def product_list(request):
    # Dastlab barcha mahsulotlarni olish
    products = Product.objects.all().filter(show_product=True).order_by('-id')
    category_param = request.GET.get('category')
    color_param = request.GET.get('color')
    brend_param = request.GET.get('brend')

    if category_param and ',' in category_param:
        # Vergul bilan ajratilganlarni listga o'zgartirish
        selected_categories = category_param.split(',')
    else:
        selected_categories = request.GET.getlist('category') 
    if color_param and ',' in color_param:
        # Vergul bilan ajratilganlarni listga o'zgartirish
        selected_colors = color_param.split(',')
    else:
        selected_colors = request.GET.getlist('color') 
    if brend_param and ',' in brend_param:
        # Vergul bilan ajratilganlarni listga o'zgartirish
        selected_brands = brend_param.split(',')
    else:
        selected_brands = request.GET.getlist('brend')

    # URL parametrlardan filtrlash qiymatlarini olish
    min_price = request.GET.get('price-from')
    max_price = request.GET.get('price-to')
    sorting = request.GET.get('sorting')
    query = request.GET.get('q', '')

    if query:
        products = products.filter(
            Q(name__icontains=query) |       # Mahsulot nomida qidiruv
            Q(description__icontains=query) |  # Tavsifda qidiruv
            Q(brend__name__icontains=query)    # Brend nomida qidiruv
        ).distinct() 
    if selected_categories:
        products = products.filter(category__name__in=selected_categories).distinct()
    if min_price:
        min_price_val = int(min_price)
        products = products.filter(final_price__gte=min_price_val)

    if max_price:
        max_price_val = int(max_price)
        products = products.filter(final_price__lte=max_price_val)

    # Ranglar bo'yicha filtrlash
    if selected_colors:
        products = products.filter(colors__color__color_code__in=selected_colors).distinct()

    # Brendlar bo'yicha filtrlash
    if selected_brands:
        products = products.filter(brend__name__in=selected_brands).distinct()

    if sorting == "ko'p sotilgan":
        products = products.order_by('-order_count')  # Eng ko'p sotilgan
    elif sorting == "arzon":
        products = products.order_by('final_price')  # Eng arzon
    elif sorting == "qimmat":
        products = products.order_by('-final_price')  # Eng qimmat
    elif sorting == "yangi":
        products = products.order_by('-created_at')

    categories = Category.objects.all()
    brands = Brend.objects.all()
    colors = Color.objects.all()

    # # Pagination
    paginator = Paginator(products,9)  # Har sahifada 10 mahsulot
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    banner = Banner.objects.all().order_by('?').first()
    high_price = Product.objects.all().aggregate(Max('final_price'))['final_price__max']

    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'colors': colors,
        'selected_categories': selected_categories,  # Form uchun tanlangan kategoriyalar
        'selected_min_price': min_price,      # Tanlangan minimal narx
        'selected_max_price': max_price,      # Tanlangan maksimal narx
        'selected_colors': selected_colors,             # Tanlangan ranglar
        'selected_brands': selected_brands,    
        'sorting': sorting,
        "banner": banner,  # Ҳамма баннерларни оламиз
        "high_price":high_price,
        'query':query
    }
    
    return render(request, 'filter.html', context)
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    category = product.category.all()  # Product obyektiga tegishli kategoriyalarni olish
    related_products = Product.objects.filter(category__in=category).exclude(id=product.id).distinct()[:4]  # Mahsulotning kategoriyasiga mos mahsulotlarni olish, hozirgi mahsulotni chiqarib tashlash
    try:
        user_rating = Rating.objects.get(user=request.user,product=product).rating
    except:
        user_rating = 0
    session_key = request.session.session_key

    # Foydalanuvchi tizimga kirmagan bo'lsa, session_keyni tekshiradi
    is_favorite = Favorite.objects.filter(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key if not request.user.is_authenticated else None,
        product_id=product_id
    ).exists()
    return render(request, 'detail.html', {
        'product': product,
        'related_products': related_products,
        'user_rating':user_rating,
        'rating_list': [5,4,3,2,1],
        'is_favorite':is_favorite,
    })
@csrf_exempt
def rate_product(request):
    if not request.user.is_authenticated:
        # Foydalanuvchi tizimga kirmagan bo'lsa, JSON javob qaytarish
        return JsonResponse({"success": False, "error": "Siz tizimga kirmagansiz. Reyting qo'shish uchun iltimos, tizimga kiring."}, status=401)

    if request.method == "POST":
        data = json.loads(request.body)
        product_id = data.get("product_id")
        rating_value = data.get("rating")

        try:
            product = Product.objects.get(id=product_id)

            # Reytingni yaratish yoki yangilash
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={"rating": rating_value}
            )

            return JsonResponse({"success": True, "created": created})

        except Product.DoesNotExist:
            return JsonResponse({"success": False, "error": "Mahsulot topilmadi"}, status=404)

    return JsonResponse({"success": False, "error": "Noto'g'ri so'rov"}, status=400)
def contact(request):
    if request.method == 'POST':
        post_data = request.POST.copy()

        # Telefon raqamini tozalash
        phone_number = post_data.get('phone_number', '')
        phone_number = re.sub(r'\D', '', phone_number)  # Faqat raqamlarni qoldirish
        if phone_number:
            phone_number = '+' + phone_number  # Boshiga "+" belgisini qo'shish
        post_data['phone_number'] = phone_number
        form = ContactForm(post_data)
        print(post_data)
        if form.is_valid():
            form.save()
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone_number = request.POST.get('phone_number')
            address = request.POST.get('address')
            description = request.POST.get('description')
            bot_token = '8100584262:AAE8h6k7Tp6b9oBHKUmG_cv1MQDgM3Qq0xA'  # O'zingizning bot tokeningizni qo'shing
            chat_id = '1831969115'  # O'zingizning chat ID'ingizni qo'shing

            # Xabarni tayyorlash
            telegram_message = (
                f"Yangi kontakt ma'lumoti:\n"
                f"Ism: {first_name}\n"
                f"Familya: {last_name}\n"
                f"Telefon raqami: {phone_number}\n"
                f"Manzil: {address}\n"
                f"Xabar: {description}"
            )
            # Xabarni yuborish
            response = requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                data={'chat_id': chat_id, 'text': telegram_message}
            )

            if response.status_code == 200:
                print(True)
                messages.success(request, 'Malumotlar menejerga yuborildi')
            else:
                print(False)
                messages.error(request, 'Xabar yuborishda xatolik yuz berdi!')
            return redirect('main:contact')  # Yaratilgan kontaktlar ro'yxatiga o'tish
        else:
            print("Form xatolari:", form.errors)
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})

# FAVORITE PRODUCTS

def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    session_key = request.session.session_key or request.session.create()
    
    if request.user.is_authenticated:
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    else:
        favorite, created = Favorite.objects.get_or_create(session_key=session_key, product=product)

    # Mahsulotni olib tashlash yoki qo'shish
    if not created:
        favorite.delete()
        status = 'removed'
    else:
        status = 'added'

    return JsonResponse({'status': status})


def favorite_list(request):
    session_key = request.session.session_key
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user)  # faqat user bilan
    else:
        favorites = Favorite.objects.filter(session_key=session_key)  # faqat session_key bilan
    
    # Extract products from favorites
    products = [favorite.product for favorite in favorites]
    
    # Set up pagination, 4 products per page
    paginator = Paginator(products, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'likeproduct.html', {'page_obj': page_obj})
@login_required
def orders_view(request):
    order = Order.objects.filter(user=request.user).order_by('-id')
    context = {
        'orders': order,
        'new_order': order.exclude(status__in=["F", "S"]),
    }
    return render(request, 'orders.html', context)
