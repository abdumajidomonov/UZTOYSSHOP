from django.urls import path
from . import views

app_name = "payment"

urlpatterns = [
    path('paycom/endpoint/', views.TestView.as_view()),
    # path('paycom/endpoint/create',views.create_payment,name="paycom")
]
