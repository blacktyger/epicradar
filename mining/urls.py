from django.urls import path
from . import views

urlpatterns = [

    path('', views.MiningView.as_view(), name='home-mining'),
    path('ajax/', views.mining_ajax, name='ajax_calculator'),
    path('json/', views.JsonMinerCalculatorView.as_view(), name='json-calculator'),
    ]
