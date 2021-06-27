
# global options
storage_heavy = False # turn on if the data csv file is very large (probably never? ;P)

# imports
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
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

default_quantities = ['kg', 'Body fat']

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

date_zero = pd.to_datetime('2000-01-01 00:00:00.0000')
df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
dt_min = (df['DateTime'].min() - date_zero).total_seconds()
dt_max = (df['DateTime'].max() - date_zero).total_seconds()
dt_span = dt_max - dt_min

def dateTime_to_dateTimeInt (dt):
    if not isinstance(dt, np.datetime64):
        dt = pd.to_datetime(dt)
    res = (dt - date_zero).total_seconds()
    res = (res - dt_min) * 100.0 / dt_span
    return res
def dateTimeInt_to_dateTime (dt):
    return date_zero + (dt_min + dt_span * dt/100.) * pd.to_timedelta('1s')

df['DateTime-int'] = df['DateTime'].apply(dateTime_to_dateTimeInt)

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
    fig['layout']['xaxis']['range'] = [dateTimeInt_to_dateTime(ti) for ti in time_range]
    fig['layout']['xaxis']['autorange'] = False
    # update the yrange given the xrange visible
    # TODO (need to do this for each axis separately)
    return fig

fig = redraw_figure(default_quantities)

# SET UP THE APP ------------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Dropdown(
        id='quantity-dropdown',
        options=[{'label': settings[quantity]['label'], 'value': quantity} for quantity in settings.keys()],
        value=default_quantities,
        multi=True
    ),
    dcc.Graph(id='graph', figure=fig),
    dcc.RangeSlider(
        id='time-range-slider',
        min=0,
        max=100,
        value=[0,100],
        marks={int(ti):{'label':dateTimeInt_to_dateTime(ti).strftime("%Y-%m-%d"), 'style':{'color':'black'}} for ti in np.linspace(0,100,6)},
        updatemode='drag'
    )
])

# app callbacks

# TODO: prevent the two callbacks from calling each other in a loop

@app.callback(
    Output('graph', 'figure'),
    Input('quantity-dropdown', 'value'),
    Input('time-range-slider', 'drag_value'),
    State('graph', 'figure')
)
def update_figure (quantities, time_range, fig):
    print('Updating the figure.. ', end='')
    ctx = dash.callback_context
    triggers = [x['prop_id'].split('.')[0] for x in ctx.triggered]
    # prevent callback loops
    if 'quantity-dropdown' in triggers:
        fig = redraw_figure(quantities)
    if 'time-range-slider' in triggers:
        print(fig['layout'].keys())
        fig = update_figure_timerange(time_range, fig)
    print('done.')
    return fig

@app.callback(
    Output('time-range-slider', 'value'),
    Input('graph', 'relayoutData')
)
def update_time_range_slider (relayoutData):
    print('Updating the time slider..', end='')
    # initial and reset
    if relayoutData == None or 'autosize' in relayoutData.keys() or 'xaxis.autorange' in relayoutData.keys():
        return [0,100]
    # modifying the graph through graph tools
    new_timerange = [dateTime_to_dateTimeInt(t) for t in [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]]
    print('done.')
    return new_timerange

# RUN THE SERVER ------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)