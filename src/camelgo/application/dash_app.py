
import os

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from camelgo.domain.environment.state_manager import StateManager

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    html.H2("CamelUp Game Setup"),
    dbc.Row([
        dbc.Col([
            dbc.Input(id="players-input", type="text", placeholder="Enter player names (comma separated)", className="mb-2"),
            dbc.Textarea(id="dices-input", placeholder="Enter dice rolls as color:value, e.g. blue:2,red:3", className="mb-2"),
            dbc.Button("Start Game", id="start-btn", color="success", className="mb-2"),
            html.Div(id="game-state", className="mt-3")
        ], width=6)
    ])
], className="mt-5")

@app.callback(
    Output("game-state", "children"),
    Input("start-btn", "n_clicks"),
    State("players-input", "value"),
    State("dices-input", "value")
)
def start_game(n_clicks, players_value, dices_value):
    if n_clicks and players_value and dices_value:
        players = [p.strip() for p in players_value.split(",") if p.strip()]
        dices_rolled = []
        for item in dices_value.split(","):
            if ":" in item:
                color, value = item.split(":")
                dices_rolled.append((color.strip(), int(value.strip())))
        manager = StateManager()
        manager.start_game(players=players, dices_rolled=dices_rolled)
        gs = manager.game_state()
        return html.Pre(f"GameState:\nPlayers: {[p.name for p in gs.players]}\nLegs Played: {gs.legs_played}\nNext Leg Player: {gs.next_leg_player}\nCamel States: {getattr(gs.current_leg, 'camel_states', {})}")
    return ""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, ssl_context=("src/camelgo/application/cert.pem", "src/camelgo/application/key.pem"))
