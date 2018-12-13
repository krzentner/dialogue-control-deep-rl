#!/usr/bin/env python3

import sys
sys.path.append('.')

import numpy as np
from pprint import pprint
from enum import IntEnum, unique
from dial_control_rl import game


def dist(abrev, name):
    return np.array([float(name in n) for n in game.JEWELRY_NAMES] +
                    [float(i == abrev) for i in game.ITEMS])

ABBREVS = [('G', 'Gold'),
     ('S', 'Silver'),
     ('O', 'Coal'),

     ('R', 'Ruby'),
     ('A', 'Amethyst'),
     ('D', 'Diamond'),
     ('J', 'Jade'),
     ('P', 'Pearl'),

     ('B', 'Bracelet'),
     ('C', 'Crown'),
     ('I', 'Ring')]

DISTS = dict([(abrev, dist(abrev, name)) for (abrev, name) in ABBREVS])


@unique
class BackChannelAct(IntEnum):
    NO_PROGRESS = 0
    PROGRESS = 1
    RESET = 2
    REQUEST_CONFIRMATION = 3
    INCONSISTENT_ACT = 4
    DONE = 5


@unique
class ForwardChannelAct(IntEnum):
    PART_OF_GOAL = 0
    NOT_PART_OF_GOAL = 1
    CONFIRM = 2
    DISCONFIRM = 3


@unique
class InferenceState(IntEnum):
    UNCERTAIN = 0
    CONFUSED = 1
    UNCONFIRMED = 2
    CONFIRMED = 3


class GoalInference:

    def __init__(self, certainty_threshold=0.75, update_threshold=0.1):
        self.certainty_threshold = certainty_threshold
        self.update_threshold = update_threshold
        self.full_reset()


    def full_reset(self):
        self.conf_per_goal = np.zeros(game.GOAL_LEN)
        self.conf_not_goal = np.zeros(game.GOAL_LEN)
        self.confirmed = False

    @property
    def net_confidence(self):
        return np.clip(self.conf_per_goal - self.conf_not_goal, 0, 1)

    @property
    def state(self):
        most_likely_goal = np.argmax(self.net_confidence)
        p = np.array(self.net_confidence)
        p[most_likely_goal] = 0.0
        next_most_likely = np.argmax(p)
        conf_most_likely = self.net_confidence[most_likely_goal]
        conf_2nd_likely = self.net_confidence[next_most_likely]
        relative_conf = conf_most_likely - conf_2nd_likely
        if relative_conf > self.certainty_threshold:
            if self.confirmed:
                return InferenceState.CONFIRMED, most_likely_goal
            else:
                return InferenceState.UNCONFIRMED, most_likely_goal
        elif np.min(self.conf_not_goal) > 1 - self.certainty_threshold:
            return InferenceState.CONFUSED, most_likely_goal
        else:
            return InferenceState.UNCERTAIN, most_likely_goal

    def forward_act(self, act, abbrevs, confidences):
        for a in abbrevs:
            assert a in DISTS
        for c in confidences:
            assert c > 0
        assert isinstance(act, ForwardChannelAct)
        assert len(confidences) == len(abbrevs)
        if act == ForwardChannelAct.PART_OF_GOAL:
            original_conf_per_goal = np.array(self.conf_per_goal)
            for a, conf in zip(abbrevs, confidences):
                self.conf_not_goal = np.clip(self.conf_not_goal + conf -
                                             DISTS[a], 0, 1)
                update = conf * DISTS[a] * (1 - self.conf_not_goal)
                self.conf_per_goal = np.clip(self.conf_per_goal + conf *
                                             DISTS[a] + 
                                             (1 - self.conf_not_goal), 0, 1)

            if np.any(self.conf_per_goal - original_conf_per_goal >
                      self.update_threshold):
                return self._progress_made()
            else:
                return BackChannelAct.NO_PROGRESS, None
        elif act == ForwardChannelAct.NOT_PART_OF_GOAL:
            original_conf_not_goal = self.conf_not_goal
            for a, conf in zip(abbrevs, confidences):
                update = conf * DISTS[a]
                new_not_goal = self.conf_not_goal + conf * DISTS[a]
                self.conf_not_goal = np.clip(new_not_goal, 0, 1)
            if np.any(self.conf_not_goal - original_conf_not_goal >
                      self.update_threshold):
                return self._progress_made()
            else:
                return BackChannelAct.NO_PROGRESS, None
        elif act == ForwardChannelAct.CONFIRM:
            if self.state[0] != InferenceState.UNCONFIRMED:
                return BackChannelAct.INCONSISTENT_ACT, None
            else:
                self.confirmed = True
                return BackChannelAct.DONE, self.state[1]
        elif act == ForwardChannelAct.DISCONFIRM:
            self.full_reset()
            return BackChannelAct.RESET, None
        assert False, "Should not be reached."

    def _progress_made(self):
        state, goal = self.state
        if state == InferenceState.UNCONFIRMED:
            return BackChannelAct.REQUEST_CONFIRMATION, goal
        elif state == InferenceState.CONFUSED:
            self.full_reset()
            return BackChannelAct.RESET, None
        else:
            return BackChannelAct.PROGRESS, None

    def goal_name(self, goal):
        return game.JEWELRY_NAMES[goal]


def example_inference_loop():
    inference = GoalInference()
    forward_act_map = {
        'G': ForwardChannelAct.PART_OF_GOAL,
        'N': ForwardChannelAct.NOT_PART_OF_GOAL,
        'C': ForwardChannelAct.CONFIRM,
        'D': ForwardChannelAct.DISCONFIRM,
    }
    print('Please provide act,goal abbreviation pairs:')
    while True:
        print('Input: ', end='', flush=True)
        try:
            i = input()
            if i[0] in 'CD' and len(i) == 1:
                act = i
                abbrevs = []
            else:
                act, abbrevs = i.split(',')
            action = forward_act_map[act]
            print('Inference state before:', inference.state[0])
            back_act, goal = inference.forward_act(action, abbrevs,
                                                   len(abbrevs) * [1.0])
            print('Inference state after:', inference.state[0])
            if back_act == BackChannelAct.NO_PROGRESS:
                print('Of course.')
            elif back_act == BackChannelAct.PROGRESS:
                print('Okay.')
            elif back_act == BackChannelAct.RESET:
                inference.full_reset()
                print("Wait what? Let's start over.")
            elif back_act == BackChannelAct.REQUEST_CONFIRMATION:
                print('Is your goal to create the', inference.goal_name(goal), 
                      '?')
            elif back_act == BackChannelAct.INCONSISTENT_ACT:
                print("I don't understand.")
            elif back_act == BackChannelAct.DONE:
                print("Great! Let's make the", inference.goal_name(goal), "!")
                break
        except Exception as e:
            print('Please provide a dialogue act and goal abbreviation pair.')
            print('For example: "G,C" indicates that your goal is to create a '
                  'crown. Multiple abbreviations can also be used. "G,GCR" '
                  'indicates that you would like to create the gold crown '
                  'with a ruby.')
            print('Valid dialogue acts are:')
            print('G : indicate part of the goal')
            print('N : indicate *not* being part of the goal')
            print('C : confirm the goal')
            print('D : refuse to confirm the goal')
            print('D and C dialogue acts do not require abbreviations.')
            print('Valid abbreviations are:')
            for a, name in ABBREVS:
                print(a, ':', name)
            raise e

if __name__ == '__main__':
    example_inference_loop()
