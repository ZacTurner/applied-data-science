
# coding: utf-8

# In[9]:


import pandas as pd
import numpy as np
from bokeh.io import curdoc,output_notebook
from bokeh.layouts import row, column,widgetbox
from bokeh.models import ColumnDataSource, LabelSet, Label
from bokeh.models.widgets import PreText, Select
from bokeh.plotting import figure,show

DEFAULT_TICKERS = ['15:15', '15:40', '16:20', '16:45']

def nix(val, lst):
    return [x for x in lst if x != val]

def get_data(t1):
    vl = pd.read_csv("/Users/chengchun/Desktop/vol.csv")
    vl = vl.copy()
    df = pd.read_csv("/Users/chengchun/Desktop/data.csv")
    df = df.copy()
    data = pd.DataFrame(columns=['vol','room' 'tmp', 'hum'])
    data['vol'] = vl['volume'].values
    data['room'] = vl['room'].values
    if t1 == '15:15':       #Living room and bedroom window open
        t1 = '75.0'
    elif t1 == '16:45':    # All window close
        t1 = '165.0'
    elif t1 == '15:40':    #Kitchen window open
        t1 = '100.0'
    elif t1 == '16:20':  # bathroom window open
        t1 = '140.0'
    t1 = float(t1)

    data['tmp'] = df[df['time'] == t1]['temperature'].values
    data['hum'] = df[df['time'] == t1]['humidity'].values
    
    data.sort_values(['vol'],inplace=True)
   
    return data

# set up widgets

stats = PreText(text='', width=500)
ticker1 = Select(value='15:15', options=nix('13:00', DEFAULT_TICKERS))
ticker2 = Select(value='15:15', options=nix('13:00', DEFAULT_TICKERS))

# set up plots

source = ColumnDataSource(data=dict(vol=[], tmp=[], hum=[]))
source_static = ColumnDataSource(data=dict(vol=[], tmp=[], hum=[]))
tools = 'pan,wheel_zoom,xbox_select,reset'
corr = figure(plot_width=600, plot_height=600,
              tools='pan,wheel_zoom,box_select,reset')
corr.scatter(x='tmp', y='hum', size=8, source=source)
labels = LabelSet(x='tmp', y='hum', text='room', level='glyph',
              x_offset=-20, y_offset=0, source=source, render_mode='canvas')
citation = Label(x=100, y=100, x_units='screen', y_units='screen',
                 render_mode='css',
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)

ts1 = figure(plot_width=900, plot_height=350, tools=tools, active_drag="xbox_select")
ts1.scatter(x='vol', y='tmp', size=10, source=source)
ts1.xaxis[0].axis_label = 'Volume (m3)'
ts1.yaxis[0].axis_label = 'Temperature (C)'
ts1.xaxis[0].axis_label_text_font_size = "40pt"
ts1.yaxis[0].axis_label_text_font_size = "40pt"
labels1 = LabelSet(x='vol', y='tmp', text='room', level='glyph',
              x_offset=-30, y_offset=0, source=source, render_mode='canvas')

citation1 = Label(x=100, y=100, x_units='screen', y_units='screen',
                 render_mode='css',
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)


ts2 = figure(plot_width=900, plot_height=350, tools=tools, active_drag="xbox_select")
ts2.x_range = ts1.x_range
ts2.scatter(x='vol', y='hum', size=10, source=source)

labels2 = LabelSet(x='vol', y='hum', text='room', level='glyph',
              x_offset=-30, y_offset=0, source=source, render_mode='canvas')
citation2 = Label(x=100, y=100, x_units='screen', y_units='screen',
                 render_mode='css',
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)


# set up callbacks

def ticker1_change(attrname, old, new):
    ticker2.options = nix(new, DEFAULT_TICKERS)
    update()
    

def update(selected=None):
    t1 = ticker1.value
    data = get_data(t1)
    source.data = source.from_df(data[['vol', 'room','tmp', 'hum']])
    source_static.data = source.data
    corr.title.text = 'Temperature  vs. humidity in all roms at time = %s' % (t1)
    ts1.title.text = 'Temperature  vs. rooms volume at time = %s' % (t1)
    ts2.title.text = 'Humidity  vs. rooms volume at time = %s' % (t1)


ticker1.on_change('value', ticker1_change)


def selection_change(attrname, old, new):
    t1 = ticker1.value
    data = get_data(t1)
    selected = source.selected.indices
    if selected:
        data = data.iloc[selected, :]

source.on_change('selected', selection_change)

# set up layout
widgets = column(ticker1, stats)
main_row = row(corr, widgets)
series = column(ts1, ts2)
layout = column(main_row, series)

# initialize
update()
corr.add_layout(labels)
corr.add_layout(citation)
ts1.add_layout(labels1)
ts1.add_layout(citation1)
ts2.add_layout(labels2)
ts2.add_layout(citation2)
curdoc().add_root(layout)
curdoc().title = "Applied Data Science - SH2 Data Visualisation 2"


