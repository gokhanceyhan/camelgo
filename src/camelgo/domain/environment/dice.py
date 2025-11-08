from pydantic import BaseModel, Field, PrivateAttr
import random
from typing import ClassVar, List, Set

from camelgo.domain.environment.game_config import GameConfig

class Dice(BaseModel):
    _color: str = PrivateAttr()
    number: int
    number_color: str = 'white'  # only relevant for grey dice indicating crazy camel color

    model_config = {'frozen': True}

    def __init__(self, color: str, number: int, number_color: str = 'white'):
        super().__init__(number=number, number_color=number_color)
        object.__setattr__(self, '_color', color)

    @property
    def color(self):
        if self._color == 'grey':
            return self.number_color
        return self._color
	

class DiceRoller(BaseModel):
    # There are 6 dice in total, 5 for normal camels and 1 for crazy camel
    DICE_COLORS: ClassVar[List[str]] = ['red', 'blue', 'green', 'yellow', 'purple', 'grey']  # grey is for the crazy camel
    # Each dice can roll a number between 1 and 3
    DICE_NUMBERS: ClassVar[List[int]] = [1, 2, 3]
    # Grey dice numbers are either in white or black indicating the crazy camel
    GREY_DICE_NUMBER_COLORS: ClassVar[List[str]] = ['white', 'black']

    _rng: random.Random = PrivateAttr()
    dices_rolled: List[Dice] = Field(default_factory=list)

    def __init__(self, seed: int = 42, **data):
        # create a random number generator for reproducibility if needed
        super().__init__(**data)
        self._rng = random.Random(seed)

    def roll_dice(self) -> Dice:
        # each rolled dice must have a unique color in a leg
        # privately access to the _color attribute not to pick grey color again
        colors = [c for c in DiceRoller.DICE_COLORS if c not in {d._color for d in self.dices_rolled}]
        color = self._rng.choice(colors)
        if color == 'grey':
            number_color = self._rng.choice(DiceRoller.GREY_DICE_NUMBER_COLORS)
            number = self._rng.choice(DiceRoller.DICE_NUMBERS)
            dice = Dice(color=color, number=number, number_color=number_color)
        else:
            number = self._rng.choice(DiceRoller.DICE_NUMBERS)
            dice = Dice(color=color, number=number)
        self.dices_rolled.append(dice)
        return dice
    
    def roll_grey_dice(self) -> Dice:
        """Specifically roll the grey dice for crazy camel (only at the beginning of the game).
        This is needed because there is only one dice for crazy camels.
        """
        number_color = self._rng.choice(DiceRoller.GREY_DICE_NUMBER_COLORS)
        number = self._rng.choice(DiceRoller.DICE_NUMBERS)
        dice = Dice(color='grey', number=number, number_color=number_color)
        self.dices_rolled.append(dice)
        return dice

    def reset(self) -> None:
        self.dices_rolled = []
