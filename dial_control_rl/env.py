#!/usr/bin/env python3

import curses
import random
import numpy as np
from enum import IntEnum, unique

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

GEMS = [RUBY, AMETHYST, DIAMOND, JADE, PEARL]
METALS = [SILVER, GOLD]
ITEMS = GEMS + METALS + [COAL]


@unique
class JewelryShape(IntEnum):
    CROWN = 0
    RING = 1
    BRACELET = 2


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

JEWELRY_NAMES = [f'{metal.capitalize()} {shape.capitalize()} with {gem}'
                 for shape in [shape.name.capitalize()
                               for shape in JewelryShape]
                 for metal in ['Silver', 'Gold']
                 for gem in ['Ruby', 'Amethyst', 'Diamond', 'Jade', 'Pearl']]


def jewelry_index(shape, metal, gem):
    return (gem +
            len(GEMS) * metal +
            len(GEMS) * len(METALS) * shape)


MAX_JEWELRY_IDX = jewelry_index(JewelryShape.BRACELET, len(METALS) - 1,
                                len(GEMS) - 1)


GOAL_LEN = (MAX_JEWELRY_IDX + 1) + len(ITEMS)
assert GOAL_LEN == 38
GOAL_REWARD = 100


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
CRUCIBLE_ITEMS = ('crucible_items',)
BENCH_ITEMS = ('bench_items',)


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
        if not the_plot.get(('goal_complete', player), False):
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
                        log(f'Player #{self._player} put {item!r} in '
                            'crucible.')
                        make_crucible_jewelry(self._player, the_plot, item)
                    if thing.character == BENCH:
                        log(f'Player #{self._player} put {item!r} in bench.')
                        make_bench_jewelry(self._player, the_plot, item)
                else:
                    log(f'Player #{self._player} has not item in slot {slot}')
                if not found_thing:
                    # TODO: Handle dropping items.
                    pass


def make_crucible_jewelry(player, the_plot, item):
    items = the_plot.setdefault(CRUCIBLE_ITEMS, [])
    new_items = items + [item]
    if len(new_items) == 3:
        if COAL in new_items:
            make_from(player, the_plot, JewelryShape.CROWN,
                      new_items)
        new_items = new_items[-2:]
    elif len(new_items) == 2:
        make_from(player, the_plot, JewelryShape.RING,
                  new_items)
    the_plot[CRUCIBLE_ITEMS] = new_items


def make_bench_jewelry(player, the_plot, item):
    items = the_plot.setdefault(BENCH_ITEMS, [])
    new_items = items + [item]
    if len(new_items) > 2:
        new_items = new_items[-2:]
    the_plot[BENCH_ITEMS] = new_items
    if len(new_items) == 2:
        make_from(player, the_plot, JewelryShape.BRACELET,
                  new_items)


def make_from(player, the_plot, shape, items):
    metals = get_metals(items)
    gems = get_gems(items)
    if len(metals) == 1 and len(gems) == 1:
        give_reward(player, the_plot, jewelry_index(shape,
                                                    metal_index(metals[0]),
                                                    gem_index(gems[0])))
    else:
        log(f'Cannot make {shape.name.lower()} from {items!r}.')


def get_metals(items):
    return [item for item in items if item in METALS]


def get_gems(items):
    return [item for item in items if item in GEMS]


def metal_index(m):
    return METALS.index(m)


def gem_index(g):
    return GEMS.index(g)


def give_reward(player, the_plot, jewelry_idx):
    for p in (1, 2):
        player_goal = the_plot[('goal', p)]
        reward = player_goal[jewelry_idx] * GOAL_REWARD
        log(f'Giving reward {reward} to Player {p} for '
            f'{JEWELRY_NAMES[jewelry_idx]}.')
        the_plot.add_reward(reward)
        if reward > 0:
            the_plot[('goal_complete', p)] = True


class Item(things.Sprite):

    def update(self, actions, board, layers, backdrop, all_things, the_plot):
        pass


class Place(things.Sprite):

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
    engine = ascii_art.ascii_art_to_game(
        gen_start(),
        what_lies_beneath=' ',
        sprites={
            '1': Player,
            '2': Player,
            RUBY: Item,
            GOLD: Item,
            AMETHYST: Item,
            DIAMOND: Item,
            SILVER: Item,
            JADE: Item,
            COAL: Item,
            PEARL: Item,
            CRUCIBLE: Place,
            BENCH: Place,
            },
        z_order='CBRGADSJOP12')
    for player in (1, 2):
        player_goal = np.zeros(GOAL_LEN)
        player_goal_index = random.randint(0, MAX_JEWELRY_IDX)
        log(f'Giving Player {player} the goal of '
            f'{JEWELRY_NAMES[player_goal_index]}.')
        player_goal[player_goal_index] = 1.0
        engine.the_plot[('goal', player)] = player_goal
    return engine


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
