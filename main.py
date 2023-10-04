from random import randint

from colorama import Fore
from colorama import init

init(autoreset=True)

import time


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"({self.x}, {self.y})"


class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "You're trying to shoot over the board!"


class BoardUsedException(BoardException):
    def __str__(self):
        return "You've already shot at this cage"


class BoardWrongShipException(BoardException):
    pass


class Ship:
    def __init__(self, bow, l, o):
        self.bow = bow
        self.l = l
        self.o = o
        self.lives = l

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.l):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.o == 0:
                cur_x += i

            elif self.o == 1:
                cur_y += i

            ship_dots.append(Dot(cur_x, cur_y))

        return ship_dots

    def shooten(self, shot):
        return shot in self.dots


class Board:
    def __init__(self, hid=False, size=6):
        self.size = size
        self.hid = hid

        self.count = 0

        self.field = [["~"] * size for _ in range(size)]

        self.busy = []
        self.ships = []

    def add_ship(self, ship):
        for d in ship.dots:
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = "□"
            self.busy.append(d)

        self.ships.append(ship)
        self.contour(ship)

    def contour(self, ship, verb=False):
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for d in ship.dots:
            for dx, dy in near:
                cur = Dot(d.x + dx, d.y + dy)
                if not (self.out(cur)) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = "."
                    self.busy.append(cur)

    def __str__(self):
        res = ""
        res += "  | 1 | 2 | 3 | 4 | 5 | 6 |"
        for i, row in enumerate(self.field):
            res += f"\n{i + 1} | " + " | ".join(row) + " |"

        if self.hid:
            res = res.replace("□","~")
        return res

    def out(self, d):
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def shot(self, d):
        if self.out(d):
            raise BoardOutException()

        if d in self.busy:
            raise BoardUsedException()

        self.busy.append(d)

        for ship in self.ships:
            if d in ship.dots:
                ship.lives -= 1
                self.field[d.x][d.y] = "X"
                if ship.lives == 0:
                    self.count += 1
                    self.contour(ship, verb=True)
                    print(f"\033[32m The ship is sunk!")
                    return False
                else:
                    print(f"\033[32m Hit!")
                    return True

        self.field[d.x][d.y] = "."
        print(f"\033[31m Past!")
        return False

    def begin(self):
        self.busy = []


class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy

    def ask(self):
        raise NotImplementedError()

    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                return repeat
            except BoardException as e:
                print(e)


class AI(Player):
    def ask(self):
        d = Dot(randint(0, 5), randint(0, 5))
        print(f"\033[33m Computer progress: {d.x + 1} {d.y + 1}")
        return d


class User(Player):
    def ask(self):
        while True:
            cords = input("\033[35m Your move:").split()

            if len(cords) != 2:
                print(f"\033[31m Enter 2 coordinates! ")
                continue

            x, y = cords

            if not (x.isdigit()) or not (y.isdigit()):
                print(f"\033[31m Enter numbers! ")
                continue

            x, y = int(x), int(y)

            return Dot(x - 1, y - 1)


class Game:
    def __init__(self, size=6):
        self.lens = [3, 2, 2, 1, 1, 1, 1]
        self.size = size
        pl = self.random_board()
        co = self.random_board()
        co.hid = True

        self.ai = AI(co, pl)
        self.us = User(pl, co)

    def random_board(self):
        board = None
        while board is None:
            board = self.random_place()
        return board

    def random_place(self):
        board = Board(size=self.size)
        attempts = 0
        for l in self.lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), l, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    @staticmethod
    def greet():
        print(Fore.BLUE + "-" * 60)
        print(f"{Fore.YELLOW} Welcome to the sea battle game!")
        print(f"{Fore.YELLOW} Input format: x y ")
        print(f"{Fore.YELLOW} x - row number y - column number")
        print()

    @staticmethod
    def fields_parallel(first, second):
        first_sp = first.split("\n")
        second_sp = second.split("\n")
        max_width = max(map(len, first_sp))
        max_len = max(len(first_sp), len(second_sp))
        first_sp += [""] * (max_len - len(first_sp))
        second_sp += [""] * (max_len - len(second_sp))
        text = []
        for f, s in zip(first_sp, second_sp):
            text.append(f"{f: <{max_width}}   |  {s: <{max_width}}")
        return "\n".join(text)

    def loop(self):
        username = input(f"\033[35m Your name: ")
        num = 0
        while True:
            print(Fore.BLUE + "-" * 60)
            user_board = "User board:\n\n" + str(self.us.board)
            ai_board = "Computer board:\n\n" + str(self.ai.board)
            print(self.fields_parallel(user_board, ai_board))

            if num % 2 == 0:
                print(Fore.BLUE + "-" * 60)
                print(f"\033[35m Move: {username}!")
                repeat = self.us.move()
            else:
                print(Fore.BLUE + "-" * 60)
                print("\033[33m The computer is moving...")
                time.sleep(2)
                repeat = self.ai.move()
            if repeat:
                num -= 1

            if self.ai.board.count == 7:
                print(Fore.BLUE + "-" * 60)
                print(f"\033[32m {username} won!")
                break

            if self.us.board.count == 7:
                print(Fore.BLUE + "-" * 60)
                print(f"\033[31m Computer won!")
                break
            num += 1

    def start(self):
        self.greet()
        self.loop()


g = Game()
g.start()
