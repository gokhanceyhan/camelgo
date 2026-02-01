from pydantic import BaseModel, Field, PrivateAttr
import random
from typing import ClassVar, List, Optional, Set

from camelgo.domain.environment.game_config import GameConfig, Color

class Dice(BaseModel):
    base_color: Color
    number: int
    number_color: Optional[Color] = Color.WHITE  # only relevant for grey dice indicating crazy camel color

    model_config = {'frozen': True}

    @property
    def color(self):
        if self.base_color == Color.GREY:
            return self.number_color
        return self.base_color
	

class DiceRoller(BaseModel):
    # There are 6 dice in total, 5 for normal camels and 1 for crazy camel
    DICE_COLORS: ClassVar[List[Color]] = [
        Color.RED, Color.BLUE, Color.GREEN, 
        Color.YELLOW, Color.PURPLE, Color.GREY
    ]  # grey is for the crazy camel
    # Each dice can roll a number between 1 and 3
    DICE_NUMBERS: ClassVar[List[int]] = [1, 2, 3]
    # Grey dice numbers are either in white or black indicating the crazy camel
    GREY_DICE_NUMBER_COLORS: ClassVar[List[Color]] = [Color.WHITE, Color.BLACK]

    _rng: random.Random = PrivateAttr()
    dices_rolled: List[Dice] = Field(default_factory=list)

    def __init__(self, seed: int = 42, **data):
        # create a random number generator for reproducibility if needed
        super().__init__(**data)
        self._rng = random.Random(seed)

    def roll_dice(self) -> Dice:
        # each rolled dice must have a unique color in a leg
        # privately access to the _color attribute not to pick grey color again
        colors = [c for c in DiceRoller.DICE_COLORS if c not in {d.base_color for d in self.dices_rolled}]
        color = self._rng.choice(colors)
        if color == Color.GREY:
            number_color = self._rng.choice(DiceRoller.GREY_DICE_NUMBER_COLORS)
            number = self._rng.choice(DiceRoller.DICE_NUMBERS)
            dice = Dice(base_color=color, number=number, number_color=number_color)
        else:
            number = self._rng.choice(DiceRoller.DICE_NUMBERS)
            dice = Dice(base_color=color, number=number)
        self.dices_rolled.append(dice)
        return dice
    
    def deterministic_roll_dice(self, dice: Dice) -> Dice:
        """Deterministically roll a dice with given color and number (for testing purposes)."""
        rolled_colors = {d.color for d in self.dices_rolled}
        if dice.color in rolled_colors:
            raise ValueError(f"Dice with color {dice.color} has already been rolled.")
        self.dices_rolled.append(dice)
        return dice
    
    def roll_grey_dice(self) -> Dice:
        """Specifically roll the grey dice for crazy camel (only at the beginning of the game).
        This is needed because there is only one dice for crazy camels.
        """
        number_color = self._rng.choice(DiceRoller.GREY_DICE_NUMBER_COLORS)
        number = self._rng.choice(DiceRoller.DICE_NUMBERS)
        dice = Dice(base_color=Color.GREY, number=number, number_color=number_color)
        self.dices_rolled.append(dice)
        return dice

    def reset(self) -> None:
        self.dices_rolled = []

    def remaining_colors(self) -> Set[str]:
        return {c for c in DiceRoller.DICE_COLORS if c not in {d.base_color for d in self.dices_rolled}}
