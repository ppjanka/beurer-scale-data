import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

import plotly.express as px
import pandas as pd

# LOAD IN THE DATA -----------------------------------------------------------

csv_filename = 'HealthManagerApp_DataExport.csv'
storage_heavy = False
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
        dfs.append(pd.read_csv(csv_filename, sep=';', header=chunk[0], nrows=(chunk[1]-chunk[0]+1)))
    df = pd.concat(dfs, ignore_index=True)
    del dfs
# otherwise figure out where the weight data is stored in the data dump, pack it into a string
else: # not storage heavy (single file pass, but saves as string first)
    import sys
    if sys.version_info[0] < 3: 
        from StringIO import StringIO
    else:
        from io import StringIO
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

print(df.head())

# SET UP THE APP ------------------------------------------------------------
#app = dash.Dash(__name__, external_stylesheets=external_stylesheets)