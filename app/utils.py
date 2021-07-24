import datetime

from app.templatetags.math import t_s
from core.db import db
import ciso8601
import time


def total_volumes():
    vitex = float(db.vitex['ticker']['quantity'])
    stellar = float(db.stellar['sepic_xlm']['vol_24h'])
    pancake = float(db.pancake['volume_24']['total'])
    return vitex + stellar + pancake


def liquidity(chain):
    if chain == "stellar":
        stellar = db.orderbook['stellarx']['xlm']
        s_bids = sum(x[1] for x in stellar['bids'])
        s_asks = sum(x[1] for x in stellar['asks'])
        stellar_l = s_bids + s_asks
        return stellar_l * db.epic_vs_usd

    elif chain == 'vitex':
        vitex = db.orderbook['vitex']['btc']
        v_bids = sum(float(x[1]) for x in vitex['bids'])
        v_asks = sum(float(x[1]) for x in vitex['asks'])
        vitex_l = v_bids + v_asks
        return vitex_l * db.epic_vs_usd


def nearest(li, pivot):
    return min([ts for ts in li if ts <= pivot], key=lambda x: abs(x - pivot), default=None)


def last_24h():
    now = datetime.datetime.now()
    day_ago = datetime.timedelta(hours=24)
    return now - day_ago


def change(data, chain, current_price):
    now = datetime.datetime.now()
    day_ago = datetime.timedelta(hours=24)
    day_ago = int(datetime.datetime.timestamp(now - day_ago))
    value = ''
    old_price = 0
    color = 'success'
    arrow = '<i class="fas fa-arrow-up"></i>'

    if chain == 'vitex':
        d = {'time': data['t'],
             'price': data['c']}

    elif chain == "stellar":
        d = {'time': [int(x['time']) for x in data],
             'price': [float(x['price']) for x in data]}

        # for i, x in enumerate(d['time']):
        #     print(t_s(x))
        #     print(d['price'][i])

    else:
        d = {'time': data['time'],
             'price': data['price']}

    if chain == "stellar":
        temp = []
        try:
            for i, ts in enumerate(d['time']):
                if now.day - 1 == t_s(ts).day:
                    old_price = d['price'][i]
                    temp.append((t_s(ts), old_price))
            old_price = temp[-1][1]

        except IndexError as er:
            print(er)
            for i, ts in enumerate(d['time']):
                if (ts + 86_400) <= time.time():
                    old_price = d['price'][i]
                    break
                else:
                    old_price = d['price'][1]
                    # print(t_s(ts), old_price)

    else:
        for i, ts in enumerate(d['time']):
            if (ts + 86_400) >= time.time():
                old_price = d['price'][i]
                break

    if old_price != 0:
        diff = current_price - old_price
        if diff < 0:
            color = 'danger'
            arrow = '<i class="fas fa-arrow-down"></i>'

        value = diff / old_price * 100

        if 0 <= value < 0.01:
            color = 'dark'
            arrow = ''

    return {'color': color, 'arrow': arrow, 'value': value}

"""

print(t_s(day_ago))
    ts = nearest(d['time'], day_ago)
    # price = d['price'][index]
    print(f"Now: {base_price}, "
          f"24h: {price}, time: {t_s(ts)}")

for i, ts in enumerate(d['time']):
    if chain == "stellar":
        temp = []
        if now.day - 1 == t_s(ts).day:
            price = d['price'][i]
            # print(price)
            # print(t_s(ts))
            # print(base_price)
            temp.append((t_s(ts), price))
        print(temp)
    else:
        if (ts + 86_400) >= time.time():
            price = d['price'][i]
            break
"""