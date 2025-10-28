# import debugpy
# debugpy.listen(("0.0.0.0", 5678))
# print("Waiting for debugger attach...")
# debugpy.wait_for_client()
# print("Debugger attached!")

import os

from camelgo.domain.environment.game import Game
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    html.H2("CamelUp Game Setup"),
    dbc.Row([
        dbc.Col([
            dbc.Input(id="players-input", type="text", placeholder="Enter player names (comma separated)", className="mb-2"),
            dbc.Button("Start Game", id="start-btn", color="success", className="mb-2"),
            html.Div(id="game-state-left", className="mt-3")
        ], width=6),
        dbc.Col([
            html.Div(id="game-state", className="mt-3")
        ], width=6)
    ])
], className="mt-5")

@app.callback(
    Output("game-state", "children"),
    Input("start-btn", "n_clicks"),
    State("players-input", "value")
)
def start_game(n_clicks, players_value):
    if n_clicks and players_value:
        players = [p.strip() for p in players_value.split(",") if p.strip()]
        gs = Game.start_game(players=players)
        camel_states = getattr(gs.current_leg, "camel_states", {})
        camel_colors = {
            "red": "#ff4d4d",
            "blue": "#4d79ff",
            "green": "#4dff88",
            "yellow": "#ffe44d",
            "purple": "#b84dff",
            "white": "#f8f8f8",
            "black": "#222"
        }
        camel_cells = []
        for color in ["red", "blue", "green", "yellow", "purple", "white", "black"]:
            camel = camel_states[color]
            card_style = {"backgroundColor": camel_colors[color], "color": "#222" if color in ["yellow", "white"] else "#fff"}
            camel_cells.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(f"{color.title()} Camel"),
                        dbc.CardBody([
                            html.P(f"Track Position: {camel.track_pos}"),
                            html.P(f"Stack Position: {camel.stack_pos}"),
                            html.P(f"Finished: {getattr(camel, 'finished', False)}")
                        ])
                    ], className="mb-3", style=card_style)
                ], width=4)
            )
        return dbc.Row(camel_cells)
    return ""

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=True, ssl_context=("src/camelgo/application/cert.pem", "src/camelgo/application/key.pem"))
    app.run(host="0.0.0.0", port=8080, debug=True)
