from pytz import NonExistentTimeError, AmbiguousTimeError
from decimal import InvalidOperation, Decimal
from django.utils.timezone import make_aware
from django import template
import ciso8601
import datetime
import time
import pytz

register = template.Library()


def get_ts(date):
    """ Convert datetime object to timestamp in milliseconds """
    if not isinstance(date, str):
        date = str(date).split(" ")[0]
    else:
        date = date
    return int(time.mktime(time.strptime(date, "%Y-%m-%d"))) * 1000


def last_24h():
    now = datetime.datetime.now()
    day_ago = datetime.timedelta(hours=24)
    return now - day_ago


def str_to_ts(ts):
    return int(time.mktime(ciso8601.parse_datetime(ts).timetuple()))


def sort_by_date(time, days=1):
    now = datetime.datetime.now(datetime.timezone.utc)
    difference = now - t_s(time)

    if difference.days < days:
        return True
    else:
        return False


def t_s(timestamp):
    """ Convert different timestamps to datetime object"""
    try:
        if len(str(timestamp)) == 13:
            time = datetime.datetime.fromtimestamp(int(timestamp) / 1000)
        elif len(str(timestamp)) == 10:
            time = datetime.datetime.fromtimestamp(int(timestamp))
        elif len(str(timestamp)) == 16:
            time = datetime.datetime.fromtimestamp(int(timestamp / 1000000))
        elif len(str(timestamp)) == 12:
            time = datetime.datetime.fromtimestamp(int(timestamp.split('.')[0]))

        else:
            # print(f"Problems with timestamp: {timestamp}, len: {len(str(timestamp))}")
            pass
        try:
            return make_aware(time)

        except (NonExistentTimeError, AmbiguousTimeError):
            timezone = pytz.timezone('Europe/London')
            time = timezone.localize(time, is_dst=False)
            return time

    except UnboundLocalError as er:
        return timestamp


def d(value, places=8):
    try:
        return round(Decimal(value), places)
    except (InvalidOperation, ValueError):
        if value == '' or ' ' or []:
            print(f'Empty string')
            return Decimal(0)
        else:
            print(f'String should have numbers only')
            pass


@register.filter(name='color')
def color(value):
    if float(value) > 0:
        return 'success'
    else:
        return 'danger'


@register.filter(name='multi')
def multi(value, num):
    return d(value) * d(num)


@register.filter(name='divide')
def divide(value, num):
    try:
        return d(value) / d(num)
    except:
        return 'N/A'


@register.filter(name='sub')
def subtract(value, arg):
    return value - arg


@register.filter()
def add(value, num):
    return d(value) + d(num)


@register.filter()
def satoshi(value):
    return d(value) * 100000000


@register.filter()
def get_percent(value, num):
    """
    :param value:
    :param num:
    :return: rounded percentage value of num
    """
    return d(d(value) / d(num) * 100, 2)


@register.filter(name='colour')
def percentage_color(value):
    if value < 20:
        return f"progress-bar-danger"
    elif 20 <= value <= 50:
        return f"progress-bar-warning"
    else:
        return f"progress-bar-success"

