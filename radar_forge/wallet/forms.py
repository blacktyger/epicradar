from django import forms
from django.forms import ModelChoiceField

from ecb.models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('amount', 'sender', 'recipient')
        widgets = {
            'recipient': forms.TextInput(attrs={'class': 'form-control', 'id': 'ecb_recipient_form'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'id': 'ecb_amount_form', 'required': True})
            }
