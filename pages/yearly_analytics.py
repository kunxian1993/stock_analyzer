from dash import Dash, html, dash_table, dcc, register_page,  callback
from dash.dcc.Dropdown import Dropdown
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px

# app = Dash(__name__)

register_page(__name__, path='/')

layout = html.Div(
        children=[
                # html.Div(
                #         children=[
                #                 html.P(children="📊", className="header-emoji"),
                #                 html.H1(children="Stock Data", className="header-title"),
                #                 html.P(children="Analyze Stock Data", className="header-description")
                #         ],
                #         className="header"
                # ),
                html.Div(
                        children=[
                                html.Div(
                                        children=[
                                                # ticker input textbox
                                                html.Div(children="Stock Ticker A", className="menu-title"),
                                                html.Div(
                                                        dcc.Input(
                                                                id='input-stock-A',
                                                                placeholder='Ticker Symbol',
                                                                type='text',
                                                                className='Input-box'
                                                        )
                                                ),
                                                html.Button('SUBMIT', id='text-submit-button-A', n_clicks=0, className='Submit-button'),
                                        ],
                                        style={'width': '13%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                ),
                                html.Div(
                                        children=[
                                                # ticker input textbox
                                                html.Div(children="Stock Ticker B", className="menu-title"),
                                                html.Div(
                                                        dcc.Input(
                                                                id='input-stock-B',
                                                                placeholder='Ticker Symbol',
                                                                type='text',
                                                                className='Input-box'
                                                        )
                                                ),
                                                html.Button('SUBMIT', id='text-submit-button-B', n_clicks=0, className='Submit-button'),
                                        ],
                                        style={'width': '13%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                ),
                                html.Div(
                                        children=[
                                                # metric selection dropdown
                                                dcc.Store(id='stock-data'),
                                                html.Div(children="Metric", className="menu-title"),
                                                dcc.Dropdown(
                                                        id='yaxis-column',
                                                        # options=[{'label': i, 'value': i} for i in data.columns],
                                                        value='Total Revenue',
                                                        className="dropdown"
                                                )                                                
                                        ],
                                        style={'width': '30%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                ),
                                 html.Div(
                                        children=[
                                                # metric selection dropdown
                                                html.Div(children="Denominator", className="menu-title"),
                                                dcc.Dropdown(
                                                        id='yaxis-column-denominator',
                                                        value='Total Revenue',
                                                        className="dropdown"
                                                )                                                
                                        ],
                                        style={'width': '30%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                )
                        ],
                        className="menu"
                ),
                html.Div(
                        html.Div(dcc.Graph(id='stock-bar-chart'), className="card"),
                        className="wrapper"
                ),
                html.Div(
                        html.Div(dcc.Graph(id='stock-trend-chart'), className='card'),
                        className='wrapper'
                ),
                html.Div(
                        html.Div(dash_table.DataTable(id='growth-table'), className='card'),
                        className='wrapper'
                )
        ]
)

# callback for user interaction
@callback(
    Output('yaxis-column', 'options'),
    Output('yaxis-column-denominator', 'options'),
    Output('stock-data', 'data'),
    Input('text-submit-button-A', 'n_clicks'),
    Input('text-submit-button-B', 'n_clicks'),
    State('input-stock-A', 'value'),
    State('input-stock-B', 'value'))
def update_dropdown(n_clicks_A, n_clicks_B, selected_stock_A, selected_stock_B):

        if n_clicks_A < 1 and n_clicks_B < 1:
                raise PreventUpdate
        else:
                df = pd.DataFrame()
                for selected_stock in [selected_stock_A, selected_stock_B]:
                        if selected_stock != None:
                                stock_object = yf.Ticker(selected_stock)
                                df1 = stock_object.income_stmt
                                df1 = df1.transpose()
                                df1['Date']=df1.index
                                df1['Ticker']=selected_stock
                                df = pd.concat([df,df1])


                options = [{'label': i, 'value': i} for i in df.columns]
                options.append({'label': 'None', 'value': 'None'})
                df['Year'] = df['Date'].dt.year
                
                # convert df to json for keeping in dcc store
                stock_data = df.to_dict('records')

                return options, options, stock_data

# callback for user interaction
@callback(
    Output('stock-bar-chart', 'figure'),
    Output('stock-trend-chart', 'figure'),
    Output('growth-table', 'data'),
    Input('text-submit-button-A', 'n_clicks'),
    Input('text-submit-button-B', 'n_clicks'),
    Input('stock-data', 'data'),
    Input('yaxis-column', 'value'),
    Input('yaxis-column-denominator', 'value'))
def update_graph(n_clicks_A, n_clicks_B, stock_data, selected_metric, selected_denominator):
        if n_clicks_A < 1 and n_clicks_B < 1 :
                raise PreventUpdate
        else:
                df = pd.DataFrame(stock_data)

                if selected_denominator == 'None':
                        # add new column for common size metric
                        title = selected_metric
                        df[title] = df[selected_metric]                    

                else:
                        # add new column for common size metric
                        title = selected_metric + '/' + selected_denominator
                        df[title] = df[selected_metric]/df[selected_denominator]
                
                df.sort_values(by=['Ticker', 'Date'], ascending=True, inplace=True)

                # plot charts
                fig = px.bar(df, x="Year", y=title, color="Ticker", barmode="group")
                fig.update_xaxes(type='category')
                fig2 = px.line(df,x='Date',y=title, color="Ticker", markers=True)
                
                # calculate % change
                df_table=df.pivot(index='Year', columns='Ticker', values=title)
                df_table['Year']=df_table.index
                df['% Change'] = df[title].pct_change()
                df['% Change'] = df['% Change'].map('{:.2%}'.format)
                df_table = df[['Ticker','Year',title,'% Change']]

                return fig, fig2, df_table.to_dict('records')

# if __name__ == '__main__':
#     app.run(debug=True)
