import pandas as pd

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import PreText, Select
from bokeh.plotting import figure


DEFAULT_TICKERS = ['dining_room', 'kitchen', 'bathroom', 'stairs', 'bedroom', 'hall', 'living_room']

def nix(val, lst):
    return [x for x in lst if x != val]

def get_data(t1, t2, sensor):
	df = pd.read_csv("https://s3-eu-west-1.amazonaws.com/applied-data-science-uob-2018/data.csv")
	df = df.copy()
	data = pd.DataFrame(columns=['date', 't1', 't2'])
	data['date'] = df[df['room'] == t1]['time'].values
	data['t1'] = df[df['room'] == t1][sensor].values
	data['t2'] = df[df['room'] == t2][sensor].values
	return data

# set up widgets

stats = PreText(text='', width=500)
ticker1 = Select(value='dining_room', options=nix('living_room', DEFAULT_TICKERS))
ticker2 = Select(value='living_room', options=nix('dining_room', DEFAULT_TICKERS))
sensor = Select(value='temperature', options=['temperature', 'humidity'])

# set up plots

source = ColumnDataSource(data=dict(date=[], t1=[], t2=[]))
source_static = ColumnDataSource(data=dict(date=[], t1=[], t2=[]))
tools = 'pan,wheel_zoom,xbox_select,reset'

corr = figure(plot_width=350, plot_height=350,
              tools='pan,wheel_zoom,box_select,reset')
corr.circle('t1', 't2', size=2, source=source,
            selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)

ts1 = figure(plot_width=900, plot_height=200, tools=tools, active_drag="xbox_select")
ts1.line('date', 't1', source=source_static)
ts1.circle('date', 't1', size=1, source=source, color=None, selection_color="orange")

ts2 = figure(plot_width=900, plot_height=200, tools=tools, active_drag="xbox_select")
ts2.x_range = ts1.x_range
ts2.line('date', 't2', source=source_static)
ts2.circle('date', 't2', size=1, source=source, color=None, selection_color="orange")

# set up callbacks

def ticker1_change(attrname, old, new):
    ticker2.options = nix(new, DEFAULT_TICKERS)
    update()

def ticker2_change(attrname, old, new):
    ticker1.options = nix(new, DEFAULT_TICKERS)
    update()
	
def sensor_change(attrname, old, new):
	update()

def update(selected=None):
    t1, t2, s = ticker1.value, ticker2.value, sensor.value

    data = get_data(t1, t2, s)
    source.data = source.from_df(data[['date', 't1', 't2']])
    source_static.data = source.data

    update_stats(data, t1, t2)

    corr.title.text = '%s vs. %s' % (t1, t2)
    ts1.title.text, ts2.title.text = t1, t2

def update_stats(data, t1, t2):
    stats.text = str(data[['t1', 't2']].rename(columns={'t1': t1, 't2': t2}).describe())

ticker1.on_change('value', ticker1_change)
ticker2.on_change('value', ticker2_change)
sensor.on_change('value', sensor_change)

def selection_change(attrname, old, new):
    t1, t2, s = ticker1.value, ticker2.value, sensor.value
    data = get_data(t1, t2, s)
    selected = source.selected.indices
    if selected:
        data = data.iloc[selected, :]
    update_stats(data, t1, t2)

source.on_change('selected', selection_change)

# set up layout
widgets = column(ticker1, ticker2, sensor, stats)
main_row = row(corr, widgets)
series = column(ts1, ts2)
layout = column(main_row, series)

# initialize
update()

curdoc().add_root(layout)
curdoc().title = "Applied Data Science - SH2 Data Visualisation 2"
