from pydantic import BaseModel
import random
from typing import List, Set

from camelgo.domain.environment.game_config import GameConfig

class Dice(BaseModel):
    color: str
    number: int

    model_config = {'frozen': True}
	

class DiceRoller:
    # There are 6 dice in total, 5 for normal camels and 1 for crazy camel
    DICE_COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'grey']  # grey is for the crazy camel
    # Each dice can roll a number between 1 and 3
    DICE_NUMBERS = [1, 2, 3]
    # Grey dice numbers are either in white or black indicating the crazy camel
    GREY_DICE_NUMBER_COLORS = ['white', 'black']

    dices_rolled: List[Dice]

    def __init__(self, seed: int = 42):
        # create a random number generator for reproducibility if needed
        self.rng = random.Random(seed)
        self.dices_rolled = []

    def roll_dice(self) -> Dice:
        # each rolled dice must have a unique color in a leg
        colors = [c for c in GameConfig.ALL_CAMEL_COLORS if c not in {d.color for d in self.dices_rolled}]
        color = self.rng.choice(colors)
        if color == 'grey':
            color = self.rng.choice(DiceRoller.GREY_DICE_NUMBER_COLORS)
            number = self.rng.choice(DiceRoller.DICE_NUMBERS)
        else:
            number = self.rng.choice(DiceRoller.DICE_NUMBERS)
        dice = Dice(color=color, number=number)
        self.dices_rolled.append(dice)
        return dice
    
    def roll_grey_dice(self) -> Dice:
        """Specifically roll the grey dice for crazy camel (only at the beginning of the game).
        This is needed because there is only one dice for crazy camels.
        """
        color = self.rng.choice(DiceRoller.GREY_DICE_NUMBER_COLORS)
        number = self.rng.choice(DiceRoller.DICE_NUMBERS)
        dice = Dice(color=color, number=number)
        self.dices_rolled.append(dice)
        return dice

    def reset(self) -> None:
        self.dices_rolled = []
