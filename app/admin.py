# -*- encoding: utf-8 -*-
from django.contrib import admin
from .models import *

admin.site.register((Coin, Currency, Price, Explorer, Network, Vitex, Stellar, Pancake, Orderbook))
