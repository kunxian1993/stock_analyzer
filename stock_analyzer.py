import dash
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True)

app.layout = html.Div([
    html.Div(
        children=[
            dcc.Link(f"Income Statement - Yearly", href="/", style={'color': '#FFFFFF', 'margin-left': '10px', 'margin-right': '10px'}),
            dcc.Link(f"Income Statement - Quarterly", href="quarterly-statements", style={'color': '#FFFFFF', 'margin-left': '10px', 'margin-right': '10px'})
        ],
        className="nav-bar"
    ),
    html.Div(
            children=[
                    html.P(children="📊", className="header-emoji"),
                    html.H1(children="Stock Data", className="header-title"),
                    html.P(children="Analyze Stock Data", className="header-description")
            ],
            className="header"
    ),


    dash.page_container
])

if __name__ == '__main__':
    app.run(debug=True)