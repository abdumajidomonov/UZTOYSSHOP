from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path('',views.home,name="home"),
    path('product_list/',views.product_list,name="product_list"),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path("rate-product/", views.rate_product, name="rate_product"),
    path('contact/', views.contact, name='contact'),
    path('toggle-favorite/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('my-orders/',views.orders_view,name="my-orders"),
    path('faq/', views.FAQListView.as_view(), name='faq'),
]
