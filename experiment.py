import torch
import sys, os
import datetime
sys.path.insert(0, os.path.abspath('..'))
import torch_rl.policies as policies
import torch.optim as optim
from torch_rl.learners import TFLog as Log
import torch_rl.learners as learners
import torch_rl.core as core
from torch_rl.tools import rl_evaluate_policy, rl_evaluate_policy_multiple_times
from torch_rl.policies import DiscreteModelPolicy
from gym.spaces import Discrete
from model_zoo import *
from constants import ExperimentConstants as C
from constants import MazeConstants as MC
import numpy as np

class Experiment:
    def __init__(self, policy, optimizer, envs, epsilon=None, n_train_steps=10000, eval_freq=10, save_freq=100, num_observations=1, args=None):

        self.envs = envs
        self.policy = policy
        self.optimizer = optimizer
        self.n_train_steps = n_train_steps
        self.eval_freq = eval_freq
        self.save_freq = save_freq
        self.epsilon = epsilon
        self.num_observations = num_observations
        self.args = args
        self.training_actions = [a for a in range(policy.action_space.n)]
        self.evaluation_actions = [a for a in range(MC.NUM_BASIC_ACTIONS)]
        self.do_admin()

    def do_admin(self):
        # make the log directory
        dt = datetime.datetime.now()
        self.unique_id = '{}-{}___{:02d}-{:02d}-{:02d}-{}-{}'.format(dt.strftime("%b"), dt.day, dt.hour, dt.minute, dt.second, self.envs[0].__class__.__name__, self.policy.action_model.neural_net.model_type)
        self.experiment_dir = os.path.join(C.WORKING_DIR, 'experiments', self.unique_id)
        self.model_file = os.path.join(self.experiment_dir, self.unique_id + '.ckpt')
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)
        self.log_file = os.path.join(self.experiment_dir, self.unique_id + ".log")
        self.log = Log(self.experiment_dir)
        torch.save(self.log.learner_log, self.log_file)

        # write the settings to log
        def write_and_log(k, v, f, log):
            f.write("{}: {}\n".format(k, v))
            log.add_static_value(k, v)
        log = self.log
        with open(os.path.join(self.experiment_dir,'settings.txt'), 'w') as f:
            f.write("####### EXPERIMENT PARAMETERS #######\n\n")
            write_and_log("eval_freq", self.eval_freq, f, log)
            write_and_log("save_freq", self.save_freq, f, log)
            write_and_log("model_file", self.model_file, f, log)
            write_and_log('optimizer', self.optimizer, f, log)
            write_and_log('num_observations', self.num_observations, f, log)
            write_and_log("env_name", self.envs[0].__class__.__name__, f, log)
            #for idx, friend in enumerate(self.envs[0].friends):
            #    write_and_log("Friend{}".format(idx + 1), friend.action_model.filename, f, log)
            for k, v in vars(self.args).items():
                write_and_log(k, v, f, log)

            f.write("\n####### POLICY #######\n\n")
            for k, v in self.policy.info.items():
                write_and_log('policy_'+k, v, f, log)
            write_and_log("action_model", self.policy.action_model, f, log)
            write_and_log("baseline_model", self.policy.baseline_model, f, log)

            f.write("\n####### MAZE #######\n\n")
            for k, v in self.envs[0].world.maze.maze_dict.items():
                write_and_log(k, v, f, log)

            f.write("\n####### REWARDS #######\n\n")
            for k, v in self.envs[0].reward.reward_dict.items():
                write_and_log(k, v, f, log)

            f.write("\n####### SENSORS #######\n\n")
            if self.envs[0].world.agent.sensors is None:
                write_and_log("Sensors", "none", f, log)
            else:
                for idx, sensor in enumerate(self.envs[0].world.agent.sensors):
                    write_and_log(idx, sensor.name, f, log)

            f.write("\n####### TRAINING CONSTANTS #######\n\n")
            garbage = ['__qualname__', 'COLLECTED_CONSTANTS', '__module__']
            for k, v in C.COLLECTED_CONSTANTS.items():
                if k not in garbage:
                    write_and_log(k, v, f, log)


    def print_train(self):
        out_str = 'Training statistics:\n'
        out_str += "Reward = {:.4f} (length = {})".format(self.log.get_last_dynamic_value("avg_total_reward"),self.log.get_last_dynamic_value("avg_length"))
        if self.args.debug:
            out_str += "\nQuery percentage: {}".format(self.log.get_last_dynamic_value("avg_queries"))

        if self.policy.baseline_model is not None:
            out_str += "\nBaseline loss = {}".format(self.log.get_last_dynamic_value("baseline_loss"))
        action_breakdown = self.log.get_last_dynamic_value("action_breakdown", eval_mode=False)
        for idx, value in enumerate(action_breakdown):
            out_str += "\nAction {} percentage: {}".format(idx, value)
        out_str += '\n'
        print(out_str)

    def print_eval(self, step):
        out_str = "Evaluation after {} training episodes\nAvg reward = {}".format((step) * len(self.envs), self.log.get_last_dynamic_value("avg_total_reward", eval_mode=True))
        action_breakdown = self.log.get_last_dynamic_value("action_breakdown", eval_mode=True)
        for idx, value in enumerate(action_breakdown):
            out_str += "\nAction {} percentage: {}".format(idx, value)
        out_str += '\n'
        print(out_str)

    def save_everything(self):
        torch.save(self.log.learner_log, self.log_file)
        torch.save(self.policy.action_model.neural_net, self.model_file)
        print("Saved model checkpoint to {}\n".format(self.model_file))

    def kill(self):
        import shutil
        shutil.rmtree(self.experiment_dir)

    def train(self, step, learning_algorithm):
        self.policy.train_mode(max(1, C.TRAIN_TEMPERATURE ** (1 - (step / self.n_train_steps))), self.training_actions)
        learning_algorithm.step(envs=self.envs,discount_factor=0.95,maximum_episode_length=C.EPISODE_LENGTH)
        if step % self.eval_freq == 0:
            self.print_train()
        if step > 0:
            self.log.log()

    def evaluate(self, step, learning_algorithm):
        self.policy.eval_mode(1, self.evaluation_actions)
        _=rl_evaluate_policy_multiple_times(self.envs[0],self.log,self.policy,C.EPISODE_LENGTH,1.0,10)
        self.print_eval(step)
        if step > 0:
            self.log.log(eval_mode=True)

    def run(self):
        learning_algorithm=learners.LearnerBatchPolicyGradient(
                                action_space=self.envs[0].action_space,
                                log=self.log,
                                average_reward_window=10,
                                policy=self.policy,
                                optimizer=self.optimizer,
                                epsilon=self.epsilon,
                                num_observations=self.num_observations,
                                args=self.args)
        learning_algorithm.reset()

        for step in range(0, self.n_train_steps):
            self.train(step, learning_algorithm)
            if step % self.eval_freq == 0:
                self.evaluate(step, learning_algorithm)
            if step % self.save_freq == 0:
                self.save_everything()
            if step == 0:
                self.log.create_summaries()

        self.save_everything()
        print("Finished training!")
