"""
Training script
"""

import gym
import config
from dqn_agent import DqnAgent
from replay_buffer import DqnReplayBuffer
from utils import compute_avg_reward, collect_episode
from visualizer import get_training_visualizer


# pylint: disable=too-many-arguments,too-many-locals
def train_model(
        num_iterations=config.DEFAULT_NUM_ITERATIONS,
        batch_size=config.DEFAULT_BATCH_SIZE,
        max_replay_history=config.DEFAULT_MAX_REPLAY_HISTORY,
        gamma=config.DEFAULT_GAMMA,
        eval_eps=config.DEFAULT_EVAL_EPS,
        learning_rate=config.DEFAULT_LEARNING_RATE,
        checkpoint_location=config.DEFAULT_CHECKPOINT_LOCATION,
        model_location=config.DEAFULT_MODEL_LOCATION,
        verbose='progress',
        visualizer_type='none',
        render=False,
        persist_progress=True,
):
    """
    Trains a DQN agent by playing episodes of the Cart Pole game

    :param num_iterations: the number of episodes the agent will play
    :param batch_size: the training batch size
    :param max_replay_history: the limit of the replay buffer length
    :param gamma: discount rate
    :param eval_eps: the number of episode per evaluation
    :param learning_rate: the learning rate of the back propagation
    :param checkpoint_location: the location to save the training checkpoints
    :param model_location: the location to save the pre-trained models
    :param verbose: the verbosity level which can be progress, loss, policy and init
    :param visualizer_type: the type of visualization to be used
    :param render: if the game play should be rendered
    :param persist_progress: if the training progress should be saved

    :return: (maximum average reward, baseline average reward)
    """
    env_name = config.DEFAULT_ENV_NAME
    train_env = gym.make(env_name)
    eval_env = gym.make(env_name)
    agent = DqnAgent(state_space=train_env.observation_space.shape[0],
                     action_space=train_env.action_space.n,
                     gamma=gamma, verbose=verbose, lr=learning_rate,
                     checkpoint_location=checkpoint_location,
                     model_location=model_location,
                     persist_progress=persist_progress)
    benchmark_reward = compute_avg_reward(eval_env, agent.random_policy,
                                          eval_eps)
    buffer = DqnReplayBuffer(max_size=max_replay_history)
    max_avg_reward = 0.0
    visualizer = get_training_visualizer(visualizer_type=visualizer_type)
    for eps_cnt in range(num_iterations):
        collect_episode(train_env, agent.policy, buffer, render)
        if buffer.can_sample_batch(batch_size):
            state_batch, next_state_batch, action_batch, reward_batch, done_batch = \
                buffer.sample_batch(batch_size=batch_size)
            loss = agent.train(state_batch=state_batch,
                               next_state_batch=next_state_batch,
                               action_batch=action_batch,
                               reward_batch=reward_batch, done_batch=done_batch,
                               batch_size=batch_size)
            visualizer.log_loss(loss=loss)
            avg_reward = compute_avg_reward(eval_env, agent.policy, eval_eps)
            visualizer.log_reward(reward=[avg_reward])
            if avg_reward > max_avg_reward:
                max_avg_reward = avg_reward
                if persist_progress:
                    agent.save_model()
            if verbose != 'none':
                print(
                    'Episode {0}/{1}({2}%) finished with avg reward {3} w/ benchmark reward {4}'
                    ' and buffer volume {5}'.format(
                        eps_cnt, num_iterations,
                        round(eps_cnt / num_iterations * 100.0, 2),
                        avg_reward, benchmark_reward, buffer.get_volume()))
        else:
            if verbose != 'none':
                print('Not enough sample, skipping...')
    train_env.close()
    eval_env.close()
    return max_avg_reward, benchmark_reward
