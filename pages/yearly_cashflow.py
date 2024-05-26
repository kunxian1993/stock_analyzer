from dash import Dash, html, dash_table, dcc, register_page,  callback
from dash.dcc.Dropdown import Dropdown
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px

# app = Dash(__name__)

register_page(__name__)

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
                                                                id='input-stock-A-CF',
                                                                placeholder='Ticker Symbol',
                                                                type='text',
                                                                className='Input-box'
                                                        )
                                                ),
                                                html.Button('SUBMIT', id='text-submit-button-A-CF', n_clicks=0, className='Submit-button'),
                                        ],
                                        style={'width': '13%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                ),
                                html.Div(
                                        children=[
                                                # ticker input textbox
                                                html.Div(children="Stock Ticker B", className="menu-title"),
                                                html.Div(
                                                        dcc.Input(
                                                                id='input-stock-B-CF',
                                                                placeholder='Ticker Symbol',
                                                                type='text',
                                                                className='Input-box'
                                                        )
                                                ),
                                                html.Button('SUBMIT', id='text-submit-button-B-CF', n_clicks=0, className='Submit-button'),
                                        ],
                                        style={'width': '13%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                ),
                                html.Div(
                                        children=[
                                                # metric selection dropdown
                                                dcc.Store(id='stock-data-CF'),
                                                html.Div(children="Metric", className="menu-title"),
                                                dcc.Dropdown(
                                                        id='yaxis-column-CF',
                                                        # options=[{'label': i, 'value': i} for i in data.columns],
                                                        value='Free Cash Flow',
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
                                                        id='yaxis-column-CF-denominator',
                                                        value='None',
                                                        className="dropdown"
                                                ),                                             
                                        ],
                                        style={'width': '30%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                )
                        ],
                        className="menu"
                ),
                html.Div(
                        html.Div(dcc.Graph(id='stock-bar-chart-CF'), className="card"),
                        className="wrapper"
                ),
                html.Div(
                        html.Div(dcc.Graph(id='stock-trend-chart-CF'), className='card'),
                        className='wrapper'
                ),
                html.Div(
                        html.Div(dash_table.DataTable(id='growth-table-CF'), className='card'),
                        className='wrapper'
                )
        ]
)

# callback for user interaction
@callback(
    Output('yaxis-column-CF', 'options'),
    Output('yaxis-column-CF-denominator', 'options'),
    Output('yaxis-column-CF-denominator', 'value'),
    Output('stock-data-CF', 'data'),
    Input('text-submit-button-A-CF', 'n_clicks'),
    Input('text-submit-button-B-CF', 'n_clicks'),
    State('input-stock-A-CF', 'value'),
    State('input-stock-B-CF', 'value'))
def update_dropdown(n_clicks_A, n_clicks_B, selected_stock_A, selected_stock_B):

        if n_clicks_A < 1 and n_clicks_B < 1:
                raise PreventUpdate
        else:
                df = pd.DataFrame()
                for selected_stock in [selected_stock_A, selected_stock_B]:
                        if selected_stock != None:
                                stock_object = yf.Ticker(selected_stock)
                                df1 = stock_object.cashflow
                                df1 = df1.transpose()
                                df1['Date']=df1.index
                                df1['Ticker']=selected_stock

                                df1['Year'] = df1['Date'].dt.year
                                df1['Year-Month'] = df1['Date'].dt.year.astype(str) + '-' + df1['Date'].dt.month.astype(str)
                                
                                # get historical stock price
                                hist_price = stock_object.history(start=f"{df1['Year'].min()}-01-01", end=f"{df1['Year'].max()}-12-31", interval="1wk")
                                hist_price = hist_price.reset_index()
                                hist_price['Year-Month'] = hist_price['Date'].dt.year.astype(str) + '-' + hist_price['Date'].dt.month.astype(str)

                                # aggregate to monthly average price
                                table = pd.pivot_table(hist_price, values=['Close', 'Volume'], index=['Year-Month'], aggfunc={'mean'})
                                table.columns = table.columns.droplevel(1)

                                # merge price with income statement
                                df1 = df1.merge(table, how='left', on=['Year-Month'])
                                
                                df = pd.concat([df,df1])


                options = [{'label': i, 'value': i} for i in df.columns]
                options.append({'label': 'None', 'value': 'None'})
                df['Year'] = df['Date'].dt.year
                
                # convert df to json for keeping in dcc store
                stock_data = df.to_dict('records')

                return options, options, 'None', stock_data

# callback for user interaction
@callback(
    Output('stock-bar-chart-CF', 'figure'),
    Output('stock-trend-chart-CF', 'figure'),
    Output('growth-table-CF', 'data'),
    Input('text-submit-button-A-CF', 'n_clicks'),
    Input('text-submit-button-B-CF', 'n_clicks'),
    Input('stock-data-CF', 'data'),
    Input('yaxis-column-CF', 'value'),
    Input('yaxis-column-CF-denominator', 'value'))
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

                # exclude blank rows
                df = df[df[title].notnull()]

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
