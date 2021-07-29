from app.templatetags.math import t_s
from decimal import Decimal
import datetime
import time


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
    old_price = 0

    if chain == 'vitex':
        d = {'time': data['t'],
             'price': data['c']}

    elif chain == "stellar":
        d = {'time': [int(x['time']) for x in data],
             'price': [float(x['price']) for x in data]}
        d['time'].reverse()
        d['price'].reverse()
    else:
        d = {'time': data['time'],
             'price': data['price']}

    if chain == "stellar":
        try:
            old_price = 0
            for t, p in zip(d['time'], d['price']):
                if t_s(t).day == now.day - 1 and t_s(t).month == now.month:
                    old_price = p
                    print((t_s(t), old_price))

        except IndexError as er:
            print(er)
            old_price = 0
    else:
        for i, ts in enumerate(d['time']):
            if (ts + 86_400) > time.time():
                if ts < day_ago:
                    old_price = 0
                    break
                old_price = d['price'][i]
                break

    if old_price != 0:
        old_price = Decimal(old_price)
        diff = current_price - old_price
        if diff < 0:
            color = 'danger'
            arrow = '<i class="fas fa-arrow-down"></i>'
            value = diff / old_price * 100

        elif diff > 0:
            color = 'success'
            arrow = '<i class="fas fa-arrow-up"></i>'
            value = diff / old_price * 100

        else:
            color = 'dark'
            arrow = ''
            value = 0
    else:
        color = 'dark'
        arrow = ''
        value = 0

    try:
        last_trade = datetime.datetime.fromtimestamp(d['time'][-1])
    except:
        last_trade = datetime.datetime.fromtimestamp(d['time'][-1]/1000)

    print(chain, last_trade)

    return {'color': color, 'arrow': arrow,
            'value': value, 'last_trade': last_trade}


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