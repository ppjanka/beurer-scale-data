
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

import os
if not storage_heavy:
    import sys
    if sys.version_info[0] < 3: 
        from StringIO import StringIO
    else:
        from io import StringIO

default_quantities = ['kg', 'Body fat']
default_running_mean_length = 7

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

# date and time handling

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

pad_fraction = 0.063 # matches Plotly's default AutoScale padding
def pad_timerange (time_range):
    ''' slightly expand figure time_range for better viewing'''
    padding = pad_fraction * (time_range[1] - time_range[0])
    return [time_range[0] - padding, time_range[1] + padding]
def unpad_timerange (time_range):
    ''' remove figure time_range padding'''
    padding = pad_fraction * (time_range[1] - time_range[0]) / (1.0 + 2*pad_fraction)
    return [time_range[0]+padding, time_range[1]-padding]

def update_figure_timerange (time_range, fig, scale_yrange=True):
    time_range = pad_timerange(time_range)
    # apply the xrange change
    fig['layout']['xaxis']['range'] = [dateTimeInt_to_dateTime(ti) for ti in time_range]
    fig['layout']['xaxis']['autorange'] = False
    # update the yrange given the xrange visible
    if scale_yrange:
        for key in fig['layout']:
            if key[:5] == 'yaxis':
                # figure out which quantity is plotted on this axis
                axis = key
                label = fig['layout'][key]['title']['text']
                for quantity in settings.keys():
                    if settings[quantity]['label'] == label:
                        break
                # update the axis yrange to what is visible
                visible_data = df[quantity][(df['DateTime-int'] >= time_range[0]) & (df['DateTime-int'] <= time_range[1])]
                fig['layout'][axis]['range'] = pad_timerange([visible_data.min(), visible_data.max()])
                fig['layout'][axis]['autorange'] = False
                del visible_data
    return fig

def redraw_figure (quantities_to_plot, running_mean_length):

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
        # add a running mean if requested
        if running_mean_length != None:
            running_mean = df[['DateTime', quantity]].reset_index().set_index('DateTime').sort_index()
            running_mean = running_mean.resample('1D').mean().rolling(running_mean_length, min_periods=0, center=True).mean()
            fig.add_trace(go.Scatter(
                x=running_mean.index, y=running_mean[quantity],
                mode='lines',
                hoverinfo='skip',
                #hovertemplate='%{hovertext:.1f}',
                #hovertext=df[quantity],
                name=('%s, running mean' % settings[quantity]['label']),
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
            domain=[max(padding['left'] - padding_step, 0.), min(1.0, 1.0 + padding_step - padding['right'])],
            autorange=False
        ),
        hovermode='x unified',
        margin={'t':40}
    )

    update_figure_timerange([0,100], fig)

    return fig

fig = redraw_figure(default_quantities, default_running_mean_length)

# APP LAYOUT ----------------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def RM_slider_transform (x):
    return int(100.*np.log(x)/np.log(5))
def RM_slider_invTransform (x):
    return int(np.exp(x*np.log(5.) / 100.))

app.layout = html.Div([
    dcc.Dropdown(
        id='quantity-dropdown',
        options=[{'label': settings[quantity]['label'], 'value': quantity} for quantity in settings.keys()],
        value=default_quantities,
        multi=True
    ),
    html.Div(" "),
    html.Div(className='row', children=[
        html.Div(),
        dcc.Checklist(
            id='options-checklist',
            options=[{'label': 'Running Mean', 'value': 'running_mean'}],
            value=['running_mean',]
        ),
        dcc.Slider(
            id='running-mean-slider',
            min=0,
            max=RM_slider_transform(90),
            value=RM_slider_transform(default_running_mean_length),
            marks={RM_slider_transform(i): ('1 day' if i==1 else '%i days' % i if i < 30 else '%im' % int(i/30.)) for i in [1,7,14,30,60,90]}
        ),
        html.Div()
    ], style={'display':'grid', 'grid-template-columns': '10% 20% 60% 10%', 'height':'40px', 'padding':10}),
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

# APP CALLBACKS ------------------------------------------------------------

@app.callback(
    Output('graph', 'figure'),
    Input('quantity-dropdown', 'value'),
    Input('time-range-slider', 'value'),
    Input('options-checklist', 'value'),
    Input('running-mean-slider', 'value'),
    State('graph', 'figure')
)
def update_figure (quantities, time_range, options, running_mean_length, fig):
    print(fig['layout']['hovermode'])
    print('Updating the figure.. ', end='', flush=True)
    ctx = dash.callback_context
    triggers = [x['prop_id'].split('.')[0] for x in ctx.triggered]
    # prevent callback loops
    if len(set(triggers).intersection(['quantity-dropdown', 'options-checklist', 'running-mean-slider'])) > 0:
        if 'running_mean' not in options:
            running_mean_length = None
        else:
            running_mean_length = RM_slider_invTransform(running_mean_length)
        fig = redraw_figure(quantities, running_mean_length)
        fig = update_figure_timerange(time_range, fig)
    if 'time-range-slider' in triggers and time_range != None:
        current_timerange = unpad_timerange([1.0*dateTime_to_dateTimeInt(t) for t in fig['layout']['xaxis']['range']])
        if time_range != current_timerange:
            fig = update_figure_timerange(time_range, fig)
        else: # nothing to do
            print('noting to update. ', end='', flush=True)
            PreventUpdate()
    print('done.', flush=True)
    return fig

@app.callback(
    Output('time-range-slider', 'value'),
    Input('graph', 'relayoutData')
)
def update_time_range_slider (relayoutData):
    print('Updating the time slider..', end='', flush=True)
    # initial and reset
    if relayoutData == None or 'autosize' in relayoutData.keys() or 'xaxis.autorange' in relayoutData.keys():
        print('done.', flush=True)
        return [0,100]
    # modifying the graph through graph tools
    new_timerange = [1.0*dateTime_to_dateTimeInt(t) for t in [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]]
    new_timerange = unpad_timerange(new_timerange)
    print('done.', flush=True)
    return new_timerange

# RUN THE SERVER ------------------------------------------------------------

if __name__ == '__main__':
    app.server(host='0.0.0.0', port=os.environ['PORT'], debug=True)