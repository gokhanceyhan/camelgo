# import debugpy
# debugpy.listen(("0.0.0.0", 5678))
# print("Waiting for debugger attach...")
# debugpy.wait_for_client()
# print("Debugger attached!")

import os
import traceback

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from camelgo.domain.environment.action import Action
from camelgo.domain.environment.dice import Dice, DiceRoller
from camelgo.domain.environment.game import Game


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


app.layout = dbc.Container([
    html.H2("CamelUp Game Setup"),
    dbc.Row([
        dbc.Col([
            dbc.Input(id="players-input", type="text", placeholder="Enter player names (comma separated)", className="mb-2"),
            dbc.Button("Start Game", id="start-btn", color="success", className="mb-2"),
            html.Hr(),
            html.H5("Enter Action Information", className="mt-3 mb-2"),
            dcc.Dropdown(id="action-player", placeholder="Select player", className="mb-2"),
            html.H6("Dice Roll Action", className="mt-3 mb-2"),
            dbc.Input(id="action-dice-color", type="text", placeholder="Dice color (optional)", className="mb-2"),
            dbc.Input(id="action-dice-number", type="number", placeholder="Dice number (optional)", className="mb-2"),
            html.H6("Tile Action", className="mt-3 mb-2"),
            dbc.Select(id="action-tile-type", options=[{"label": "None", "value": "none"}, {"label": "Cheering", "value": "cheering"}, {"label": "Booing", "value": "booing"}], value="none", className="mb-2"),
            dbc.Input(id="action-tile-pos", type="number", placeholder="Tile position (optional)", className="mb-2"),
            html.H6("Leg Betting Action", className="mt-3 mb-2"),
            dbc.Input(id="action-leg-bet", type="text", placeholder="Leg bet camel color (optional)", className="mb-2"),
            html.H6("Game Betting Action", className="mt-3 mb-2"),
            dbc.Input(id="action-winner-bet", type="text", placeholder="Game winner bet (optional)", className="mb-2"),
            dbc.Input(id="action-loser-bet", type="text", placeholder="Game loser bet (optional)", className="mb-2"),
            dbc.Button("Play Action", id="action-played-btn", color="primary", className="mb-2"),
            html.Div(id="action-feedback", className="mt-2"),
        ], width=6),
        dbc.Col([
            html.H4("Game State", className="mb-3"),
            html.Div(id="game-state", className="mt-3")
        ], width=6)
    ]),
    dcc.Store(id="game-store")
], className="mt-5")

# Callback to update player dropdown options based on current game state
@app.callback(
    Output("action-player", "options"),
    Input("game-store", "data")
)
def update_player_dropdown(game_data):
    if not game_data or "players" not in game_data:
        return []
    return [{"label": name, "value": name} for name in game_data["players"].keys()]

# Helper to render game state
def render_game_state(gs):
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

# Unified callback for game start and action play
@app.callback(
    Output("game-state", "children"),
    Output("action-feedback", "children"),
    Output("game-store", "data"),
    Input("start-btn", "n_clicks"),
    Input("action-played-btn", "n_clicks"),
    State("players-input", "value"),
    State("game-store", "data"),
    State("action-player", "value"),
    State("action-dice-color", "value"),
    State("action-dice-number", "value"),
    State("action-tile-pos", "value"),
    State("action-tile-type", "value"),
    State("action-leg-bet", "value"),
    State("action-winner-bet", "value"),
    State("action-loser-bet", "value")
)
def unified_callback(start_n, 
                     action_n, 
                     players_value, 
                     game_data, 
                     player, 
                     dice_color, 
                     dice_number, 
                     tile_pos, 
                     tile_type, 
                     leg_bet, 
                     winner_bet, 
                     loser_bet):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", "", None
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger == "start-btn":
        if start_n and players_value:
            players = [p.strip() for p in players_value.split(",") if p.strip()]
            gs = Game.start_game(player_names=players)
            # Robust recursive serialization for game state
            return render_game_state(gs), "Game started.", gs.model_dump()
        return "", "", None
    elif trigger == "action-played-btn":
        if not action_n or not game_data:
            return dash.no_update, "", dash.no_update
        
        gs = Game.model_validate(game_data)
        
        action_kwargs = {"player": player}
        if dice_color and dice_number:
            action_kwargs["dice_rolled"] = Dice(color=dice_color, number=int(dice_number))
        if tile_type == "cheering" and tile_pos:
            action_kwargs["cheering_tile_placed"] = int(tile_pos)
        if tile_type == "booing" and tile_pos:
            action_kwargs["booing_tile_placed"] = int(tile_pos)
        if leg_bet:
            action_kwargs["leg_bet"] = leg_bet
        if winner_bet:
            action_kwargs["game_winner_bet"] = winner_bet
        if loser_bet:
            action_kwargs["game_loser_bet"] = loser_bet
        action = Action(**action_kwargs)

        try:
            gs.play_action(action)
            feedback = "Action played successfully."
        except Exception as e:
            feedback = f"Error: {e}\n{traceback.format_exc()}"
        # Robust recursive serialization for game state
        return render_game_state(gs), feedback, gs.model_dump()
    
    return dash.no_update, dash.no_update, dash.no_update


if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=True, ssl_context=("src/camelgo/application/cert.pem", "src/camelgo/application/key.pem"))
    app.run(host="0.0.0.0", port=8080, debug=True)
