"""Implementation of the CamelGo environment using OpenAI Gymnasium."""

import logging
from typing import Optional

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from camelgo.domain.environment.game import Game
from camelgo.domain.environment.game_config import GameConfig
from camelgo.domain.environment.action import Action
from camelgo.domain.environment.dice import DiceRoller


class CamelGoEnv(gym.Env):
    metadata = {"render_modes": ["ansi"]}

    ACTION_DIM = 48
    OBSERVATION_DIM = 253

    def __init__(self, opponent_type="random"):
        super().__init__()
        
        # Action Space
        self.action_space = spaces.Discrete(CamelGoEnv.ACTION_DIM)
        
        # Observation Space (flattened vector of size 253)
        self.observation_space = spaces.Box(low=0, high=1, shape=(CamelGoEnv.OBSERVATION_DIM,), dtype=np.float32)
        
        self.agent_name = "Agent"
        self.opponent_name = "Opponent"
        self.player_names = [self.agent_name, self.opponent_name]
        
        self.game: Optional[Game] = None
        # TODO: Not being used!
        self.opponent_type = opponent_type

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Initialize Game
        dice_roller = DiceRoller(seed=self.np_random_seed)
        
        self.game = Game.start_game(
            player_names=self.player_names,
            dice_roller=dice_roller
        )
        
        # If it's not agent's turn, simulate until it is
        self._simulate_opponents()
        
        return self._get_obs(), self._get_info(self.agent_name)

    def step(self, action_idx: int):
        if self.game.finished:
            return self._get_obs(), 0.0, True, False, self._get_info(self.agent_name)
        # 1. Decode Action
        action = Action.from_int(action_idx, self.agent_name)
        
        # 2. Capture state before move (for reward calc)
        prev_score = self.game.current_player_points(self.agent_name)
        
        # 3. Apply Action
        try:
            self._apply_action(action)
        except ValueError as e:
            # Invalid move attempted (should be masked, but safety net)
            logging.warning(f"Invalid action attempted by agent: {e}")
            return self._get_obs(), -1e6, True, False, {"error": str(e)}
        
        # 4. Simulate Opponents until it is Agent's turn again or Game Over
        if not self.game.finished:
            self._simulate_opponents()
            
        # 6. Calculate Reward
        # TODO: It might be a problem that agent receives reward only from dice roll within a leg.
        current_score = self.game.current_player_points(self.agent_name)
        reward = float(current_score - prev_score)
        
        terminated = self.game.finished
        truncated = False
        
        return self._get_obs(), reward, terminated, truncated, self._get_info(self.agent_name)

    def _get_obs(self) -> np.ndarray:
        # Construct the 253-dim vector
        obs = []
        
        # 1. Camels (7 * 23 = 161)
        # Order: Blue, Yellow, Green, Purple, Red, White, Black
        all_colors = GameConfig.CAMEL_COLORS + GameConfig.CRAZY_CAMELS
        camel_map = self.game.current_leg.camel_states
        
        for color in all_colors:
            camel = camel_map.get(color)
            if camel:
                # Pos One-Hot (16)
                pos_vec = [0] * 16
                if 1 <= camel.track_pos <= 16:
                    pos_vec[camel.track_pos - 1] = 1
                obs.extend(pos_vec)
                
                # Stack One-Hot (7)
                stack_vec = [0] * 7
                if 0 <= camel.stack_pos < 7:
                    stack_vec[camel.stack_pos] = 1
                obs.extend(stack_vec)
            else:
                # Should not happen if initialized correctly
                obs.extend([0] * 23)

        # 2. Dice (6)
        # color sequence: 'red', 'blue', 'green', 'yellow', 'purple', 'grey'
        # TODO: the color sequence is dependent on the DiceRoller implementation
        remaining_colors = self.game.dice_roller.remaining_colors()
        for d_color in DiceRoller.DICE_COLORS:
            obs.append(1.0 if d_color in remaining_colors else 0.0)

        # 3. Leg Bets (5 * 4 = 20)
        # Next available ticket value for normal camels {None, 2, 3, 5} -> One hot
        # Logic: check taken bets in leg.
        for color in GameConfig.CAMEL_COLORS:
            # Count how many bets placed on this color
            placed = 0
            for p in self.game.players.values():
                if color in self.game.current_leg.player_bets[p.name]:
                     placed += len(self.game.current_leg.player_bets[p.name][color])
            
            next_val = 0 # 0 means None
            if placed == 0: next_val = 5
            elif placed == 1: next_val = 3
            elif placed == 2: next_val = 2
            elif placed == 3: next_val = 2
            
            # One hot [None, 2, 3, 5]
            val_vec = [0, 0, 0, 0]
            if next_val == 0: val_vec[0] = 1
            elif next_val == 2: val_vec[1] = 1
            elif next_val == 3: val_vec[2] = 1
            elif next_val == 5: val_vec[3] = 1
            obs.extend(val_vec)
            
        # 4. Board Tiles (16 * 3 = 48)
        # {Empty, Cheer, Boo}
        cheer_pos = {pos for pos, _ in self.game.current_leg.cheering_tiles}
        boo_pos = {pos for pos, _ in self.game.current_leg.booing_tiles}
        
        for i in range(1, 17):
            # TODO: tile_vec size cold be decreased to 2 without accounting Empty explicitly
            tile_vec = [0, 0, 0] # Empty, Cheer, Boo
            if i in cheer_pos:
                tile_vec[1] = 1
            elif i in boo_pos:
                tile_vec[2] = 1
            else:
                tile_vec[0] = 1
            obs.extend(tile_vec)
            
        # 5. Agent Resources (16)
        agent = self.game.players[self.agent_name]
        obs.append(agent.points / 50.0) # Normalize loosely
        
        # Agents leg bets held (value sum)
        current_bets = self.game.current_leg.player_bets[self.agent_name]
        for color in GameConfig.CAMEL_COLORS:
            # Sum of bet values held
            value = sum(current_bets.get(color, []))
            obs.append(float(value) / 12.0)
            
        # Game Winners/Losers placed
        # We need to check hidden bets for self
        has_win_bet = [0]*5
        has_lose_bet = [0]*5
        for idx, color in enumerate(GameConfig.CAMEL_COLORS):
             if self.agent_name in self.game.hidden_game_winner_bets[color]:
                 has_win_bet[idx] = 1.0
             if self.agent_name in self.game.hidden_game_loser_bets[color]:
                 has_lose_bet[idx] = 1.0
        obs.extend(has_win_bet)
        obs.extend(has_lose_bet)
        
        # 6. Aggregates (2)
        # Global bet counts on Win/Lose
        win_counts = sum([len(self.game.hidden_game_winner_bets[c]) for c in GameConfig.CAMEL_COLORS])
        lose_counts = sum([len(self.game.hidden_game_loser_bets[c]) for c in GameConfig.CAMEL_COLORS])
        # TODO: normalize properly later. it depends on number of players.
        obs.append(float(win_counts) / 2.0)
        obs.append(float(lose_counts) / 2.0)
        
        return np.array(obs, dtype=np.float32)

    def _apply_action(self, action: Action):
        # Handle Roll Dice special case, as input Action doesn't have dice value info
        # The environment determines the dice roll result.
        
        is_roll_act = (action.leg_bet is None and 
                       action.game_winner_bet is None and 
                       action.game_loser_bet is None and 
                       action.cheering_tile_placed is None and 
                       action.booing_tile_placed is None)
        if is_roll_act:
            dice = self.game.roll_dice()
            action.dice_rolled = dice
             
        # Apply Action to Game
        self.game.play_action(action)
        
    def _simulate_opponents(self):
        while self.game.current_leg.next_player != self.agent_name and not self.game.finished:
            next_player = self.game.current_leg.next_player
            # Random Move
            valid_actions = self.get_action_mask(next_player) # Only valid
            valid_indices = np.where(valid_actions)[0]
            if len(valid_indices) == 0:
                # No moves? Should not happen.
                raise ValueError("No valid actions available for a player, should not happen.")
                 
            idx = np.random.choice(valid_indices)
            action = Action.from_int(idx, next_player)
            self._apply_action(action)
                
    def get_action_mask(self, player_name) -> np.ndarray:
        # 1=Valid, 0=Invalid
        mask = np.ones(CamelGoEnv.ACTION_DIM, dtype=bool)
        
        # 0: Roll Dice (Valid unless leg ended, but step handles that. Always valid if turn exists)
        
        # 1-5: Leg Bets
        # Check if tickets available for color
        for i, color in enumerate(GameConfig.CAMEL_COLORS):
            # Count total bets
            count = 0 
            for p in self.game.players.values():
                count += len(self.game.current_leg.player_bets[p.name][color])
            if count >= 4: # 5,3,2,2
                mask[1+i] = False
                
        # 6-10: Game Win (One per color per player)
        # Logic: Can usually bet once per turn. Always valid if not already bet
        for i, color in enumerate(GameConfig.CAMEL_COLORS):
            if player_name in self.game.hidden_game_winner_bets[color]:
                mask[6+i] = False

        # 11-15: Game Lose (Same logic as above)
        for i, color in enumerate(GameConfig.CAMEL_COLORS):
            if player_name in self.game.hidden_game_loser_bets[color]:
                mask[11+i] = False
        
        # 16-47: Tiles
        # Indices: Cheer (16-31) -> pos (1-16). Boo (32-47).
        # TODO: no need for having for both cheer and boo separately.
        
        # A player can place only one tile per leg
        tile_played_players = {p for _, p in self.game.current_leg.cheering_tiles} | \
            {p for _, p in self.game.current_leg.booing_tiles}
        if player_name in tile_played_players:
            mask[16:48] = [False] * 32
        
        # Invalid if occupied by camel or existing tile
        # Also adjacent rule: cannot place on X if X-1 or X+1 has a tile
        camel_positions = {
            c.track_pos for c in self.game.current_leg.camel_states.values()}
        
        tile_positions = {pos for pos, _ in self.game.current_leg.cheering_tiles} | \
            {pos for pos, _ in self.game.current_leg.booing_tiles}
                   
        for pos in range(1, 17):
            is_invalid = (pos in camel_positions) or (pos in tile_positions) or \
                (pos - 1 in tile_positions) or (pos + 1 in tile_positions)
            if is_invalid:
                mask[16 + (pos-1)] = False
                mask[32 + (pos-1)] = False
                
        return mask

    def _get_info(self, player_name):
        return {"mask": self.get_action_mask(player_name)}
