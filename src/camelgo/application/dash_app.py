# import debugpy
# debugpy.listen(("0.0.0.0", 5678))
# print("Waiting for debugger attach...")
# debugpy.wait_for_client()
# print("Debugger attached!")

import os

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from camelgo.domain.environment.game import Game


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
            html.H4("Game State", className="mb-3"),  # Header for right column
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
        gs = Game.start_game(player_names=players)
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
                        dbc.CardHeader(f"{color.title()}"),
                        dbc.CardBody([
                            html.P(f"Track: {camel.track_pos}"),
                            html.P(f"Stack: {camel.stack_pos}"),
                        ])
                    ], className="mb-3", style=card_style)
                ], width=3)
            )

        # Game state sections
        card_style = {"fontSize": "0.85rem", "padding": "0.5rem"}

        next_leg_section = dbc.Card([
            dbc.CardHeader("Player to Start Next Leg", style=card_style),
            dbc.CardBody(html.P(gs.next_leg_starting_player, style=card_style))
        ], className="mb-2", style=card_style)

        next_player_section = dbc.Card([
            dbc.CardHeader("Next Player to Play in Current Leg", style=card_style),
            dbc.CardBody(html.P(gs.current_leg.next_player, style=card_style))
        ], className="mb-2", style=card_style)

        dices_rolled_section = dbc.Card([
            dbc.CardHeader("Dices Rolled in Current Leg", style=card_style),
            dbc.CardBody([
                html.Ul([
                    html.Li(f"{d.color.title()} ({d.number})", style=card_style) for d in getattr(gs.dice_roller, "dices_rolled", [])
                ]) if getattr(gs.dice_roller, "dices_rolled", []) else html.P("None yet.", style=card_style)
            ])
        ], className="mb-2", style=card_style)

        leg_bets_section = dbc.Card([
            dbc.CardHeader("Leg Bets of Players", style=card_style),
            dbc.CardBody([
                html.Ul([
                    html.Li(f"{player}: " + ", ".join([f'{camel}: {bets}' for camel, bets in bets_dict.items()]), style=card_style)
                    for player, bets_dict in getattr(gs.current_leg, "player_bets", {}).items()
                ]) if getattr(gs.current_leg, "player_bets", {}) else html.P("No bets yet.", style=card_style)
            ])
        ], className="mb-2", style=card_style)

        points_section = dbc.Card([
            dbc.CardHeader("Points of Players", style=card_style),
            dbc.CardBody([
                html.Ul([
                    html.Li(f"{name}: {player.points}", style=card_style) for name, player in gs.players.items()
                ])
            ])
        ], className="mb-2", style=card_style)

        winner_bets_section = dbc.Card([
            dbc.CardHeader("Game Winner Bets So Far", style=card_style),
            dbc.CardBody([
                html.Ul([
                    html.Li(f"{camel}: {', '.join(players)}", style=card_style) for camel, players in gs.hidden_game_winner_bets.items()
                ]) if gs.hidden_game_winner_bets else html.P("No winner bets yet.", style=card_style)
            ])
        ], className="mb-2", style=card_style)

        loser_bets_section = dbc.Card([
            dbc.CardHeader("Game Loser Bets So Far", style=card_style),
            dbc.CardBody([
                html.Ul([
                    html.Li(f"{camel}: {', '.join(players)}", style=card_style) for camel, players in gs.hidden_game_loser_bets.items()
                ]) if gs.hidden_game_loser_bets else html.P("No loser bets yet.", style=card_style)
            ])
        ], className="mb-2", style=card_style)

        return html.Div([
            dbc.Row(camel_cells),
            next_leg_section,
            next_player_section,
            dices_rolled_section,
            leg_bets_section,
            points_section,
            winner_bets_section,
            loser_bets_section
        ])
    return ""

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=True, ssl_context=("src/camelgo/application/cert.pem", "src/camelgo/application/key.pem"))
    app.run(host="0.0.0.0", port=8080, debug=True)
