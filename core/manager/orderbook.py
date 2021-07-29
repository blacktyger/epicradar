from app.models import db


def check_impact(price_before, price_after):
    impact = float(price_after / float(price_before) - 1) * 100
    if impact < 0:
        return impact * -1
    else:
        return impact


def orderbook_check(quantity, exchange, pair, side):
    filled = 0
    fill_array = []
    ordered = quantity

    if side == "ask" or side == "sell":
        data = db['orderbook'][exchange][pair]['asks']
    elif side == "bid" or side == "buy":
        data = db['orderbook'][exchange][pair]['bids']

    for entry in data:
        price = float(entry[0])
        amount = float(entry[1])

        if ordered != filled:
            required = ordered - filled

            if amount >= required:
                fill_array.append([price, required])
                filled += required
                print('Order done:', filled)
                break
            else:
                filled += amount
                fill_array.append([price, amount])
                print('Adding: ', amount, ' for ', price)
                print('order filled:', filled, ' out of ', ordered, ' ...')

    total_amount = 0
    total_sum = 0

    # print(fill_array)

    for ele in fill_array:
        total_sum += (ele[0] * ele[1])
        total_amount += ele[1]

    print('START PRICE: ', '{:.8f}'.format(fill_array[0][0]))
    print('AVG PRICE: ', '{:.8f}'.format(total_sum / total_amount))
    print('NEW PRICE: ', '{:.8f}'.format(fill_array[-1][0]))
    return {'average': total_sum / total_amount,
            'total': total_sum,
            'new_price': fill_array[-1][0],
            'start_price': fill_array[0][0]}