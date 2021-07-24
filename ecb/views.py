from django.views.generic.base import TemplateView
from core.manager.epic_wallet import WalletManager
from authentication.forms import SignUpForm
from wallet.forms import TransactionForm
from django.http import JsonResponse
from django.core import serializers
from core.db import db
from .models import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger('ECB')


def initialize():
    logger.debug(f"INITIALIZING BLOCKCHAIN ...")
    ecb, created = Blockchain.objects.get_or_create(id=0)
    print(ecb, created)

    if created:
        logger.debug(f"SETTING NODE(USER) AND COINBASE(WALLET) ...")
        ecb.node = User.objects.get_or_create(username=ecb.name)[0]
        ecb.coinbase = Wallet.objects.get_or_create(
            owner=ecb.node, blockchain=ecb, balance=ecb.total_supply)[0]
        ecb.save()

        logger.debug(f"CREATING GENESIS BLOCK ...")
        Block.objects.create(
            proof=54,
            id=0,
            timestamp=timezone.now(),
            blockchain=ecb,
            previous_hash='If you reading this, talk via telegram to '
                          '@blacktyg3r with code "5445", 3 epics reward ;)')

    logger.debug(f"BLOCKCHAIN '{ecb.name}' SET AND READY!")

    return ecb


blockchain = initialize()


class PersonalWalletView(TemplateView):
    template_name = 'personal_wallet.html'
    context_object_name = 'wallets'
    model = Wallet
    wallet = WalletManager()

    def post(self, *args, **kwargs):
        if self.request.is_ajax and self.request.method == "POST":
            amount = Decimal(self.request.POST.get('amount')) or None
            sender = Wallet.objects.get(owner=self.request.user)
            send_method = self.request.POST.get('send_method')

            try:
                recipient = self.request.POST.get('recipient')
                if '@' in str(recipient):
                    username = recipient.split('@')[1]
                else:
                    username = recipient
                user = User.objects.get(username=username)
                recipient = Wallet.objects.filter(Q(owner=user) | Q(telegram_user=user))[0]
            except:
                recipient = None

            if amount:
                if amount <= sender.balance:
                    if recipient:
                        tx = sender.send(recipient, amount)
                        if tx:
                            # json_tx = serializers.serialize('json', [tx])
                            response = {
                                'transaction': 1,
                                'balance': round(tx.sender.balance, 3),
                                'locked': round(tx.sender.locked, 3),
                                'status': 'success',
                                'message': "Transaction sent successfully!"
                                }
                            print('YAY!')
                            return JsonResponse(response, status=200)
                        else:
                            response = {
                                'transaction': None,
                                'status': 'danger',
                                'message': "Something went wrong, no more details yet."
                                }
                            return JsonResponse(response, status=200)
                    else:
                        response = {
                            'transaction': None,
                            'status': 'warning',
                            'message': "Can't find recipient, check address."
                            }
                        return JsonResponse(response, status=200)
                else:
                    response = {
                        'transaction': None,
                        'status': 'warning',
                        'message': "Balance is too low."
                        }
                    return JsonResponse(response, status=200)
            else:
                response = {
                    'transaction': None,
                    'status': 'warning',
                    'message': "Can't send 0 EPIC"
                    }
                return JsonResponse(response, status=200)

    def get_context_data(self, **kwargs):
        context = super(PersonalWalletView, self).get_context_data(**kwargs)
        context['blockchain_size'] = self.wallet.blockchain_size()
        context['node_is_online'] = self.wallet.node_is_online()
        context['currency_list'] = db.currency
        context['transactions'] = self.wallet.get_txs()[:5]
        context['epic_prices'] = [db.epic_to(x) for x in ['GBP', 'CNY']]
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