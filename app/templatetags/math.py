from django.template.defaultfilters import stringfilter
from pytz import NonExistentTimeError, AmbiguousTimeError
from decimal import InvalidOperation, Decimal
from django.utils.timezone import make_aware
from django import template
import ciso8601
import datetime
import time
import pytz

from core.db import db
from mining.models import Block

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
    try:
        if float(value) > 0:
            return 'success'
        else:
            return 'danger'
    except:
        return 'warning'


@register.filter(name='multi')
def multi(value, num):
    try:
        return d(value) * d(num)
    except:
        return 0


@register.filter(name='divide')
def divide(value, num):
    try:
        return d(value) / d(num)
    except:
        return 'N/A'


@register.filter(name='sub')
def subtract(value, arg):
    try:
        return value - arg
    except:
        return 0


@register.filter()
def add(value, num):
    try:
        return d(value) + d(num)
    except:
        return 0


@register.filter()
def satoshi(value):
    try:
        return d(value) * 100000000
    except:
        return 0


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter()
def get_block(height):
    return db.get_block(height)


@register.filter
@stringfilter
def upto(value, delimiter=None):
    return value.split(delimiter)[0]
upto.is_safe = True


@register.filter()
def date_obj(timestamp):
    return datetime.datetime.utcfromtimestamp(int(timestamp))


@register.filter()
def pretty_url(value):
    return value.split('//')[1]


@register.filter()
def get_percent(value, num):
    """
    :param value:
    :param num:
    :return: rounded percentage value of num
    """
    try:
        return d(d(value) / d(num) * 100, 2)
    except:
        return 0


@register.filter(name='progress_colour')
def percentage_color(value):
    try:
        if value < 20:
            return f"bg-danger"
        elif 20 <= value <= 50:
            return f"bg-warning"
        else:
            return f"bg-success"
    except:
        return f"bg-warning"
