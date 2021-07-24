from django.contrib import admin
from .models import UserTransaction, SwapicTransaction, Transaction

admin.site.register((UserTransaction, SwapicTransaction, Transaction))

