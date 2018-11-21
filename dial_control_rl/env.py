#!/usr/bin/env python3

import curses
import random
from enum import IntEnum

from pycolab import ascii_art, human_ui, things

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
COAL = 'O'
PEARL = 'P'

ITEMS = [RUBY, GOLD, AMETHYST, DIAMOND, SILVER, JADE, COAL, PEARL]

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


PLAYING = False


def clear_log():
    with open('dial_control.log', 'w'):
        pass


def log(msg):
    if PLAYING:
        with open('dial_control.log', 'a') as f:
            f.write(msg)
            f.write('\n')


class Action(IntEnum):
    SKIP = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    ITEM1 = 5
    ITEM2 = 6
    ITEM3 = 7
    QUIT = 8


P2_OFF = Action.ITEM3 + 1


def move(x, y, direction):
    dx = [0, 0, -1, 1][direction]
    dy = [-1, 1, 0, 0][direction]
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

    def update(self, actions, board, layers, backdrop, all_things, the_plot):
        if actions == Action.QUIT:
            the_plot.terminate_episode()
        if actions is None:
            return
        player = 1 + int(actions >= P2_OFF)
        action = actions % P2_OFF
        if player != self._player:
            return
        the_plot.add_reward(-1)
        if action != Action.SKIP:
            the_plot.add_reward(-1)
        if Action.UP <= action <= Action.RIGHT:
            self.update_move(action)
        if Action.ITEM1 <= action <= Action.ITEM3:
            self.update_item(action, all_things, the_plot)

    def update_move(self, action):
        x, y = move(self._position.col, self._position.row,
                    action - Action.UP)
        self._position = self.Position(y, x)

    def update_item(self, action, all_things, the_plot):
        slot = action - Action.ITEM1
        found_thing = False
        for c, thing in all_things.items():
            if thing.position == self.position:
                if c in ITEMS:
                    log(f'Player #{self._player} picked up {c!r} to {slot}.')
                    the_plot[('inv', self._player, slot)] = thing.character
                    found_thing = True
                item = the_plot.get(('inv', self._player, slot), None)
                if item is not None:
                    found_thing = True
                    if thing.character == CRUCIBLE:
                        log(f'Player #{self._player} put {c!r} in crucible.')
                        items = the_plot.setdefault('crucible_items', [])
                        items.append(item)
                        make_crucible_jewelry(self._player, items, the_plot)
                    if thing.character == BENCH:
                        log(f'Player #{self._player} put {c!r} in bench.')
                        items = the_plot.setdefault('bench_items', [])
                        items.append(item)
                        make_bench_jewelry(self._player, items, the_plot)
                if not found_thing:
                    # TODO: Handle dropping items.
                    pass


def make_crucible_jewelry(player, items, the_plot):
    raise Exception(items)


def make_bench_jewelry(player, items, the_plot):
    raise Exception(items)


class Item(things.Sprite):

    def update(self, actions, board, layers, backdrop, all_things, the_plot):
        pass


def gen_start():
    items_copy = list(ITEMS)
    background_copy = [list(row) for row in BACKGROUND]
    background_copy[0][2] = '1'
    background_copy[0][3] = '2'
    random.shuffle(items_copy)
    for index, item in enumerate(items_copy):
        if index < 4:
            background_copy[index][0] = item
        else:
            background_copy[index - 4][5] = item
    return [''.join(row) for row in background_copy]


def make_game():
    return ascii_art.ascii_art_to_game(
        gen_start(),
        what_lies_beneath=' ',
        sprites={
            '1': ascii_art.Partial(Player),
            '2': ascii_art.Partial(Player),
            RUBY: Item,
            GOLD: Item,
            AMETHYST: Item,
            DIAMOND: Item,
            SILVER: Item,
            JADE: Item,
            COAL: Item,
            PEARL: Item,
            },
        z_order='RGADSJOP12')


def main():

    global PLAYING
    PLAYING = True
    clear_log()

    game = make_game()

    ui = human_ui.CursesUi(
        keys_to_actions={
            ' ': Action.SKIP,
            curses.KEY_UP: Action.UP,
            curses.KEY_DOWN: Action.DOWN,
            curses.KEY_LEFT: Action.LEFT,
            curses.KEY_RIGHT: Action.RIGHT,
            ',': Action.ITEM1,
            '.': Action.ITEM2,
            '/': Action.ITEM3,

            'e': P2_OFF + Action.SKIP,
            'w': P2_OFF + Action.UP,
            's': P2_OFF + Action.DOWN,
            'a': P2_OFF + Action.LEFT,
            'd': P2_OFF + Action.RIGHT,
            '1': P2_OFF + Action.ITEM1,
            '2': P2_OFF + Action.ITEM2,
            '3': P2_OFF + Action.ITEM3,

            'q': Action.QUIT,
            curses.KEY_EXIT: Action.QUIT,
        },
        delay=50, colour_fg=COLOURS)

    ui.play(game)


if __name__ == '__main__':
    main()
