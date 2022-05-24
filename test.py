# --- SeaBattle game for practical work on SkillFactory FPW-2.0 course
# --- Evgeniy Ivanov, flow FPW-42, Okt'2021
from __future__ import annotations

import random as rnd
import time


class BoardException(Exception):
    def __init__(self, message):
        super().__init__(message)


class OutOfBoardException(BoardException):
    def __init__(self, message='Out of board'):
        super().__init__(message)


class CollisionOnBoardException(BoardException):
    def __init__(self, message='Collision on board'):
        super().__init__(message)


class WrongCellSelectedException(BoardException):
    def __init__(self, message):
        super().__init__(message)


class StrikeHitException(Exception):
    def __init__(self):
        super().__init__()


class StrikeMissException(Exception):
    def __init__(self):
        super().__init__()


class Dot:
    DOT_STATES = {
        'hit': '*',
        'miss': '.',
        'dead': 'X',
        'blank': ' '
    }

    def __init__(self, row: int = 0, col: int = 0, state: str = DOT_STATES['blank']):
        self.row: int = row
        self.col: int = col
        self.state: str = state

    @property
    def visible(self):
        # --- comment / uncomment one string for invisible / visible target ships
        return False if self.state in ['4', '3', '2', '1'] else True
        # return True if self.state in ['4', '3', '2', '1'] else True

    def __eq__(self, other):
        return True if self.row == other.row and self.col == other.col else False

    def __repr__(self):
        return str((self.row, self.col))

    def __str__(self):
        return self.state


class Ship:

    def __init__(self, ship_size: int, horizontal: bool = True):
        self.ship_size: int = ship_size
        self.lives: int = ship_size
        self.horizontal: bool = horizontal
        self.dots: list = []
        self.set_position(0, 0)

    def __repr__(self):
        return str([dot.state for dot in self.dots])

    def set_position(self, row: int = 0, col: int = 0):
        if self.horizontal:
            self.dots = [Dot(row, col + i, f'{self.ship_size}') for i in range(self.ship_size)]
        else:
            self.dots = [Dot(row + i, col, f'{self.ship_size}') for i in range(self.ship_size)]


class Board:

    @staticmethod
    def random_direction() -> bool:
        return bool(((0, 1) * 5)[rnd.randint(0, 9)])

    def __init__(self, board_size: int):
        self.board_size: int = board_size
        self.cells: list = [[Dot(row, col) for col in range(self.board_size)] for row in range(self.board_size)]
        self.ships_types: tuple = (4, 3, 3, 2, 2, 2, 1, 1, 1, 1)
        self.ships: list = [Ship(ship_size, Board.random_direction()) for ship_size in self.ships_types]
        self.lives: int = len(self.ships)
        self.random_set_ships()

    def random_set_ships(self):
        for ship in self.ships:
            while True:
                row = rnd.randint(0, self.board_size - 1)
                col = rnd.randint(0, self.board_size - 1)
                try:
                    self.move_ship(ship, row, col)
                except BoardException:
                    continue
                else:
                    break

    def move_ship(self, ship: Ship, row: int, col: int):
        # ---
        def collision():
            if ship.horizontal:
                _rows = [_row for _row in range(row - 1, row + 2) if 0 <= _row < self.board_size]
                _cols = [_col for _col in range(col - 1, col + ship.ship_size + 1) if 0 <= _col < self.board_size]
            else:
                _rows = [_row for _row in range(row - 1, row + ship.ship_size + 1) if 0 <= _row < self.board_size]
                _cols = [_col for _col in range(col - 1, col + 2) if 0 <= _col < self.board_size]
            for _row in _rows:
                for _col in _cols:
                    if not self.cells[_row][_col].state == Dot.DOT_STATES['blank']:
                        return True
            return False
        # ---
        if row + ship.ship_size > self.board_size or col + ship.ship_size > self.board_size:
            raise OutOfBoardException
        else:
            if collision():
                raise CollisionOnBoardException
            else:
                ship.set_position(row, col)
                for dot in ship.dots:
                    self.cells[dot.row][dot.col] = dot

    def find_ship(self, row: int, col: int) -> bool:
        for ship in self.ships:
            for dot in ship.dots:
                if (dot.row, dot.col) == (row, col) and \
                        dot.state not in (Dot.DOT_STATES['hit'], Dot.DOT_STATES['dead']):
                    return True
        # - Ship not found
        return False


class Game:

    GAME_DIFFICULTY = {
        'normal': 0,
        'hard': 1
    }

    def __init__(self, difficulty: int = GAME_DIFFICULTY['normal']):
        self.difficulty: int = difficulty
        self.board_size: int = 10
        self.ai_data: list = [False, [0, 0], None]  # --- AI gameplay data
        self.players: tuple = (
            Board(self.board_size),  # - Human board
            Board(self.board_size)  # - AI board
        )

    def __str__(self) -> str:
        # --- output game boards
        top_panel = f'{" " * 10}PLAYER SHIPS {self.players[0].lives}{" " * 26}TARGET SHIPS {self.players[1].lives}\n'
        field = '|0||1||2||3||4||5||6||7||8||9|'
        field = f'{" " * 3}{field}{" " * 10}{field}\n'
        for line in range(self.board_size):
            # --- human board ---
            field += f'|{line}| '
            for cell in self.players[0].cells[line]:
                field += f'{cell}  '
            # --- AI board ---
            field += ' ' * 6 + f'|{line}| '
            for cell in self.players[1].cells[line]:
                field += f'{cell if cell.visible else Dot.DOT_STATES["blank"]}  '
            field += '\n'
        return top_panel + field

    def ai_strike(self):
        # ---
        def normalize(_row, _col):
            _row_normalized, _col_normalized = _row, _col
            if _row < 0:
                _row_normalized = 0
            if _row >= self.board_size:
                _row_normalized = 9
            if _col < 0:
                _col_normalized = 0
            if _col >= self.board_size:
                _col_normalized = 9
            return _row_normalized, _col_normalized

        # ---
        def find_ship_around(saved_row: int, saved_col: int) -> tuple | None:
            # --- find ship top of row, col
            _row, _col = normalize(saved_row - 1, saved_col)
            if self.players[0].find_ship(_row, _col):
                return _row, _col
            # --- find ship left of row, col
            _row, _col = normalize(saved_row, saved_col - 1)
            if self.players[0].find_ship(_row, _col):
                return _row, _col
            # --- find ship right of row, col
            _row, _col = normalize(saved_row, saved_col + 1)
            if self.players[0].find_ship(_row, _col):
                return _row, _col
            # --- find ship bottom of row, col
            _row, _col = normalize(saved_row + 1, saved_col)
            if self.players[0].find_ship(_row, _col):
                return _row, _col
            # ---
            return None

        # --- AI is cheater! ha-ha-ha :-)
        def ai_new_position():
            # --- If last strike is 'hit', find ship part around and strike by found row, col
            if self.ai_data[0]:
                # --- find ship part around as next target dot for AI
                next_dot = find_ship_around(self.ai_data[1][0], self.ai_data[1][1])
                if next_dot is not None:
                    return next_dot
                # --- if nothing found get another chance...
                if self.ai_data[2]:
                    self.ai_data[1] = self.ai_data[2].copy()
                    self.ai_data[2] = None
                    return ai_new_position()
                else:
                    # --- get another chance from random position
                    next_dot = find_ship_around(rnd.randint(0, 9), rnd.randint(0, 9))
                    if next_dot is not None:
                        return next_dot
                    else:
                        # --- or return random
                        return rnd.randint(0, 9), rnd.randint(0, 9)
            # ---
            # --- If last strike is 'miss' or WrongCellSelectedException, strike random
            else:
                if self.difficulty == self.GAME_DIFFICULTY['hard']:
                    # --- get another chance from random position
                    next_dot = find_ship_around(self.ai_data[1][0], self.ai_data[1][1])
                    if next_dot is not None:
                        return next_dot
                    else:
                        # --- or return random
                        return rnd.randint(0, 9), rnd.randint(0, 9)
                else:
                    # --- or return random
                    return rnd.randint(0, 9), rnd.randint(0, 9)
        # ---
        row, col = ai_new_position()
        try:
            result = self.strike(0, row, col)
        except WrongCellSelectedException:
            self.ai_data[0] = False
            self.ai_strike()
        else:
            if result:
                self.ai_data[0] = True
                self.ai_data[1] = [row, col]
                if not self.ai_data[2]:
                    self.ai_data[2] = [row, col]
            else:
                self.ai_data[0] = False
                self.ai_data[1] = [row, col]

    def human_strike(self, row: int, col: int):
        try:
            self.strike(1, row, col)
        except WrongCellSelectedException:
            return False
        else:
            return True

    def strike(self, player: int, row: int, col: int) -> bool:
        # --- check target cell state
        state = self.players[player].cells[row][col].state
        if state in (Dot.DOT_STATES['hit'], Dot.DOT_STATES['dead'], Dot.DOT_STATES['miss']):
            raise WrongCellSelectedException(
                f'Wrong cell selected for target player {player}. Cell {row}:{col} already {state}')
        try:
            target = Dot(row, col)
            for ship in self.players[player].ships:
                for dot in ship.dots:
                    if dot == target:
                        dot.state = Dot.DOT_STATES['hit']
                        if ship.lives > 0:
                            ship.lives -= 1
                        if ship.lives == 0 and self.players[player].lives > 0:
                            self.players[player].lives -= 1
                            for _dot in ship.dots:
                                _dot.state = Dot.DOT_STATES['dead']
                        raise StrikeHitException  # --- hit
            # ---
            self.players[player].cells[row][col].state = Dot.DOT_STATES['miss']
            raise StrikeMissException  # --- miss
        except StrikeHitException:
            return True
        except StrikeMissException:
            return False

    def check_win(self, player: int) -> bool:
        return False if any([ship.lives for ship in self.players[player].ships]) else True


def start():
    def test_game() -> tuple:
        steps = [0, 0]
        while True:
            # --- Human randomly selects cell
            row = rnd.randint(0, 9)
            col = rnd.randint(0, 9)
            steps[0] += 1
            if not game.human_strike(row, col):
                continue
            else:
                if game.check_win(1):
                    return 'Human', steps[0]
            # --- AI selects cell by his gameplay algorithm
            steps[1] += 1
            game.ai_strike()
            if game.check_win(0):
                return 'AI', steps[1]

    msg_step = f'Enter row, col (like 12, 65, etc.) or q - to exit game: '
    msg_hello = f'Welcome to Sea Battle game!\nChoice difficulty level [0-normal, 1-hard]: '

    game_test = False
    # game_test = True

    if game_test:
        game = Game(Game.GAME_DIFFICULTY['normal'])
        # game = Game(Game.GAME_DIFFICULTY['hard'])
        res = test_game()
        print(game)
        print(f'{res[0]} win after {res[1]} steps!!!')

    else:
        # ---
        difficulty = input(msg_hello)
        if difficulty.isdigit():
            difficulty = int(difficulty)
            if difficulty == 0:
                game = Game(Game.GAME_DIFFICULTY['normal'])
            elif difficulty == 1:
                game = Game(Game.GAME_DIFFICULTY['hard'])
            else:
                print(f'Wrong choice - {difficulty}!')
                return
        else:
            print(f'Wrong choice - {difficulty}!')
            return
        # ---
        print(game)
        while True:
            rc = input(msg_step)
            print()
            if rc.isdigit() and len(rc) == 2:
                if not game.human_strike(int(rc[0]), int(rc[1])):
                    print('Wrong cell selected! Try again.')
                    continue
                elif game.check_win(1):
                    print(game)
                    print('Human win!!!')
                    return

                print('AI...')
                time.sleep(1)
                game.ai_strike()
                print(game)
                if game.check_win(0):
                    print('AI win!!!')
                    return
            else:
                if rc and rc[0] == 'q':
                    break
                else:
                    continue


if __name__ == '__main__':
    start()