from envs import REGISTRY as env_REGISTRY
from functools import partial
import numpy as np




from components.episode_buffer import EpisodeBatch
from agent_framework.utils import translator, connector
from agent_framework.high_commander import LLMCommander
from agent_framework.low_implementer import LowImplementer



class AgentRunner:

    def __init__(self, args, logger, save_dir=None):
        self.args = args
        self.logger = logger
        self.batch_size = self.args.batch_size_run
        assert self.batch_size == 1

        

        self.env = env_REGISTRY[self.args.env](**self.args.env_args)
        self.episode_limit = self.env.episode_limit
        self.t = 0

        self.t_env = 0

        self.train_returns = {"reward": [], "delta_enemy": [], "delta_deaths": [], "delta_ally": []}
        self.test_returns = {"reward": [], "delta_enemy": [], "delta_deaths": [], "delta_ally": []}
        self.train_stats = {}
        self.test_stats = {}

        '''######################################################
        Initialize agent framework components
        '''
        self.llm_commander = LLMCommander(self.args, save_dir=save_dir)
        self.llm_freq = self.args.llm_freq
        self.low_implementer = LowImplementer(self.args)
        '''######################################################'''


    def save_replay(self):
        self.env.save_replay()

    def close_env(self):
        self.env.close()

    def reset(self):
        self.batch = self.new_batch()
        self.env.reset()
        self.t = 0

    def run(self):
        self.reset()

        terminated = False
        episode_return = {"reward": 0, "delta_enemy": 0, "delta_deaths": 0, "delta_ally": 0}
        while not terminated:

            avail_actions = self.env.get_avail_actions()
            env_obs = self.env.get_obs()

            if self.t % self.llm_freq == 0:
                print(f"AgentRunner.run: Step {self.t} - Querying LLMCommander")
                llm_obs = translator(env_obs)
                llm_response = self.llm_commander.process_observations(llm_obs)
                llm_strategy = connector(llm_response)
                # learn from LLM response, record high-level strategy
                self.low_implementer.read_llm_response(llm_response)
            else:
                print(f"AgentRunner.run: Step {self.t} - Using previous LLM strategy")


            actions = self.low_implementer.take_actions(llm_strategy)

            reward, terminated, env_info = self.env.step(actions[0])
            reward, delta_enemy, delta_deaths, delta_ally = reward
            episode_return["reward"] += reward
            episode_return["delta_enemy"] += delta_enemy
            episode_return["delta_deaths"] += delta_deaths
            episode_return["delta_ally"] += delta_ally

            self.t += 1

        # log episode statistics
        print(f"AgentRunner.run: Episode completed in {self.t} steps. Logging statistics.")
        print(f"Episode Return: {episode_return}")
        print(f"reward: {episode_return['reward']}, delta_enemy: {episode_return['delta_enemy']}, delta_deaths: {episode_return['delta_deaths']}, delta_ally: {episode_return['delta_ally']}")
        battle_result = env_info.get("battle_result", 0)
        if battle_result == True:
            print("Battle Result: Victory")
        elif battle_result == False:
            print("Battle Result: Defeat")

        return battle_result, episode_return

