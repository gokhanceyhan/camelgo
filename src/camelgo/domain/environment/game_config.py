

class GameConfig:
    BOARD_SIZE = 16  # Number of tiles on the board
    CAMEL_COLORS = ['blue', 'yellow', 'green', 'purple', 'red']  # Standard camel colors
    CRAZY_CAMELS = ['white', 'black']  # Camels that move backwards
    DICE_VALUES = [1, 2, 3]  # Possible dice roll values
    BET_VALUES = [5, 3, 2, 2]  # Bet values for first to third place and subsequent bets
    STARTING_MONEY = 3  # Starting money for each player
    MAX_PLAYERS = 8  # Maximum number of players allowed
    MIN_PLAYERS = 2  # Minimum number of players required

    @classmethod
    def is_camel_crazy(cls, color: str) -> bool:
        return color in cls.CRAZY_CAMELS