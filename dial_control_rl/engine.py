from lagom.runner import EpisodeRunner
from lagom.engine import BaseEngine


class Engine(BaseEngine):
    def train(self, n):
        self.agent.train()
        T = int(self.runner.env.T)
        D = self.runner(T)

        out_agent = self.agent.learn(D)
        train_output = {}
        train_output['D'] = D
        train_output['out_agent'] = out_agent
        train_output['n'] = n
        return train_output

    def log_train(self, train_output, **kwargs):
        pass

    def eval(self, n):
        self.agent.eval()
        eval_runner = EpisodeRunner(self.config, self.agent, self.eval_env)
        T = self.eval_env.T
        D = eval_runner(T)

        eval_output = {}
        eval_output['D'] = D
        eval_output['n'] = n
        eval_output['T'] = T

        return eval_output

    def log_eval(self, eval_output, **kwargs):
        pass
