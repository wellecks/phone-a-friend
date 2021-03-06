import sys, os
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../..'))
try:
    from .maze import *
    from .utils import tensor_from_list
except ImportError:
    from maze import *
    from utils import tensor_from_list
import torch

from constants import MazeConstants as C

class Basic(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class NoWalls(MazeEnv):
    def __init__(self, **kwargs):
        walls = tensor_from_list([
        [1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1]]
        ).float()

        exits = torch.zeros(walls.size()).float()
        exits[6, 3] = 1

        apples = torch.zeros(walls.size()).float()
        apples[6, 1] = 1
        #apples[2, 5] = 1

        oranges = torch.zeros(walls.size()).float()
        #oranges[5, 1] = 1

        pears = torch.zeros(walls.size()).float()
        #pears[4, 3] = 1
        #pears[4, 4] = 1
        maze_dict = {
        'walls' : walls,
        'apples' : apples,
        'exits' : exits,
        'pears' : pears,
        'oranges': oranges
        }
        super().__init__(maze_dict=maze_dict, **kwargs)


class OneApple(MazeEnv):
    def __init__(self, **kwargs):
        apples = torch.zeros(C.WALLS.size()).float()
        apples[2, 5] = 1
        maze_dict = {
        'apples': apples
        }

        super().__init__(maze_dict=maze_dict, **kwargs)


class ApplesEverywhere(MazeEnv):
    def __init__(self, **kwargs):
        apples = torch.ones(C.WALLS.size()) - C.WALLS
        maze_dict = {
        'apples': apples
        }

        super().__init__(maze_dict=maze_dict, **kwargs)


class NavigateOnly(MazeEnv):
    def __init__(self, **kwargs):
        exits = torch.zeros(C.WALLS.size()).float()
        apples = torch.zeros(C.WALLS.size()).float()
        oranges = torch.zeros(C.WALLS.size()).float()
        pears = torch.zeros(C.WALLS.size()).float()
        maze_dict = {
        'apples': apples,
        'oranges': oranges,
        'pears':pears,
        'exits': exits
        }

        super().__init__(maze_dict=maze_dict, **kwargs)


class RandomFruit(MazeEnv):
    def __init__(self, random_items=[1, 1, 1], **kwargs):
        maze_dict = {
        'random_items': random_items
        }
        super().__init__(maze_dict=maze_dict, **kwargs)


class RandomApple(RandomFruit):
    def __init__(self, **kwargs):
        random_items=[1, 0, 0]
        super().__init__(random_items=random_items, **kwargs)


class RandomOrange(RandomFruit):
    def __init__(self, **kwargs):
        random_items=[0, 1, 0]
        super().__init__(random_items=random_items, **kwargs)


class RandomPear(RandomFruit):
    def __init__(self, **kwargs):
        random_items=[0, 0, 1]
        super().__init__(random_items=random_items, **kwargs)


class InfiniteApples(MazeEnv):
    def __init__(self, **kwargs):
        random_items=[1, 0, 0]
        maze_dict = {
        'random_items': random_items,
        'regenerate' : True
        }
        super().__init__(maze_dict=maze_dict, **kwargs)

class RandomRewards(MazeEnv):
    def __init__(self, **kwargs):
        random_items=[1, 1, 1]
        maze_dict = {
        'random_items': random_items,
        'regenerate':True
        }
        reward_dict = {
        'apple':0,
        'orange':0,
        'pear':0,
        'reward_std': 5.0
        }
        super().__init__(maze_dict=maze_dict, reward_dict=reward_dict, **kwargs)


class DoubleRandomPear(MazeEnv):
    def __init__(self, **kwargs):
        random_items=[0, 0, 1]
        maze_dict = {
        'random_items': random_items,
        'regenerate':True
        }
        reward_dict = {
        'apple':0,
        'orange':0,
        'pear':0,
        'reward_std': 5.0
        }
        super().__init__(maze_dict=maze_dict, reward_dict=reward_dict, **kwargs)


class DoubleRandomPearWithSensor(DoubleRandomPear):
    def __init__(self, **kwargs):
        sensors_ = [s for s in kwargs.pop('sensors', [])]
        for key in ['pear']:
            reward_sensor = RewardSensor(key)
            sensors_.append(reward_sensor)
        super().__init__(sensors=sensors_, **kwargs)


class RandomRewardsWithSensors(RandomRewards):
    def __init__(self, **kwargs):
        sensors_ = [s for s in kwargs.pop('sensors', [])]
        for key in ['apple', 'orange', 'pear']:
            reward_sensor = RewardSensor(key)
            sensors_.append(reward_sensor)
        super().__init__(sensors=sensors_, **kwargs)

class DoubleRandomPearWithPolicySensor(DoubleRandomPear):
    def __init__(self, **kwargs):
        sensors_ = [s for s in kwargs.pop('sensors', [])]
        for key in ['pear']:
            reward_sensor = RewardSensor(key)
            sensors_.append(reward_sensor)
        sensors_.append(PolicySensor('Mar-16___13-35-40-RandomPear-recurrent'))
        super().__init__(sensors=sensors_, **kwargs)
