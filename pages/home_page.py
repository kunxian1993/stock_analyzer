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
                                                dcc.Store(id='stock-data-home'),
                                                html.Div(children="Enter ticker:", className="menu-title"),
                                                html.Div(
                                                        dcc.Input(
                                                                id='input-stock-A-home',
                                                                placeholder='Ticker Symbol',
                                                                type='text',
                                                                className='Input-box'
                                                        )
                                                ),
                                                html.Button('SUBMIT', id='text-submit-button-A-home', n_clicks=0, className='Submit-button'),
                                        ],
                                        style={'width': '25%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                )                                
                        ],
                        className="menu"
                ),
                html.Div(
                        html.Div([html.H3('10Q Metrics'), dash_table.DataTable(id='quarterly-growth-table-home', style_cell={'textAlign': 'center'})], className='card'),
                        className='wrapper'
                ),
                html.Div(
                        html.Div(dcc.Graph(id='quarterly-stock-trend-chart-home'), className='card'),
                        className='wrapper'
                ),
                html.Div(
                        html.Div([html.H3('10K Metrics'),dash_table.DataTable(id='growth-table-home', style_cell={'textAlign': 'center'})], className='card'),
                        className='wrapper'
                ),
                html.Div(
                        html.Div(dcc.Graph(id='stock-trend-chart-home'), className='card'),
                        className='wrapper'
                )
        ]
)

# callback for user interaction
@callback(
    Output('stock-data-home', 'data'),
    Input('text-submit-button-A-home', 'n_clicks'),
    State('input-stock-A-home', 'value'))
def update_dropdown(n_clicks_A, selected_stock_A):

        if n_clicks_A < 1:
                raise PreventUpdate
        else:
                df = pd.DataFrame()
                for selected_stock in [selected_stock_A]:
                        if selected_stock != None:
                                stock_object = yf.Ticker(selected_stock)

                                # pull financial statements
                                s_is = stock_object.income_stmt
                                s_bs = stock_object.balancesheet
                                s_cf = stock_object.cashflow
                                
                                # combine statements and transpose
                                df1 = pd.concat([s_is,s_bs,s_cf]).transpose()

                                df1['Date']=df1.index
                                df1['Ticker']=selected_stock

                                df1['Year'] = df1['Date'].dt.year
                                df1['Year-Month'] = df1['Date'].dt.year.astype(str) + '-' + df1['Date'].dt.month.astype(str)

                                # get historical stock price
                                today = datetime.date.today().strftime('%Y-%m-%d')
                                hist_price = stock_object.history(start=f"{df1['Year'].min()}-01-01", end = today, interval="1wk")
                                hist_price = hist_price.reset_index()
                                hist_price['Year-Month'] = hist_price['Date'].dt.year.astype(str) + '-' + hist_price['Date'].dt.month.astype(str)

                                # aggregate to monthly average price
                                table = pd.pivot_table(hist_price, values=['Close', 'Volume'], index=['Year-Month'], aggfunc={'mean'})
                                table.columns = table.columns.droplevel(1)

                                # merge price with income statement
                                df1 = df1.merge(table, how='left', on=['Year-Month'])
                                
                                df = pd.concat([df,df1])

                                # pull quarterly financial statements
                                s_qis = stock_object.quarterly_income_stmt
                                s_qbs = stock_object.quarterly_balancesheet
                                s_qcf = stock_object.quarterly_cashflow
                                q_df = pd.DataFrame()

                                # combine statements and transpose
                                q_df1 = pd.concat([s_qis,s_qbs,s_qcf]).transpose()

                                # drop empty rows
                                q_df1 = q_df1.dropna(subset = ['Total Revenue'])

                                q_df1['Date']=q_df1.index
                                q_df1['Ticker']=selected_stock

                                q_df1['Year'] = q_df1['Date'].dt.year
                                q_df1['Year-Month'] = q_df1['Date'].dt.year.astype(str) + '-' + q_df1['Date'].dt.month.astype(str)
                                q_df1['Year-Quarter'] = q_df1['Date'].dt.year.astype(str) + '-Q' + ((q_df1['Date'].dt.month - 1) // 3 + 1).astype(str)

                                # merge price with income statement
                                q_df1 = q_df1.merge(table, how='left', on=['Year-Month'])

                                q_df = pd.concat([q_df,q_df1])

                # options = [{'label': i, 'value': i} for i in df.columns]
                # options.append({'label': 'None', 'value': 'None'})
                df['Year'] = df['Date'].dt.year
                
                # convert df to json for keeping in dcc store
                stock_data = {}
                stock_data['10Y'] = df.to_dict('records')
                stock_data['10Q'] = q_df.to_dict('records')

                return stock_data

# callback for user interaction
@callback(
    Output('stock-trend-chart-home', 'figure'),
    Output('growth-table-home', 'data'),
    Output('growth-table-home', 'columns'),
    Output('growth-table-home', 'style_data_conditional'),
    Input('text-submit-button-A-home', 'n_clicks'),
    Input('stock-data-home', 'data'))
def update_graph(n_clicks_A, stock_data):
        if n_clicks_A < 1 :
                raise PreventUpdate
        else:
                df = pd.DataFrame(stock_data['10Y'])
                
                df.sort_values(by=['Ticker', 'Date'], ascending=True, inplace=True)

                # calculate multiples
                df['Operating Margin'] = df['Operating Income'] / df['Total Revenue']
                df['Gross Margin'] = df['Total Revenue'] / df['Cost Of Revenue']
                df['Price to Earnings'] = df['Close'] / df['Diluted EPS']
                df['Working Capital'] = df['Current Assets']/df['Current Liabilities']
                df['CashFlow to NetIncome'] = df['Operating Cash Flow'] / df['Net Income']
                df['Retention Ratio'] = df['Retained Earnings'] / df['Net Income']

                # exclude null
                df = df[df['Operating Margin'].notnull()]
                df = df.set_index('Year')
                key_metrics = ['Operating Margin','Gross Margin','Price to Earnings','Working Capital','CashFlow to NetIncome','Retention Ratio','Close','Ticker']
                df1 = df[key_metrics]

                # calculate change and %change
                df3 = df1[key_metrics].groupby('Ticker').pct_change()
                df3 = df3.add_suffix('_Δ%')
                df2 = df1[key_metrics].groupby('Ticker').diff()
                df2 = df2.add_suffix('_Δ')

                # combine to single df
                # df4 = pd.concat([df1[key_metrics[:-1]], df2, df3], axis = 1, keys=['Raw','Change','%_Change'], names=['Source','Metric'])
                df4 = pd.concat([df1[key_metrics[:-1]], df3], axis = 1, keys=['Raw','%_Change'], names=['Source','Metric'])

               # sort axis
                df4 = df4.transpose().reset_index()
                df4 = df4.sort_values(by=['Metric'])
                df4 = df4.drop(['Source'],axis=1)

                # round values to 2dp
                value_cols = [i for i in df4.columns if type(i)==int]
                df4[value_cols] = df4[value_cols].astype(float).round(2)

                # df for line chart
                df5 = pd.concat([df1[key_metrics[:-1]], df2, df3], axis = 1)
                df5 = pd.melt(df5.reset_index(),id_vars=['Year'],value_vars=list(df5.columns),var_name='Metric', value_name='Value')

                fig = px.line(df5,x='Year',y='Value', color='Metric', markers=True)
                
                # add cell color coding              
                cols = df4.columns.to_list()
                conditional_format = []
                for i in range(len(cols)):
                        if i > 1:
                                rule_green = {
                                        'if': {
                                                'filter_query': f'{{{cols[i]}}} > {{{cols[i-1]}}}',
                                                'column_id': f'{cols[i]}'
                                        },
                                        # 'color': '#00B050'
                                        'backgroundColor': '#00B050'
                                        }
                                rule_red = {
                                        'if': {
                                                'filter_query': f'{{{cols[i]}}} < {{{cols[i-1]}}}',
                                                'column_id': f'{cols[i]}'
                                        },
                                        # 'color': "#FFFFFF",
                                        'backgroundColor': "#FF8585"
                                        }
                                conditional_format.append(rule_green)
                                conditional_format.append(rule_red)

                return fig, df4.to_dict('records'), [{'name': str(i), 'id': str(i)} for i in df4.columns], conditional_format


# callback for user interaction - quarterly
@callback(
    Output('quarterly-stock-trend-chart-home', 'figure'),
    Output('quarterly-growth-table-home', 'data'),
    Output('quarterly-growth-table-home', 'columns'),
    Output('quarterly-growth-table-home', 'style_data_conditional'),
    Input('text-submit-button-A-home', 'n_clicks'),
    Input('stock-data-home', 'data'))
def update_graph(n_clicks_A, stock_data):
        if n_clicks_A < 1 :
                raise PreventUpdate
        else:
                df = pd.DataFrame(stock_data['10Q'])
                
                df.sort_values(by=['Ticker', 'Date'], ascending=True, inplace=True)

                # calculate multiples
                df['Operating Margin'] = df['Operating Income'] / df['Total Revenue']
                df['Gross Margin'] = df['Total Revenue'] / df['Cost Of Revenue']
                df['Price to Earnings'] = df['Close'] / df['Diluted EPS']
                df['Working Capital'] = df['Current Assets']/df['Current Liabilities']
                df['CashFlow to NetIncome'] = df['Operating Cash Flow'] / df['Net Income']
                df['Retention Ratio'] = df['Retained Earnings'] / df['Net Income']

                # exclude null
                df = df[df['Operating Margin'].notnull()]
                df = df.set_index('Year-Month')
                key_metrics = ['Operating Margin','Gross Margin','Price to Earnings','Working Capital','CashFlow to NetIncome','Retention Ratio','Close','Ticker']
                df1 = df[key_metrics]

                # calculate change and %change
                df3 = df1[key_metrics].groupby('Ticker').pct_change()
                df3 = df3.add_suffix('_Δ%')
                df2 = df1[key_metrics].groupby('Ticker').diff()
                df2 = df2.add_suffix('_Δ')

                # combine to single df
                # df4 = pd.concat([df1[key_metrics[:-1]], df2, df3], axis = 1, keys=['Raw','Change','%_Change'], names=['Source','Metric'])
                df4 = pd.concat([df1[key_metrics[:-1]], df3], axis = 1, keys=['Raw','%_Change'], names=['Source','Metric'])

                # sort axis
                df4 = df4.transpose().reset_index()
                df4 = df4.sort_values(by=['Metric'])
                df4 = df4.drop(['Source'],axis=1)

                # round values to 2dp
                value_cols = [i for i in df4.columns if '-' in i]
                df4[value_cols] = df4[value_cols].astype(float).round(2)

                # df for line chart
                df5 = pd.concat([df1[key_metrics[:-1]], df2, df3], axis = 1)
                df5 = pd.melt(df5.reset_index(),id_vars=['Year-Month'],value_vars=list(df5.columns),var_name='Metric', value_name='Value')

                fig = px.line(df5,x='Year-Month',y='Value', color='Metric', markers=True)

                # add cell color coding              
                cols = df4.columns.to_list()
                conditional_format = []
                for i in range(len(cols)):
                        if i > 1:
                                rule_green = {
                                        'if': {
                                                'filter_query': f'{{{cols[i]}}} > {{{cols[i-1]}}}',
                                                'column_id': f'{cols[i]}'
                                        },
                                        # 'color': '#00B050'
                                        'backgroundColor': '#00B050'
                                        }
                                rule_red = {
                                        'if': {
                                                'filter_query': f'{{{cols[i]}}} < {{{cols[i-1]}}}',
                                                'column_id': f'{cols[i]}'
                                        },
                                        # 'color': "#FFFFFF",
                                        'backgroundColor': "#FF8585"
                                        }
                                conditional_format.append(rule_green)
                                conditional_format.append(rule_red)

                return fig, df4.to_dict('records'), [{'name': str(i), 'id': str(i)} for i in df4.columns], conditional_format

# if __name__ == '__main__':
#     app.run(debug=True)
