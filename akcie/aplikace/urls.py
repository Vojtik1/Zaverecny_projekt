from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('stock/<str:ticker>/', views.stock_detail, name='stock_detail'),
]
