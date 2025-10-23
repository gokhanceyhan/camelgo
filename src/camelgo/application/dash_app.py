
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
        return html.Pre(
            f"GameState:\n"
            f"Players: {[p.name for p in gs.players]}\n"
            f"Legs Played: {gs.legs_played}\n"
            f"Next Leg Player: {gs.players[gs.next_leg_player].name}\n"
            f"Camel States: {getattr(gs.current_leg, 'camel_states', {})}"
        )
    return ""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, ssl_context=("src/camelgo/application/cert.pem", "src/camelgo/application/key.pem"))
