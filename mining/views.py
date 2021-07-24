from core.db import db
from .mining_calculator import Calculator
from .forms import MiningCalculatorForm
from django.http import JsonResponse
from django.views import generic
from .validator import Field
import datetime


def mining_ajax(request):
    if request.method == "POST":
        r = MinerCalculatorView()
        r.request = request.POST
        r.get_queryset()
        response_data = r.result
        return JsonResponse(response_data)


class MiningView(generic.TemplateView):
    template_name = 'mining.html'
    periods = [('hour', 1 / 24), ('day', 1), ('week', 7)]
    app = Calculator(algo='randomx', rig_hashrate=1, currency='USD')

    def get_context_data(self, **kwargs):
        context = super(MiningView, self).get_context_data(**kwargs)
        context['mining_c'] = {
            'currency_list': self.app.currency_list,
            'algo_list': self.app.algos,
            }
        context['currency_list'] = [v['symbol'] for k, v in db.currency.items()]
        context['algo_list'] = self.app.algos
        context['calc_form'] = MiningCalculatorForm()
        context['network'] = db.network_data()
        context['periods'] = self.periods
        context['segment'] = 'mining'

        return context


class MinerCalculatorView(generic.ListView):
    template_name = 'mining_calculator.html'
    periods = [('hour', 1 / 24), ('day', 1), ('week', 7)]
    fields = {}
    fields_list = [('rig_hashrate', 'number'), ('algo', 'string'),
                   ('currency', 'string'), ('power_consumption', 'number'),
                   ('electricity_cost', 'number'), ('pool_fee', 'number'),
                   ('period', 'number')]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = Calculator(algo='randomx', rig_hashrate=1, currency='USD')
        self.result = {}

    def init_fields(self):
        for field in self.fields_list:
            self.fields[field[0]] = Field(name=field[0], request=self.request,
                                          type=field[1], p=False)

    def get(self, request, *args, **kwargs):
        self.get_queryset()
        # print(self.result)
        return JsonResponse(self.result)

    def get_queryset(self):
        self.init_fields()
        data = {k: v.value for k, v in self.fields.items()}
        periods = self.periods

        if self.fields['period'].is_valid():
            periods.append(('user', data['period']))
        else:
            data['period'] = 1

        if not self.fields['algo'].is_valid():
            self.fields['algo'].init_value = 'randomx'
            data['algo'] = 'randomx'

        if not self.fields['currency'].is_valid():
            self.fields['currency'].init_value = 'USD'
            data['currency'] = 'USD'

        c = Calculator(**data)

        if self.fields['rig_hashrate'].is_valid() and self.fields['algo'].is_valid():
            self.result['date'] = datetime.datetime.now()
            self.result['rig_cost'] = c.cost
            self.result['user_input'] = data
            self.result['rig_reward'] = c.mining_reward
            self.result['rig_income'] = c.income
            self.result['rig_profit'] = c.profit
            self.result['solo_block'] = c.solo_block()

        # print(self.result)

    def get_context_data(self, **kwargs):
        context = super(MinerCalculatorView, self).get_context_data(**kwargs)
        context['init'] = {k: v.init_value for k, v in self.fields.items()}
        context['result'] = self.result
        context['periods'] = self.periods
        context['currency_list'] = self.app.currency_list
        context['algo_list'] = self.app.algos
        context['form'] = MiningCalculatorForm()
        # context['example_gear'] = {
        #     'randomx': {
        #         'ryzen3900x': Calculator(rig_hashrate=13000, algo='randomx').income['value'],
        #         'epyc7742': Calculator(rig_hashrate=44000, algo='randomx').income['value']
        #         }
        #     }
        return context


class JsonMinerCalculatorView(MinerCalculatorView):
    def get(self, request, *args, **kwargs):
        self.get_queryset()
        # print(self.result)
        return JsonResponse(self.result)
