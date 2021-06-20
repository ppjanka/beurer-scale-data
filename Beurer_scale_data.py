
# global options
storage_heavy = False # turn on if the data csv file is very large (probably never? ;P)

# imports
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from matplotlib import colors

if not storage_heavy:
    import sys
    if sys.version_info[0] < 3: 
        from StringIO import StringIO
    else:
        from io import StringIO

# LOAD IN THE DATA -----------------------------------------------------------

csv_filename = 'HealthManagerApp_DataExport.csv'
in_read = False
# if there is a lot of data, find the line numbers to read first and then use lines_to_read to read the file directly into pandas df
if storage_heavy:
    line_no = 0
    lines_to_read = []
    with open(csv_filename, 'r') as f:
        for line in f:
            if not in_read and line == 'Weight\n':
                lines_to_read.append([line_no+1,None])
                in_read = True
            elif in_read and line == '\n':
                lines_to_read[-1][1] = line_no-1
                in_read = False
            line_no += 1
    dfs = []
    for chunk in lines_to_read:
        dfs.append(pd.read_csv(csv_filename, sep=';', 
            header=chunk[0], nrows=(chunk[1]-chunk[0]+1)))
    df = pd.concat(dfs, ignore_index=True)
    del dfs
# otherwise figure out where the weight data is stored in the data dump, pack it into a string
else: # not storage heavy (single file pass, but saves as string first)
    csv_data = []
    with open(csv_filename, 'r') as f:
        for line in f:
            if not in_read and line == 'Weight\n':
                in_read = True
                csv_data.append('')
            elif in_read:
                if line == '\n':
                    in_read = False
                else:
                    csv_data[-1] += line
    dfs = []
    for chunk in csv_data:
        dfs.append(pd.read_csv(StringIO(chunk), sep=';', header=0))
    df = pd.concat(dfs, ignore_index=True)
    del dfs

df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
df['DateTime-int'] = pd.to_timedelta(df['DateTime']).dt.total_seconds()
dt_min = df['DateTime-int'].min()
dt_max = df['DateTime-int'].max()

def dateTimeInt_to_dateTime (dt):
    return pd.to_datetime(dt * pd.to_timedelta('1s'))

# DRAW THE FIGURE -----------------------------------------------------------

settings = {
    'kg': {
        'label': 'Total Mass [kg]',
        'color': 'black',
        'axis_side': 'left'
    },
    'BMI': {
        'label': 'BMI',
        'color': 'orange',
        'axis_side': 'right'
    },
    'Body fat': {
        'label': 'Body Fat %',
        'color': 'green',
        'axis_side': 'right'
    },
    'Water': {
        'label': 'Water Mass [kg]',
        'color': 'blue',
        'axis_side': 'left'
    },
    'Muscles': {
        'label': 'Muscle Mass [kg]',
        'color': 'red',
        'axis_side': 'left'
    },
    'Bones': {
        'label': 'Bone Mass [kg]',
        'color': 'grey',
        'axis_side': 'right'
    }
}

def redraw_figure (quantities_to_plot):

    fig = go.Figure()

    axis_no = 1
    padding = {'left':0., 'right':0.}
    padding_step = 0.15
    for quantity in quantities_to_plot:
        fig.add_trace(go.Scatter(
            x=df['DateTime'], y=df[quantity],
            mode='markers',
            hovertemplate='%{hovertext:.1f}',
            hovertext=df[quantity],
            name=settings[quantity]['label'],
            marker=dict(
                color=settings[quantity]['color']
            ),
            yaxis=(('y%i' % axis_no) if axis_no > 1 else 'y')
        ))
        # produce a semi-transparent quantity color for the grid
        diluted_color = list(colors.to_rgba(settings[quantity]['color']))
        diluted_color[3] = 0.25 # alpha
        diluted_color = 'rgba(%.2f,%.2f,%.2f,%.2f)' % tuple(diluted_color)
        # update the layout
        layout_kwargs = {
            (('yaxis%i' % axis_no) if axis_no > 1 else 'yaxis'): dict(
                title=settings[quantity]['label'],
                titlefont=dict(color=settings[quantity]['color']),
                tickfont=dict(color=settings[quantity]['color']),
                side=settings[quantity]['axis_side'],
                overlaying=('y' if axis_no > 1 else None),
                position=(padding[settings[quantity]['axis_side']] if settings[quantity]['axis_side'] == 'left' else 1.0 - padding[settings[quantity]['axis_side']]),
                showgrid=True, gridcolor=diluted_color, gridwidth=2,
                showspikes=True, spikemode='across', spikesnap='cursor'
            )
        }
        fig.update_layout(**layout_kwargs)
        padding[settings[quantity]['axis_side']] += padding_step
        axis_no += 1

    fig.update_layout(
        xaxis=dict(
            domain=[max(padding['left'] - padding_step, 0.), min(1.0, 1.0 + padding_step - padding['right'])]
        ),
        hovermode='x unified'
    )

    return fig

def update_figure_timerange (time_range, fig):
    # slightly expand time_range for better viewing
    padding = 0.05 * (time_range[1] - time_range[0])
    time_range = [time_range[0] - padding, time_range[1] + padding]
    # apply the xrange change
    fig['layout']['xaxis']['range'] = [dateTimeInt_to_dateTime(i*(dt_max-dt_min)/100.+dt_min).strftime("%Y-%m-%d %H:%M:%S") for i in time_range]
    fig['layout']['xaxis']['autorange'] = False
    # update the yrange given the xrange visible
    # TODO (need to do this for each axis separately)
    return fig

fig = redraw_figure(['kg', 'Muscles', 'Bones'])

# SET UP THE APP ------------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Dropdown(
        id='quantity-dropdown',
        options=[{'label': settings[quantity]['label'], 'value': quantity} for quantity in settings.keys()],
        value=['kg', 'Body fat'],
        multi=True
    ),
    dcc.Graph(id='graph', figure=fig),
    dcc.RangeSlider(
        id='time-range-slider',
        min=0,
        max=100,
        value=[0,100],
        marks={int(i):{'label':dateTimeInt_to_dateTime(i*(dt_max-dt_min)/100.+dt_min).strftime("%Y-%m-%d"), 'style':{'color':'black'}} for i in np.linspace(0,100,6)}
    )
])

# app callbacks

@app.callback(
    Output('graph', 'figure'),
    Input('quantity-dropdown', 'value'),
    Input('time-range-slider', 'value'),
    State('graph', 'figure')
)
def update_figure (quantities, time_range, fig):
    ctx = dash.callback_context
    triggers = [x['prop_id'].split('.')[0] for x in ctx.triggered]
    if not ctx.triggered or 'quantity-dropdown' in triggers:
        fig = redraw_figure(quantities)
    if not ctx.triggered or 'time-range-slider' in triggers:
        fig = update_figure_timerange(time_range, fig)
    return fig

# RUN THE SERVER ------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)