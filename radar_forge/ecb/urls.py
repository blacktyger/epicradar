# -*- encoding: utf-8 -*-

from django.urls import path, include  # add this
from .views import *

urlpatterns = [
    path("", PersonalWalletView.as_view(), name='personal-wallet'),
    ]
