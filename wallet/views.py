from core.manager.epic_wallet import WalletManager
from ecb.models import Transaction, Wallet
from django.views.generic.base import TemplateView
from authentication.forms import SignUpForm
from ecb.views import blockchain
from .forms import TransactionForm
from core.db import db
from .models import *


class WalletHomeView(TemplateView):
    template_name = 'wallet-home.html'
    context_object_name = 'wallets'
    wallet = WalletManager()
    model = Account

    def get_context_data(self, **kwargs):
        context = super(WalletHomeView, self).get_context_data(**kwargs)
        context['blockchain_size'] = self.wallet.blockchain_size()
        context['node_is_online'] = self.wallet.node_is_online()
        context['currency_list'] = db.currency
        context['transactions'] = self.wallet.get_txs()[:5]
        context['epic_prices'] = [db.epic_to(x) for x in ['GBP', 'CNY']]
        context['vitex_price'] = db.vitex['ticker']['closePrice']
        context['epic_vs_usd'] = db.epic_vs_usd
        context['node_data'] = self.wallet.node_data()
        context['balances'] = self.wallet.get_balance()
        context['users'] = User.objects.all()
        context['form'] = SignUpForm()
        context['ecb'] = {
            'transaction_form': TransactionForm(),
            'transactions': Transaction.objects.filter(status='completed'),
            'coinbase': blockchain.coinbase,
            'wallets': Wallet.objects.all(),
            'volume': sum(tx.amount for tx in Transaction.objects.filter(status='completed'))
            }

        if self.request.user.is_authenticated:
            user_wallet, created = Wallet.objects.get_or_create(owner=self.request.user)
            context['ecb']['user_wallet'] = user_wallet,
            context['ecb']['user_wallet_transactions'] = user_wallet.transactions()[:5],

        return context

