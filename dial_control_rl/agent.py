from lagom.agents import BaseAgent

from lagom.policies import BasePolicy
from lagom.policies import CategoricalHead

from lagom.transform import ExplainedVariance

from lagom.value_functions import StateValueHead
from lagom.transform import ExpFactorCumSum
from lagom.history.batch_segment import BatchSegment
from lagom.history.metrics import final_state_from_segment
from lagom.history.metrics import terminal_state_from_segment
from lagom.history.metrics import bootstrapped_returns_from_segment
from lagom.history.metrics import gae_from_segment


import numpy as np

import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F


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
        # Only take our half of the transitions from D.
        D2 = BatchSegment(D.env_spec, D.T // 2)
        for t in range(0, D.T, 2):
            t_out = t // 2
            D2.add_observation(t_out, D.numpy_observations[:, t])
            D2.add_action(t_out, D.numpy_actions[:, t])
            D2.add_reward(t_out, D.numpy_rewards[:, t])
            D2.add_done(t_out, D.numpy_dones[:, t])
            D2.add_info([info[t] for info in D.infos])
            D2.add_batch_info(D.batch_info[t])
        D = D2
        # The rest of this is just a2c.

        logprobs = torch.stack([info['action_logprob'] for info in D.batch_infos], 1).squeeze(-1)
        entropies = torch.stack([info['entropy'] for info in D.batch_infos], 1).squeeze(-1)
        all_Vs = torch.stack([info['V'] for info in D.batch_infos], 1).squeeze(-1)
        
        last_states = torch.from_numpy(final_state_from_segment(D)).float().to(self.device)
        with torch.no_grad():
            last_Vs = self.policy(last_states, out_keys=['V'])['V']
        Qs = bootstrapped_returns_from_segment(D, last_Vs, self.config['algo.gamma'])
        Qs = torch.from_numpy(Qs.copy()).float().to(self.device)
        if self.config['agent.standardize_Q']:
            Qs = (Qs - Qs.mean(1, keepdim=True))/(Qs.std(1, keepdim=True) + 1e-8)
        
        As = gae_from_segment(D, all_Vs, last_Vs, self.config['algo.gamma'], self.config['algo.gae_lambda'])
        As = torch.from_numpy(As.copy()).float().to(self.device)
        if self.config['agent.standardize_adv']:
            As = (As - As.mean(1, keepdim=True))/(As.std(1, keepdim=True) + 1e-8)
        
        assert all([x.ndimension() == 2 for x in [logprobs, entropies, all_Vs, Qs, As]])
        
        policy_loss = -logprobs*As
        policy_loss = policy_loss.mean()
        entropy_loss = -entropies
        entropy_loss = entropy_loss.mean()
        value_loss = F.mse_loss(all_Vs, Qs, reduction='none')
        value_loss = value_loss.mean()
        
        entropy_coef = self.config['agent.entropy_coef']
        value_coef = self.config['agent.value_coef']
        loss = policy_loss + value_coef*value_loss + entropy_coef*entropy_loss
        
        if self.config['agent.fit_terminal_value']:
            terminal_states = terminal_state_from_segment(D)
            if terminal_states is not None:
                terminal_states = torch.from_numpy(terminal_states).float().to(self.device)
                terminal_Vs = self.policy(terminal_states, out_keys=['V'])['V']
                terminal_value_loss = F.mse_loss(terminal_Vs, torch.zeros_like(terminal_Vs))
                terminal_value_loss_coef = self.config['agent.terminal_value_coef']
                loss += terminal_value_loss_coef*terminal_value_loss
        
        self.policy.optimizer.zero_grad()
        loss.backward()
        self.policy.optimizer_step(self.config, total_T=self.total_T)
        
        self.total_T += D.total_T
        
        out = {}
        out['loss'] = loss.item()
        out['policy_loss'] = policy_loss.item()
        out['entropy_loss'] = entropy_loss.item()
        out['policy_entropy'] = -entropy_loss.item()
        out['value_loss'] = value_loss.item()
        ev = ExplainedVariance()
        ev = ev(y_true=Qs.detach().cpu().numpy().squeeze(), y_pred=all_Vs.detach().cpu().numpy().squeeze())
        out['explained_variance'] = ev
        
        return out
