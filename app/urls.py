# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from django.urls import path, re_path
from app import views

urlpatterns = [

    # The home page
    path('', views.HomeView.as_view(), name='home'),
    # Matches any html file

]
