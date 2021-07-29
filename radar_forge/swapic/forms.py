from django import forms
from django.forms import TextInput, NumberInput, RadioSelect, Select


SIDES = [('buy', 'Buy'), ('sell', 'Sell')]
PAIRS = [('btc', 'Bitcoin'), ('usd', 'USD(T)')]
EXCHANGES = [('vitex', 'ViteX'), ('citex', 'Citex')]


class StellarTraderForm(forms.Form):
    spend = forms.FloatField(widget=NumberInput(attrs={
        'class': "form-control px-3",
        'id': "spend",
        'placeholder': '0.00',
        'autocomplete ': 'off',
        'style': "font-size: 1.2rem;"
        }), required=False)

    buy = forms.FloatField(widget=NumberInput(attrs={
        'class': "form-control px-3",
        'id': "buy",
        'placeholder': '0.00',
        'autocomplete ': 'off',
        'style': "font-size: 1.2rem;"
        }), required=False)
