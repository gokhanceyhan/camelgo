

class GameConfig:
    BOARD_SIZE = 16  # Number of tiles on the board
    NUM_CAMELS = 7  # Total number of camels in the game
    NUM_NORMAL_CAMELS = 5  # Number of normal camels
    NUM_CRAZY_CAMELS = 2  # Number of crazy camels
    CAMEL_COLORS = ['blue', 'yellow', 'green', 'purple', 'red']  # Standard camel colors
    CRAZY_CAMELS = ['white', 'black']  # Camels that move backwards
    ALL_CAMEL_COLORS = CAMEL_COLORS + CRAZY_CAMELS
    DICE_VALUES = [1, 2, 3]  # Possible dice roll values
    BET_VALUES = [5, 3, 2, 2]  # Bet values for first to third place and subsequent bets
    STARTING_MONEY = 3  # Starting money for each player
    MAX_PLAYERS = 8  # Maximum number of players allowed
    MIN_PLAYERS = 2  # Minimum number of players required
    CORRECT_GAME_BET_POINTS = [8, 5, 3, 2, 1]  # Points for correct bets in order
    INCORRECT_GAME_BET_PENALTY = 1  # Points lost for incorrect bets

    @classmethod
    def is_camel_crazy(cls, color: str) -> bool:
        return color in cls.CRAZY_CAMELS