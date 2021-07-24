from bokeh.models import ColumnDataSource, NumeralTickFormatter, LinearAxis, \
    DatetimeTickFormatter, HoverTool, SingleIntervalTicker
from app.templatetags.math import t_s, sort_by_date
from bokeh.models.ranges import Range1d
from bokeh.embed import components
from bokeh.plotting import figure
import pandas as pd
from math import pi
import numpy


def stellar_price(data):
    df = pd.DataFrame(data)
    x_start = [t_s(x) for x in df.time if sort_by_date(x, days=4)]
    df['time'] = [t_s(d) for d in df['time']]
    df['time'] = pd.to_datetime(df.time)
    df[['base_volume', 'price']] = df[['base_volume', 'price']]\
        .replace(',', '.', regex=True).astype(float)
    df['adj_v'] = df.base_volume / 2

    source = ColumnDataSource(df)
    DTF = DatetimeTickFormatter()
    DTF.hours = ["%H:%M"]
    DTF.days = ["%d/%m"]
    DTF.months = ["%d/%m/%Y"]
    DTF.years = ["%d/%m/%Y"]

    w100 = 1 * 60 * 60 * 1000  # half day in ms
    TOOLS = "pan,box_zoom,reset,save,xwheel_zoom"

    # FIGURE
    p = figure(x_axis_type="datetime", tools=TOOLS, plot_height=300,
               sizing_mode='stretch_both', active_scroll='xwheel_zoom')

    p.toolbar.active_drag = None
    p.background_fill_color = None
    p.border_fill_color = None
    p.outline_line_color = None
    p.yaxis.visible = False
    p.xgrid.visible = False
    p.ygrid.visible = False
    p.toolbar_location = None

    # X STUFF
    # try:
    p.x_range = Range1d(x_start[-1], x_start[0])
    # except IndexError:
    #     pass
    # p.x_range.flipped = True

    p.xaxis[0].formatter = DTF

    p.xaxis.major_label_orientation = pi / 4
    p.xaxis[0].major_label_text_color = "white"
    p.xaxis[0].major_tick_line_color = "white"
    p.xaxis[0].axis_line_color = "white"
    p.xaxis[0].axis_line_alpha = 0.5


    # Y STUFF
    p.add_layout(LinearAxis(), 'right')
    p.y_range = Range1d(float(min(df.price)) * 0.5,
                        float(max(df.price)) * 1.2)
    p.yaxis[1].formatter = NumeralTickFormatter(format="0.00")
    p.yaxis[1].ticker.desired_num_ticks = 5
    p.yaxis[1].major_label_text_color = "white"
    p.yaxis[1].axis_line_color = "white"
    p.yaxis[1].axis_line_alpha = 0.4
    p.yaxis[1].major_tick_line_color = "white"
    p.yaxis[1].minor_tick_line_color = "white"

    price = p.line('time', y='price', source=source, line_width=3, alpha=1,
                   color="white")

    p.rect(x='time', y='adj_v', width=w100, y_range_name="volume",
           source=source, alpha=0.7, height='base_volume', color='#B3FFFF')

    p.extra_y_ranges = {'volume': Range1d(-100, max(df.base_volume) * 4)}

    p.y_range = Range1d(float(min(df.price)) * 0.5,
                        float(max(df.price)) * 1.2)
    p.yaxis[1].ticker = SingleIntervalTicker(interval=0.5, num_minor_ticks=2)

    price_hover = HoverTool(renderers=[price],
                            tooltips=[
                                ("Date: ", "@time{%y-%m-%d}"),
                                ("Time: ", "@time{%H:%M}"),
                                ("Price: ", "@price{0.000f}"),
                                ("", ""),
                                ("Volume: ", "@base_volume{0} EPIC"),
                                ],
                            formatters={"@time": "datetime"},
                            mode='vline')
    p.add_tools(price_hover)

    script, chart = components(p)
    return [script, chart]