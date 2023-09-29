import random
from collections import deque, namedtuple

import numpy as np
import torch


class ReplayBuffer:
    """The Experience Replay Buffer class. Used to store experiences and allow
    off-policy learning.

    :param n_actions: Action dimension
    :type n_actions: int
    :param memory_size: Maximum length of replay buffer
    :type memory_size: int
    :param field_names: Field names for experience named tuple, e.g. ['state', 'action', 'reward']
    :type field_names: List[str]
    :param device: Device for accelerated computing, 'cpu' or 'cuda', defaults to None
    :type device: str, optional
    """

    def __init__(self, action_dim, memory_size, field_names, device=None):
        self.n_actions = action_dim
        self.memory = deque(maxlen=memory_size)
        self.experience = namedtuple("Experience", field_names=field_names)
        self.counter = 0  # update cycle counter
        self.device = device

    def __len__(self):
        return len(self.memory)

    def _add(self, state, action, reward, next_state, done):
        e = self.experience(state, action, reward, next_state, done)
        self.memory.append(e)

    def sample(self, batch_size):
        """Returns sample of experiences from memory.

        :param batch_size: Number of samples to return
        :type batch_size: int
        """
        experiences = random.sample(self.memory, k=batch_size)

        states = torch.from_numpy(
            np.stack([e.state for e in experiences if e is not None], axis=0)
        )
        actions = torch.from_numpy(
            np.vstack([e.action for e in experiences if e is not None])
        )
        rewards = torch.from_numpy(
            np.vstack([e.reward for e in experiences if e is not None])
        ).float()
        next_states = torch.from_numpy(
            np.stack([e.next_state for e in experiences if e is not None], axis=0)
        ).float()
        dones = torch.from_numpy(
            np.vstack([e.done for e in experiences if e is not None]).astype(np.uint8)
        ).float()

        if self.device is not None:
            states, actions, rewards, next_states, dones = (
                states.to(self.device),
                actions.to(self.device),
                rewards.to(self.device),
                next_states.to(self.device),
                dones.to(self.device),
            )

        return (states, actions, rewards, next_states, dones)

    def save2memorySingleEnv(self, state, action, reward, next_state, done):
        """Saves experience to memory.

        :param state: Environment observation
        :type state: float or List[float]
        :param action: Action in environment
        :type action: float or List[float]
        :param reward: Reward from environment
        :type reward: float
        :param next_state: Environment observation of next state
        :type next_state: float or List[float]
        :param done: True if environment episode finished, else False
        :type done: bool
        """
        self._add(state, action, reward, next_state, done)
        self.counter += 1

    def save2memoryVectEnvs(self, states, actions, rewards, next_states, dones):
        """Saves multiple experiences to memory.

        :param states: Multiple environment observations in a batch
        :type states: List[float] or List[List[float]]
        :param actions: Multiple actions in environment a batch
        :type actions: List[float] or List[List[float]]
        :param rewards: Multiple rewards from environment in a batch
        :type rewards: List[float]
        :param next_states: Multiple environment observations of next states in a batch
        :type next_states: List[float] or List[List[float]]
        :param dones: True if environment episodes finished, else False, in a batch
        :type dones: List[bool]
        """
        for state, action, reward, next_state, done in zip(
            states, actions, rewards, next_states, dones
        ):
            self._add(state, action, reward, next_state, done)
            self.counter += 1


    def save2memory(self, state, action, reward, next_state, done, is_vectorised):
        """Applies appropriate save2memory function depending on whether
        the environment is vectorised or not.

        :param states: Environment observations
        :type states: float, List[float] or List[List[float]]
        :param actions: Environment actions
        :type actions: float, List[float] or List[List[float]]
        :param rewards: Environment rewards
        :type rewards: float or List[float]
        :param next_states: Environment observations for the next state
        :type next_states: float, List[float] or List[List[float]]
        :param dones: True if environment episodes finished, else False
        :type dones: float or List[bool]
        :param is_vectorised: Boolean flag indicating if the environment has been vectorised
        :type is_vectorised: bool
        """
        if is_vectorised:
            self.save2memoryVectEnvs(state, action, reward, next_state, done)
        else:
            self.save2memorySingleEnv(state, action, reward, next_state, done)
            

