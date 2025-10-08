import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    html.H2("Square Calculator"),
    dbc.Row([
        dbc.Col([
            dbc.Input(id="number-input", type="number", placeholder="Enter a number", min=0),
            dbc.Button("Calculate Square", id="calc-btn", color="primary", className="mt-2"),
            html.Div(id="result", className="mt-3")
        ], width=6)
    ])
], className="mt-5")

@app.callback(
    Output("result", "children"),
    Input("calc-btn", "n_clicks"),
    State("number-input", "value")
)
def update_result(n_clicks, value):
    if n_clicks and value is not None:
        try:
            num = int(value)
            return f"Result: {num * num}"
        except Exception:
            return "Invalid input."
    return ""

if __name__ == "__main__":
    import os
    cert_path = os.path.join(os.path.dirname(__file__), "cert.pem")
    key_path = os.path.join(os.path.dirname(__file__), "key.pem")
    app.run(host="0.0.0.0", port=8080, ssl_context=(cert_path, key_path))
