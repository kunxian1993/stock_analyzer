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
                                                                id='input-stock-A-q',
                                                                placeholder='Ticker Symbol',
                                                                type='text',
                                                                className='Input-box'
                                                        )
                                                ),
                                                html.Button('SUBMIT', id='text-submit-button-A-q', n_clicks=0, className='Submit-button'),
                                        ],
                                        style={'width': '13%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                ),
                                html.Div(
                                        children=[
                                                # ticker input textbox
                                                html.Div(children="Stock Ticker B", className="menu-title"),
                                                html.Div(
                                                        dcc.Input(
                                                                id='input-stock-B-q',
                                                                placeholder='Ticker Symbol',
                                                                type='text',
                                                                className='Input-box'
                                                        )
                                                ),
                                                html.Button('SUBMIT', id='text-submit-button-B-q', n_clicks=0, className='Submit-button'),
                                        ],
                                        style={'width': '13%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                ),
                                html.Div(
                                        children=[
                                                # metric selection dropdown
                                                dcc.Store(id='stock-data-q'),
                                                html.Div(children="Metric", className="menu-title"),
                                                dcc.Dropdown(
                                                        id='yaxis-column-q',
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
                                                        id='yaxis-column-denominator-q',
                                                        value='None',
                                                        className="dropdown"
                                                )                                                
                                        ],
                                        style={'width': '30%', 'height': '25%', 'font-size': '16px', 'margin-top': '5px'}
                                )
                        ],
                        className="menu"
                ),
                html.Div(
                        html.Div(dash_table.DataTable(id='growth-table-q', merge_duplicate_headers=True), className='card'),
                        className='wrapper'
                ),
                html.Div(
                        html.Div(dcc.Graph(id='stock-bar-chart-q'), className="card"),
                        className="wrapper"
                ),
                html.Div(
                        html.Div(dcc.Graph(id='stock-trend-chart-q'), className='card'),
                        className='wrapper'
                )
        ]
)

# callback for user interaction
@callback(
    Output('yaxis-column-q', 'options'),
    Output('yaxis-column-denominator-q', 'options'),
    Output('stock-data-q', 'data'),
    Input('text-submit-button-A-q', 'n_clicks'),
    Input('text-submit-button-B-q', 'n_clicks'),
    State('input-stock-A-q', 'value'),
    State('input-stock-B-q', 'value'))
def update_dropdown(n_clicks_A, n_clicks_B, selected_stock_A, selected_stock_B):

        if n_clicks_A < 1 and n_clicks_B < 1:
                raise PreventUpdate
        else:
                df = pd.DataFrame()
                for selected_stock in [selected_stock_A, selected_stock_B]:
                        if selected_stock != None:
                                stock_object = yf.Ticker(selected_stock)

                                # pull financial statements
                                s_is = stock_object.quarterly_income_stmt
                                s_bs = stock_object.quarterly_balancesheet
                                s_cf = stock_object.quarterly_cashflow
                                
                                # combine statements and transpose
                                df1 = pd.concat([s_is,s_bs,s_cf], keys=['IncomeStatement','BalanceSheet','CashFlow'], names=['Source', 'Line-Item'])
                                df1 = df1.reset_index().set_index('Line-Item').drop(['Source'], axis=1)
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

                                # merge df from multiple tickers
                                df = pd.concat([df,df1])

                options = [{'label': i, 'value': i} for i in df.columns]
                options.append({'label': 'None', 'value': 'None'})
                df['Quarter'] = pd.PeriodIndex(df['Date'], freq='Q').astype(str)
                # convert df to json for keeping in dcc store
                stock_data = df.to_dict('records')

                return options, options, stock_data

# callback for user interaction
@callback(
    Output('stock-bar-chart-q', 'figure'),
    Output('stock-trend-chart-q', 'figure'),
    Output('growth-table-q', 'data'),
    Output('growth-table-q', 'style_data_conditional'),
    Input('text-submit-button-A-q', 'n_clicks'),
    Input('text-submit-button-B-q', 'n_clicks'),
    Input('stock-data-q', 'data'),
    Input('yaxis-column-q', 'value'),
    Input('yaxis-column-denominator-q', 'value'))
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
                fig = px.bar(df, x="Quarter", y=title, color="Ticker", barmode="group")
                fig.update_xaxes(type='category')
                fig2 = px.line(df,x='Quarter',y=title, color="Ticker", markers=True)

                # get '% Change' by group
                df2 = df[['Ticker','Quarter',title]].set_index(['Quarter','Ticker']).groupby('Ticker').pct_change()
                df2 = df2.rename(columns={title: '% Change'})

                # merge back to raw data to get metric values and pivot
                df2 = df2.merge(df, how='left', on=['Quarter','Ticker'])
                df_table=df2.pivot(index='Quarter', columns='Ticker', values=[title, '% Change'])

                stock_A = df_table.columns[0][1]
                stock_B = df_table.columns[1][1]

                # combine multi level columns to single level
                df_table.columns = df_table.columns.map(' - '.join).str.strip(' - ')
                
                # conditional format for table
                conditional_format = [
                                        {
                                        'if': {
                                                'filter_query': '{% Change - ' + stock_A + '} > 0',
                                                'column_id': f"% Change - {stock_A}"
                                        },
                                        'color': '#00B050'
                                        },
                                                                                {
                                        'if': {
                                                'filter_query': '{% Change - ' + stock_A + '} < 0',
                                                'column_id': f"% Change - {stock_A}"
                                        },
                                        'color': '#FF0000'
                                        },
                                        {
                                        'if': {
                                                'filter_query': '{% Change - ' + stock_B + '} > 0',
                                                'column_id': f"% Change - {stock_B}"
                                        },
                                        'color': '#00B050'
                                        },
                                                                                {
                                        'if': {
                                                'filter_query': '{% Change - ' + stock_B + '} < 0',
                                                'column_id': f"% Change - {stock_B}"
                                        },
                                        'color': '#FF0000'
                                        }
                                        ]

                return fig, fig2, df_table.reset_index().to_dict('records'), conditional_format

# if __name__ == '__main__':
#     app.run(debug=True)
