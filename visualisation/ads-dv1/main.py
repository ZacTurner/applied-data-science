import pandas as pd

from bokeh.layouts import row, widgetbox
from bokeh.models import Select
from bokeh.models.widgets import RangeSlider
from bokeh.palettes import Spectral5
from bokeh.plotting import curdoc, figure

df1 = pd.read_csv("https://s3-eu-west-1.amazonaws.com/applied-data-science-uob-2018/data.csv")
df1 = df1.drop(['window_open', 'window_open_time'], axis=1)
df2 = pd.read_csv("https://s3-eu-west-1.amazonaws.com/applied-data-science-uob-2018/external_data.csv")
df = pd.concat([df1, df2], axis=1)

SIZES = list(range(6, 22, 3))
COLORS = Spectral5

rooms = ['dining_room', 'kitchen', 'bathroom', 'stairs', 'bedroom', 'hall', 'living_room']
columns = sorted(df.columns)
discrete = [x for x in columns if df[x].dtype == object]
continuous = [x for x in columns if x not in discrete]
quantileable = [x for x in continuous if len(df[x].unique()) > 20]

def create_figure():
    xs = df[df['room'] == room.value][x.value].iloc[int(time_range.value[0]*2):int(time_range.value[1]*2)+1].values
    ys = df[df['room'] == room.value][y.value].iloc[int(time_range.value[0]*2):int(time_range.value[1]*2)+1].values
    x_title = x.value.title()
    y_title = y.value.title()

    kw = dict()
    if x.value in discrete:
        kw['x_range'] = sorted(set(xs))
    if y.value in discrete:
        kw['y_range'] = sorted(set(ys))
    kw['title'] = "%s vs %s" % (x_title, y_title)

    p = figure(plot_height=600, plot_width=800, tools='pan,box_zoom,reset', **kw)
    p.xaxis.axis_label = x_title
    p.yaxis.axis_label = y_title

    if x.value in discrete:
        p.xaxis.major_label_orientation = pd.np.pi / 4

    sz = 9
    if size.value != 'None':
        groups = pd.qcut(df[size.value].values, len(SIZES))
        sz = [SIZES[xx] for xx in groups.codes]

    c = "#31AADE"
    if color.value != 'None':
        groups = pd.qcut(df[color.value].values, len(COLORS))
        c = [COLORS[xx] for xx in groups.codes]
    p.circle(x=xs, y=ys, color=c, size=sz, line_color="white", alpha=0.6, hover_color='white', hover_alpha=0.5)

    return p


def update(attr, old, new):
    layout.children[1] = create_figure()

room = Select(title='Room', value='dining_room', options=rooms)
room.on_change('value', update)

time_range = RangeSlider(start=0, end=240, value=(0,30), step=.5, title="Time range (mins)")
time_range.on_change('value', update)
	
x = Select(title='X-Axis', value='time', options=['time'] + continuous)
x.on_change('value', update)

y = Select(title='Y-Axis', value='temperature', options=['time'] + continuous)
y.on_change('value', update)

size = Select(title='Size', value='None', options=['None'] + quantileable)
size.on_change('value', update)

color = Select(title='Color', value='None', options=['None'] + quantileable)
color.on_change('value', update)

controls = widgetbox([room, time_range, x, y, color, size], width=220)
layout = row(controls, create_figure())

curdoc().add_root(layout)
curdoc().title = "Applied Data Science - SH2 Data Visualisation 1"
