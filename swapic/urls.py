# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from django.urls import path
from .views import XLM_EPICJsonView, stellar_trader_handler

urlpatterns = [
    path('', stellar_trader_handler, name='swapic-home'),
    path('xlm_sepic_json/', XLM_EPICJsonView.as_view(), name='home_xlm_sepic'),
    ]
