from core.manager.orderbook import orderbook_check, check_impact
from core.manager.stellar import StellarNetworkManager
from .models import Swapic, Transaction
from app.templatetags.math import t_s
from django.http import JsonResponse
from .forms import StellarTraderForm
from django.shortcuts import render
from django.views import generic
from datetime import datetime
from decimal import Decimal
from core.db import db


swapic = Swapic()
swapic.manager.save_all_users_txs_to_db()


def user_confirmed_form(request):
    if request.method == 'GET':

        # TODO: Add transaction pool
        transaction = Transaction.objects.\
            filter(status="Pending").order_by('timestamp').last()
        print(f"INFO: New Proforma {t_s(transaction.timestamp)}")

        if swapic.transaction_accepted(transaction):

            tx_payment = swapic.manager.extract_transaction(transaction.usertransaction.data)['_embedded']['records'][0]
            params = {
                'destination_asset': swapic.stellar.assets['sepic'],
                'send_amount': tx_payment['amount'],
                'dest_min': tx_payment['amount'],
                'send_code': 'XLM',
                'set_timeout': 60,
                'text_memo': transaction.usertransaction.data['memo'],
                }

            # Add to SwapicTransaction Model
            new_swapic_tx = swapic.create_swapic_tx(params)
            swapic.send_swapic_tx(transaction, new_swapic_tx)
            response_data = {'status': 'DONE'}

        else:
            # print(f"TX MEMO: {temp_tx['memo']} FAILED")
            response_data = {'status': 'FAILED'}

        # SUMMARY OF TRANSACTION (FAILED OR SUCCESS / DETAILS)
        return JsonResponse(response_data, safe=False)


def stellar_transaction_form(request):
    """Create new Transaction object, proforma is a User input data"""
    response_data = {}
    if request.method == 'POST':
        transaction = swapic.create_proforma(
            timestamp=datetime.now(),
            epic_amount=str(Decimal(request.POST.get('epic'))),
            xlm_amount=str(Decimal(request.POST.get('xlm'))),
            receive_address=request.POST.get('receive_address'),
            receive_method=request.POST.get('receive_method'))

        if transaction:
            response_data = {'memo': transaction.proforma['memo'],
                             'send_address': swapic.stellar.wallet['keys']['public']}

        return JsonResponse(response_data)


class XLM_EPICJsonView(generic.ListView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        buy = request.GET.get('buy')
        spend = request.GET.get('spend')
        currency = request.GET.get('currency')
        epic_to_xlm = 0
        xlm_to_epic = 0
        stellar = StellarNetworkManager()

        if spend:
            try:
                xlm_to_epic = stellar.xlm_sepic_send_path(amount=spend)
                xlm_to_epic = xlm_to_epic['_embedded']['records'][0]['destination_amount']
                print(xlm_to_epic)
            except (TypeError, KeyError) as err:
                print(err)

        if buy:
            try:
                epic_to_xlm = stellar.xlm_sepic_receive_path(amount=buy)
                epic_to_xlm = epic_to_xlm['_embedded']['records'][0]['source_amount']
                print(epic_to_xlm)
            except (TypeError, KeyError) as err:
                print(err)

        return JsonResponse({'value': {'xlm_to_epic': xlm_to_epic,
                                       'epic_to_xlm': epic_to_xlm},
                             'currency': currency})


def stellar_trader_handler(request):
    response_data = {}
    if request.method == 'POST':
        # db.update_data()
        try:
            spend = float(request.POST.get('spend'))
            buy = float(request.POST.get('buy'))
        except (TypeError, ValueError) as er:
            spend = None
            buy = None
            print(er)

        pair = 'xlm'
        side = 'buy'
        print(buy, spend, pair, side)

        if spend or buy:
            value = orderbook_check(
                quantity=buy, exchange='stellarx',
                pair=pair, side=side)

            response_data['average'] = round(value['average'], 2)
            response_data['total'] = round(value['total'], 2)
            response_data['new_price'] = round(value['new_price'], 2)
            response_data['impact'] = round(check_impact(value['start_price'], value['new_price']), 2)
            response_data['start_price'] = value['start_price']
            response_data['counter'] = 'USD'

            for x in ['average', 'total', 'new_price', 'start_price']:
                response_data[f"{x}_counter"] = round(response_data[x] * float(db.data['xlm_price']), 2)

            response_data['btc_price'] = db.data['btc_price']
            response_data['exchange'] = 'stellarx'.upper()
            response_data['pair'] = pair.upper()
            response_data['side'] = side.upper()

            return JsonResponse(response_data)
        else:
            return JsonResponse(response_data)
    else:
        form = StellarTraderForm()
        return render(request, 'swapic.html', {'form': form, 'segment': 'swapic'})
