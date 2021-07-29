# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this
from .views import *

urlpatterns = [
    path(r'', WalletHomeView.as_view(), name='wallet-home'),
    path("", include("authentication.urls")),

    ]
