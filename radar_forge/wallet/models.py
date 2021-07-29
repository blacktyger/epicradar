from django.contrib.auth.models import User
from django.db import models
from decimal import Decimal
import jsonfield
import hashlib
import uuid
import os


class Account(models.Model):
    address = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet')
    code = models.IntegerField(default=1111)
    name = models.CharField(max_length=70, blank=False, default='Default')
    telegram_user = models.CharField(max_length=70, blank=True, null=True)
    balance = models.DecimalField(max_digits=32, decimal_places=8, blank=True, default=0)
    create_at = models.DateTimeField(auto_now=True)
    data = jsonfield.JSONField(default={})

    def __str__(self):
        return f"[{self.owner.username}]{self.name}"

    def enough_balance(self, amount):
        if self.balance < Decimal(amount):
            return False
        else:
            return True

    @staticmethod
    def hash_(key):
        """Hash a key."""
        salt = os.urandom(32)
        hash_key = hashlib.pbkdf2_hmac(
            'sha256', key.encode('utf-8'), salt, 100000)

        stored_password = salt + hash_key
        return stored_password

    @staticmethod
    def verify_(stored_password, provided_password):
        """Verify a stored key against one provided by user"""
        salt = stored_password[:32]
        stored_password = stored_password[32:]
        new_key = hashlib.pbkdf2_hmac(
            'sha256', provided_password.encode('utf-8'), salt, 100000)
        return new_key == stored_password

