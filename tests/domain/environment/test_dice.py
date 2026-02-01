import pytest
from camelgo.domain.environment.dice import Dice, DiceRoller
from camelgo.domain.environment.game_config import GameConfig, Color

def test_dice_model():
    dice = Dice(base_color=Color.YELLOW, number=3)
    assert dice.color == Color.YELLOW
    assert dice.number == 3


def test_dice_roller_roll():
    roller = DiceRoller(seed=123)
    dice = roller.roll_dice()
    assert isinstance(dice, Dice)
    assert dice.color in GameConfig.ALL_CAMEL_COLORS
    assert dice.number in DiceRoller.DICE_NUMBERS
    assert len(roller.dices_rolled) == 1


def test_dice_roller_multiple_rolls():
    roller = DiceRoller(seed=42)
    rolled = [roller.roll_dice() for _ in range(3)]
    assert len(roller.dices_rolled) == 3
    colors = [d.color for d in rolled]
    assert len(set(colors)) == 3  # Each rolled dice color should be different
    assert set(colors).issubset(set(GameConfig.ALL_CAMEL_COLORS))
    for dice in rolled:
        assert dice.number in DiceRoller.DICE_NUMBERS


def test_dice_roller_roll_grey_dice():
    roller = DiceRoller(seed=99)
    dice = roller.roll_grey_dice()
    assert dice.color in DiceRoller.GREY_DICE_NUMBER_COLORS
    assert dice.number in DiceRoller.DICE_NUMBERS
    assert dice in roller.dices_rolled


def test_dice_roller_reproducibility_with_seed():
    roller1 = DiceRoller(seed=123)
    roller2 = DiceRoller(seed=123)
    rolls1 = [roller1.roll_dice() for _ in range(3)]
    roller1.reset()
    rolls2 = [roller2.roll_dice() for _ in range(3)]
    assert rolls1 == rolls2


def test_dice_roller_randomness_with_different_seeds():
    roller1 = DiceRoller(seed=123)
    roller2 = DiceRoller(seed=456)
    rolls1 = [roller1.roll_dice() for _ in range(3)]
    roller1.reset()
    rolls2 = [roller2.roll_dice() for _ in range(3)]
    assert rolls1 != rolls2
