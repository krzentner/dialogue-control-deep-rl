#!/usr/bin/env python3

from pycolab import ascii_art
from pycolab import human_ui
from pycolab import things

from enum import IntEnum

import curses

BACKGROUND = [
    ' M  W ',
    ' M  W ',
    ' M  W ',
    ' MBCW ']

MAP_WIDTH = len(BACKGROUND[0])
MAP_HEIGHT = len(BACKGROUND)

MOUNTAIN = 'M'
WATER = 'W'
BENCH = 'B'
CRUCIBLE = 'C'

RUBY = 'R'
GOLD = 'G'
AMETHYST = 'A'
DIAMOND = 'D'
SILVER = 'S'
JADE = 'J'

PLAYER_1 = '1'
PLAYER_2 = '2'

COLOURS = {' ': (128, 255, 0),  # Should look like grass.
           MOUNTAIN: (200, 200, 200),
           WATER: (50, 50, 200),
           BENCH: (50, 50, 50),
           CRUCIBLE: (200, 100, 0),
           RUBY: (255, 0, 0),
           GOLD: (200, 200, 0),
           AMETHYST: (200, 0, 200),
           DIAMOND: (250, 250, 250),
           SILVER: (200, 200, 250),
           JADE: (0, 200, 100),
           PLAYER_1: (200, 150, 150),
           PLAYER_2: (0, 50, 30)}


class Action(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    ITEM1 = 4
    ITEM2 = 5
    ITEM3 = 6


P2_OFF = Action.ITEM3 + 1


def move(x, y, action):
    dx = [0, 0, -1, 1][action]
    dy = [-1, 1, 0, 0][action]
    new_x = x + dx
    new_y = y + dy
    if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
        return (new_x, new_y)
    else:
        return (x, y)


class Player(things.Sprite):

    def __init__(self, corner, position, character):
        super(Player, self).__init__(corner, position, character)
        self._player = int(character)
        self._position = self.Position(1, 1 + self._player)

    def update(self, actions, board, layers, backdrop, all_things, the_plot):
        if actions is None:
            return
        player = int(actions >= P2_OFF)
        action = actions % P2_OFF
        if player != self._player:
            return
        if action <= Action.RIGHT:
            x, y = move(self._position.col, self._position.row, action)
            self._position = self.Position(y, x)


def make_game():
    return ascii_art.ascii_art_to_game(
        BACKGROUND, what_lies_beneath=' ',
        sprites={'1': ascii_art.Partial(Player),
                 '2': ascii_art.Partial(Player)},
        z_order='12')


def main():

    game = make_game()

    ui = human_ui.CursesUi(
        keys_to_actions={
            curses.KEY_UP: Action.UP, curses.KEY_DOWN: Action.DOWN,
            curses.KEY_LEFT: Action.LEFT, curses.KEY_RIGHT: Action.RIGHT, ',':
            Action.ITEM1, '.': Action.ITEM2, '/': Action.ITEM3,
            'w': P2_OFF + Action.UP, 's': P2_OFF + Action.DOWN, 'a': P2_OFF +
            Action.LEFT, 'd': P2_OFF + Action.RIGHT,
            '1': P2_OFF + Action.ITEM1, '2': P2_OFF + Action.ITEM2,
            '3': P2_OFF + Action.ITEM3, },
        delay=50, colour_fg=COLOURS)

    ui.play(game)


if __name__ == '__main__':
    main()
