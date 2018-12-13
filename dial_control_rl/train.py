#!/usr/bin/env python3

import sys
sys.path.append('.')

from lagom.experiment import Configurator
from lagom.experiment import BaseExperimentWorker
from lagom.experiment import BaseExperimentMaster
from lagom.experiment import run_experiment
from lagom.envs import EnvSpec
from lagom.envs import make_vec_env
from lagom.utils import Seeder
from lagom.envs.vec_env import SerialVecEnv, VecStandardize
from lagom.runner import RollingSegmentRunner
from functools import partial

from dial_control_rl.env import CraftingEnv
from dial_control_rl.engine import Engine
from dial_control_rl.agent import Agent


class ExperimentWorker(BaseExperimentWorker):
    def prepare(self):
        pass

    def make_algo(self):
        def algorithm(config, seed, device):
            seeder = Seeder(seed)
            seeds = seeder(size=config['env.count'])
            env_constructors = []
            for seed in seeds:
                env_constructors.append(partial(CraftingEnv, seed))
            env = VecStandardize(SerialVecEnv(env_constructors),
                                 clip_reward=100.0)
            env_spec = EnvSpec(env)

            agent = Agent(config, env_spec, device)
            runner = RollingSegmentRunner(config, agent, env)
            engine = Engine(agent, runner, env)

            for i in range(config['train.iter']):
                training_result = engine.train(i)
                if i % config['log.interval'] == 0:
                    engine.log_train(training_result)

        return algorithm


class ExperimentMaster(BaseExperimentMaster):
    def make_configs(self):
        configurator = Configurator('grid')

        configurator.fixed('cuda', False)

        configurator.fixed('algo.lr', 7e-4)
        configurator.fixed('algo.lr_V', 1e-3)
        configurator.fixed('algo.gamma', 0.99)
        configurator.fixed('algo.gae_lambda', 0.97)
        configurator.fixed('env.count', 20)
        configurator.fixed('agent.count', 20)

        configurator.fixed('agent.standardize_Q', False)
        configurator.fixed('agent.standardize_adv', False)
        configurator.fixed('agent.max_grad_norm', 0.5)
        configurator.fixed('agent.entropy_coef', 0.01)
        configurator.fixed('agent.value_coef', 0.5)
        configurator.fixed('agent.fit_terminal_value', False)
        configurator.fixed('agent.terminal_value_coef', 0.1)

        configurator.fixed('train.iter', 10000)
        configurator.fixed('log.interval', 1000)
        configurator.fixed('log.dir', 'logs')

        return configurator.make_configs()

    def make_seeds(self):
        return [1013845395]

    def process_results(self, results):
        assert all([result is None for result in results])


if __name__ == '__main__':
    run_experiment(worker_class=ExperimentWorker,
                   master_class=ExperimentMaster,
                   num_worker=100)
