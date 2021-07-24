import pandas as pd
from bokeh.embed import components
from bokeh.models import ColumnDataSource, FactorRange, NumeralTickFormatter, LinearAxis, DatetimeTickFormatter, \
    HoverTool, LabelSet, SingleIntervalTicker
from bokeh.plotting import figure
from bokeh.models.ranges import Range1d

from app.templatetags.math import t_s, sort_by_date


def vitex_mini_chart(data):
    data = {'time': data['t'][::10] + [data['t'][-1]],
            'price': data['c'][::10] + [data['c'][-1]]}
    temp = []
    for i, item in enumerate(data['time']):
        temp.append({'time': t_s(item), 'price': data['price'][i]})
    data = [x for x in temp if sort_by_date(x['time'], days=7)]
    # print(data)

    df = pd.DataFrame(data)
    # df['time'] = pd.to_datetime(df.time)

    source = ColumnDataSource(df)

    DTF = DatetimeTickFormatter()
    DTF.hours = ["%H:%M"]
    DTF.days = ["%d/%m/'%y"]
    DTF.months = ["%d/%m/%Y"]
    DTF.years = ["%d/%m/%Y"]

    p = figure(x_axis_type="datetime", plot_width=150,
               plot_height=45, toolbar_location=None)

    p.line('time', y='price', source=source, line_width=1.5, alpha=1, color="#AD5AF3")
    p.varea(x='time', y1=0, y2='price', alpha=0.45, source=source, fill_color='#AD5AF3')

    hover = HoverTool(tooltips=[
        ("Date: ", "@time{%y-%m-%d}"),
        ("Time: ", "@time{%H:%M}"),
        ("Price(BTC): ", "@price{0.0000000f}")],
        formatters={"@time": "datetime",
                    'price': 'printf'},
        mode='vline')

    p.add_tools(hover)

    p.xaxis.major_label_orientation = 3.14 / 4
    p.yaxis.visible = False
    # x stuff
    p.xaxis.visible = False
    p.xgrid.visible = False
    p.xaxis.major_label_text_color = "grey"
    p.xaxis[0].formatter = DTF

    # Y - PRICE
    p.y_range = Range1d(min(df.price) * 0.7, max(df.price) * 1.1)
    p.ygrid.visible = False

    p.background_fill_color = None
    p.border_fill_color = None
    p.outline_line_color = None
    p.toolbar.autohide = True

    script, chart = components(p)
    return [script, chart]


def stellar_mini_chart(data):
    filtered_data = [x for x in data if sort_by_date(x['time'], days=7)]
    if len(filtered_data) < 3:
        filtered_data = [x for x in data if sort_by_date(x['time'], days=30)]

    df = pd.DataFrame(filtered_data)
    df['time'] = [t_s(d) for d in df['time']]
    df['time'] = pd.to_datetime(df.time)
    df[['base_volume', 'price']] = df[['base_volume', 'price']] \
        .replace(',', '.', regex=True).astype(float)

    source = ColumnDataSource(df)

    DTF = DatetimeTickFormatter()
    DTF.hours = ["%H:%M"]
    DTF.days = ["%d/%m/'%y"]
    DTF.months = ["%d/%m/%Y"]
    DTF.years = ["%d/%m/%Y"]

    p = figure(x_axis_type="datetime", plot_width=150,
               plot_height=45, toolbar_location=None)

    p.line('time', y='price', source=source, line_width=1.5, alpha=1, color="#008AD6")
    p.varea(x='time', y1=0, y2='price', alpha=0.45, source=source, fill_color='#008AD6')

    hover = HoverTool(tooltips=[
        ("Date: ", "@time{%y-%m-%d}"),
        ("Time: ", "@time{%H:%M}"),
        ("Price(XLM): ", "@price{0.00f}")],
        formatters={"@time": "datetime",
                    'price': 'printf'},
        mode='vline')

    p.add_tools(hover)

    p.xaxis.major_label_orientation = 3.14 / 4
    p.yaxis.visible = False
    # x stuff
    p.xaxis.visible = False
    p.xgrid.visible = False
    p.xaxis.major_label_text_color = "grey"
    p.xaxis[0].formatter = DTF

    # Y - PRICE
    p.y_range = Range1d(min(df.price) * 0.7, max(df.price) * 1.1)
    p.ygrid.visible = False

    p.background_fill_color = None
    p.border_fill_color = None
    p.outline_line_color = None
    p.toolbar.autohide = True

    script, chart = components(p)
    return [script, chart]


def pancake_mini_chart(data):
    temp = []
    for i, item in enumerate(data['time']):
        temp.append({'time': t_s(item), 'price': data['price'][i]})

    data = [x for x in temp if sort_by_date(x['time'], days=7)]

    if not data:
        data = [x for x in temp if sort_by_date(x['time'], days=30)]

    df = pd.DataFrame(data)
    source = ColumnDataSource(df)

    DTF = DatetimeTickFormatter()
    DTF.hours = ["%H:%M"]
    DTF.days = ["%d/%m/'%y"]
    DTF.months = ["%d/%m/%Y"]
    DTF.years = ["%d/%m/%Y"]

    p = figure(x_axis_type="datetime", plot_width=150,
               plot_height=45, toolbar_location=None)

    p.line('time', y='price', source=source, line_width=1.5, alpha=1, color="#D69B25")
    p.varea(x='time', y1=0, y2='price', alpha=0.45, source=source, fill_color='#D69B25')

    hover = HoverTool(tooltips=[
        ("Date: ", "@time{%y-%m-%d}"),
        ("Time: ", "@time{%H:%M}"),
        ("Price(BNB): ", "@price{0.0000f}")],
        formatters={"@time": "datetime",
                    'price': 'printf'},
        mode='vline')

    p.add_tools(hover)

    p.xaxis.major_label_orientation = 3.14 / 4
    p.yaxis.visible = False
    # x stuff
    p.xaxis.visible = False
    p.xgrid.visible = False
    p.xaxis.major_label_text_color = "grey"
    p.xaxis[0].formatter = DTF

    # Y - PRICE
    p.y_range = Range1d(min(df.price) * 0.7, max(df.price) * 1.1)
    p.ygrid.visible = False

    p.background_fill_color = None
    p.border_fill_color = None
    p.outline_line_color = None
    p.toolbar.autohide = True

    script, chart = components(p)
    return [script, chart]
