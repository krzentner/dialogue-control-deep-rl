#!/usr/bin/env python3

import sys
sys.path.append('.')

import numpy as np
import torch
import pickle

params = torch.load('logs-3/0/1013845395/trained_params')

from dial_control_rl import agent
from dial_control_rl.env import CraftingEnv

from lagom.utils import Seeder
from lagom.envs.vec_env import SerialVecEnv, VecStandardize
from lagom.envs import EnvSpec
from functools import partial

env = CraftingEnv()


seeder = Seeder(0)
seeds = seeder(size=1)
env_constructors = []
for seed in seeds:
    env_constructors.append(partial(CraftingEnv, seed))
env = VecStandardize(SerialVecEnv(env_constructors),
                        clip_reward=100.0)
env_spec = EnvSpec(env)

policy = agent.Policy({'algo.rl': 0}, env_spec, torch.device('cpu'))
policy.load_state_dict(params)
policy = policy.double()

def V(x):
    out = policy(torch.tensor(x), ['V'])
    return out['V'][0]

def Q(x):
    out = policy(torch.tensor(x), ['action_dist'])
    out = out['action_dist']
    return out.probs.detach().numpy()

if __name__ == '__main__':
    obs = env.reset()
    print(V(obs))
    print(Q(obs))

