from pydantic import BaseModel
import random
from typing import Set

class Dice(BaseModel):
	color: str
	number: int
	

class DiceRoller:
    # There are 6 dice in total, 5 for normal camels and 1 for crazy camel
    DICE_COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'grey']  # grey is for the crazy camel
    # Each dice can roll a number between 1 and 3
    DICE_NUMBERS = [1, 2, 3]
    # Grey dice numbers are either in white or black indicating the crazy camel
    GREY_DICE_NUMBER_COLORS = ['white', 'black']

    dices_rolled: Set[Dice] = set()

    def __init__(self, seed: int = 42):
        # create a random number generator for reproducibility if needed
        self.rng = random.Random(seed)

    def roll_dice(self) -> Dice:
        colors = set(DiceRoller.DICE_COLORS) - {d.color for d in self.dices_rolled}
        color = self.rng.choice(colors)
        if color == 'grey':
            color = self.rng.choice(DiceRoller.GREY_DICE_NUMBER_COLORS)
            number = self.rng.choice(DiceRoller.DICE_NUMBERS)
        else:
            number = self.rng.choice(DiceRoller.DICE_NUMBERS)
        dice = Dice(color=color, number=number)
        self.dices_rolled.add(dice)
        return dice
    
    def roll_grey_dice(self) -> Dice:
        """Specifically roll the grey dice for crazy camel (only at the beginning of the game).
        This is needed because there is only one dice for crazy camels.
        """
        color = self.rng.choice(DiceRoller.GREY_DICE_NUMBER_COLORS)
        number = self.rng.choice(DiceRoller.DICE_NUMBERS)
        dice = Dice(color=color, number=number)
        self.dices_rolled.add(dice)
        return dice

    def reset(self) -> None:
        self.dices_rolled = set()
