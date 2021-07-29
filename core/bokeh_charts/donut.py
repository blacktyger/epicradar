from bokeh import Donut, show
import pandas as pd
data = pd.Series([0.15,0.4,0.7,1.0], index = list('abcd'))
pie_chart = Donut(data)