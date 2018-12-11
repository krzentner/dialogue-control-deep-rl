from lagom.agents import BaseAgent

from lagom.policies import BasePolicy
from lagom.policies import CategoricalHead

from lagom.value_functions import StateValueHead

import numpy as np

import torch
import torch.optim as optim
import torch.nn as nn


class Policy(BasePolicy):

    def make_networks(self, config):
        input_dim = self.env_spec.observation_space.flat_dim
        feature_dim = 50
        self.featurize = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, feature_dim))
        self.action_head = CategoricalHead(config, self.device, feature_dim,
                                           self.env_spec)
        self.V_head = StateValueHead(config, self.device, feature_dim)

    def make_optimizer(self, config, **kwargs):
        self.optimizer = optim.Adam(self.parameters(), lr=config['algo.lr'])

    def optimizer_step(self, config, **kwargs):
        self.optimizer.step()

    @property
    def recurrent(self):
        return False

    def reset(self, config, **kwargs):
        pass

    def __call__(self, x, out_keys=['action', 'V'], info={}, **kwargs):
        out = {}

        features = self.featurize(x)
        action_dist = self.action_head(features)

        action = action_dist.sample()
        out['action'] = action

        if 'V' in out_keys:
            V = self.V_head(features)
            out['V'] = V
        if 'action_dist' in out_keys:
            out['action_dist'] = action_dist
        if 'action_logprob' in out_keys:
            out['action_logprob'] = action_dist.log_prob(action)
        if 'entropy' in out_keys:
            out['entropy'] = action_dist.entropy()
        if 'perplexity' in out_keys:
            out['perplexity'] = action_dist.perplexity()

        return out


class Agent(BaseAgent):

    def make_modules(self, config):
        self.policy = Policy(config, self.env_spec, self.device)

    def prepare(self, config, **kwargs):
        self.total_T = 0

    def reset(self, config, **kwargs):
        pass

    @property
    def recurrent(self):
        pass

    def choose_action(self, obs, info={}):
        obs = torch.from_numpy(np.asarray(obs)).float().to(self.device)

        if self.training:
            out = self.policy(obs, out_keys=['action', 'action_logprob', 'V',
                                             'entropy'], info=info)
        else:
            with torch.no_grad():
                out = self.policy(obs, out_keys=['action'], info=info)

        if torch.any(torch.isnan(out['action'])):
            raise ValueError('NaN!')

        return out

    def learn(self, D, info={}):
        raise NotImplementedError()
