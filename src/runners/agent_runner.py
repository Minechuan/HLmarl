from envs import REGISTRY as env_REGISTRY
from functools import partial
import numpy as np
from openai import OpenAI
from termcolor import cprint
import textwrap

'''AgentRunner for Agent Framework with LLM integration'''
import types
import re
from components.agent_framework import CommanderContext
from components.agent_framework import LowImplementer
from components.llm_prompt import get_initial_prompt, get_subsequent_prompt
import logging


for logger_name in ["httpx", "httpcore", "urllib3"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)
    logger.propagate = False


class AgentRunner:

    def __init__(self, args):
        self.args = args
        self.batch_size = self.args.batch_size_run
        assert self.batch_size == 1

        self.events = self.args.llm_events
        self.current_event_idx = 0
        print(f"AgentRunner: Loaded {len(self.events)} events for this episode.")
        
        self.chat_history = []  # 用于存储与 LLM 的对话历史
        

        self.env = env_REGISTRY[self.args.env](**self.args.env_args)
        self.episode_limit = self.env.episode_limit
        self.t = 0

        self.t_env = 0

        self.train_returns = {"reward": [], "delta_enemy": [], "delta_deaths": [], "delta_ally": []}
        self.test_returns = {"reward": [], "delta_enemy": [], "delta_deaths": [], "delta_ally": []}


        '''######################################################
        Initialize agent framework components
        CommanderContext: 用于存储跨阶段的全局变量 '''
        self.commander = CommanderContext()
        self.low_implementer = LowImplementer(self.args, self.env)



        self.llm_output_path = self.args.llm_output_path
        if self.llm_output_path is not None:
            print(f"AgentRunner: LLM output code will be saved to {self.llm_output_path}")
        self.current_policy_func = None  # 当前阶段的策略函数

    def get_llm_prompt(self, obs):
        # 提取 obs 结构示例 (只取第一层结构做展示，避免 token 爆炸)
        # 实际使用时，obs_example 可以是空的，或者精简版
        victory = self.args.llm_victory_condition
        
        if self.current_event_idx == 0:
            return get_initial_prompt(
                self.events, 
                self.current_event_idx, 
                victory, 
                obs
            )
        else:
            # 获取当前 self.commander 里已经有哪些变量了，提示 LLM
            existing_keys = list(self.commander.__dict__.keys())
            return get_subsequent_prompt(
                self.events, 
                self.current_event_idx, 
                victory, 
                existing_keys,
                obs
            )

    def call_llm_generate_policy(self, obs):
        """
        Call LLM to generate policy code for the current event, parse it, and bind it to self.current_policy_func
        """
        print(f"\n[System]: Generating Policy for Event {self.current_event_idx}...")
        
        if self.args.llm_mock:
            print("[System]: Using mock LLM response for testing.")
            llm_output_code = self._mock_llm_response(self.current_event_idx, obs)
        else:
            prompt = self.get_llm_prompt(obs)
            # === LLM API 调用 ===
            MY_API_KEY = self.args.llm_api_key
            MY_BASE_URL = self.args.llm_url

            client = OpenAI(
                api_key=MY_API_KEY,
                base_url=MY_BASE_URL
            )
            MODEL_NAME = self.args.llm_model_name

            # === 将当前轮 prompt 加入对话历史 ===
            self.chat_history.append({
                "role": "user",
                "call_id": f"event_{self.current_event_idx}",
                "content": prompt
            })
            cprint("Sending prompt to LLM...", "cyan")
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=self.chat_history,
                stream=False,
                reasoning_effort="high",
                temperature=self.args.llm_temperature
            )
            cprint("LLM response received.", "cyan")
            llm_output_code = response.choices[0].message.content

            # === 将 LLM 回复也加入历史 ===
            self.chat_history.append({
                "role": "assistant",
                "call_id": f"event_{self.current_event_idx}",
                "content": llm_output_code
            })

            # print("===============================================")
            # print("LLM Output Code:")
            # print(llm_output_code)
            # print("===============================================")

            if self.llm_output_path is not None:
                with open(self.llm_output_path, "a") as f:
                    f.write(f"\n\n# Event {self.current_event_idx} Response:\n")
                    f.write(llm_output_code)
                    f.write("\n")
        # ===============================================

        # 清洗代码 (去掉 ```python 等)
        code_clean = self._clean_code(llm_output_code)

        
        try:
            # 1. 创建局部作用域，执行代码定义函数
            local_scope = {}
            exec(code_clean, globals(), local_scope)
            
            # 2. 获取函数对象
            func_obj = local_scope.get('execute')
            if not func_obj:
                raise ValueError("LLM did not define a function named 'execute'")
            
            # 3. Bind the function to commander context
            # 这样函数内部的 'self' 就指向了 self.commander，可以访问全局变量
            self.current_policy_func = types.MethodType(func_obj, self.commander)
            
            print(f"[System]: Policy successfully loaded for Phase {self.current_event_idx}.")
            
        except Exception as e:
            print(f"[Error]: Failed to parse LLM code: {e}")
                # 这里可以添加 Retry 机制

    def save_replay(self):
        self.env.save_replay()

    def close_env(self):
        self.env.close()

    def reset(self):
        self.env.reset()
        self.t = 0

    def run(self):
        self.reset()

        terminated = False
        episode_return = {"reward": 0, "delta_enemy": 0, "delta_deaths": 0, "delta_ally": 0}
        

        # Initialize Commander
        llm_info_dict = self.env.get_llm_info_dict()
        self.call_llm_generate_policy(llm_info_dict)
        high_action_list = []
        
        
        while not terminated:
            # Get llm info from env
            
            high_action, trigger = self.current_policy_func(llm_info_dict)
            # print(f"[DEBUG] AgentRunner.run: Step {self.t}, current_event_idx: {self.current_event_idx}")
            # print(f"[DEBUG] High-level action: {high_action}, Trigger: {trigger}")
            # print(f"NydusNetwork available actions: {llm_info_dict['ally'][1]['available_actions']}")
            # print(f"NydusCanalLoad available actions: {llm_info_dict['ally'][15]['available_actions']}")
            # 计算所有 agent 到地方 基地的平均距离
            

            '''[DEBUG] 每 10 步打印一次 bait_id 和各单位到敌方 CommandCenter 的距离'''
            if self.t % 10 == 0:
                bait_id = self.commander.bait_id
                print(f"[System]: Initial bait_id is {bait_id}")
                print("Agents load by NydusNetwork",self.env.load.keys())
                for i, v in llm_info_dict['enemy'].items():
                    if v['unit_type'] == 'CommandCenter':
                        coord = v['coords']
                dist_dict = {}
                for i, v in llm_info_dict['ally'].items():
                    dist = self.commander.get_distance(v['coords'], coord)
                    dist_dict[i] = round(dist,1)
                print ("Distance:", dist_dict)
                print(high_action[bait_id])


            high_action_list.append(high_action)
            if trigger:
                print(f"\n[Trigger Met]: Moving to next phase!")
                self.current_event_idx += 1
                if self.current_event_idx < len(self.events):
                    
                    self.call_llm_generate_policy(llm_info_dict)
                    high_action, trigger = self.current_policy_func(llm_info_dict)
                    high_action_list.append(high_action)
                else:
                    print("[System]: All events completed. Maintaining last policy.")
            # Take low-level actions
            actions = self.low_implementer.take_actions(high_action)
            reward, terminated, env_info = self.env.step(actions)
            reward, delta_enemy, delta_deaths, delta_ally = reward
            episode_return["reward"] += reward
            episode_return["delta_enemy"] += delta_enemy
            episode_return["delta_deaths"] += delta_deaths
            episode_return["delta_ally"] += delta_ally

            self.t += 1
            # get llm info for next step
            llm_info_dict = self.env.get_llm_info_dict()

        # log episode statistics
        print(f"AgentRunner.run: Episode completed in {self.t} steps. Logging statistics.")
        print(f"Episode Return: {episode_return}")
        print(f"reward: {episode_return['reward']}, delta_enemy: {episode_return['delta_enemy']}, delta_deaths: {episode_return['delta_deaths']}, delta_ally: {episode_return['delta_ally']}")
        battle_result = env_info.get("battle_result", 0)
        if battle_result == True:
            print("Battle Result: Victory")
        elif battle_result == False:
            print("Battle Result: Defeat")

        # close the env
        
        return battle_result, episode_return

    def _clean_code(self, code):
        match = re.search(r"```python(.*?)```", code, re.DOTALL)
        if match:
            code = match.group(1)
        # 关键：统一去掉公共缩进
        return textwrap.dedent(code).strip()

    def _mock_llm_response(self, idx, obs):
        if idx == 0:
            return """
def execute(self, obs):
    if not hasattr(self, 'init_done'):
        self.init_done = True
        self.bait_id = None
        self.nydus_id = None
        self.bait_start_health = 0
        
        # Find Nydus Network
        for uid, unit in obs['ally'].items():
            if unit['unit_type'] == 'nydusNetwork':
                self.nydus_id = uid
                break
        
        # Find Bait Zergling (farthest from Nydus)
        if self.nydus_id is not None:
            nydus_pos = obs['ally'][self.nydus_id]['coords']
            max_dist = -1
            best_id = None
            for uid, unit in obs['ally'].items():
                if unit['unit_type'] == 'zergling':
                    dist = self.get_distance(unit['coords'], nydus_pos)
                    if dist > max_dist:
                        max_dist = dist
                        best_id = uid
            self.bait_id = best_id
            
        if self.bait_id is not None and self.bait_id in obs['ally']:
            self.bait_start_health = obs['ally'][self.bait_id]['health']

    actions = {}
    trigger_met = False

    # Check Trigger: Bait attacked
    if self.bait_id in obs['ally']:
        current_health = obs['ally'][self.bait_id]['health']
        if current_health < self.bait_start_health:
            trigger_met = True
    
    # Define Targets
    enemy_cc_pos = None
    for uid, unit in obs['enemy'].items():
        if unit['unit_type'] == 'CommandCenter':
            enemy_cc_pos = unit['coords']
            break
    
    nydus_pos = None
    if self.nydus_id in obs['ally']:
        nydus_pos = obs['ally'][self.nydus_id]['coords']

    # Assign Actions
    for uid, unit in obs['ally'].items():
        # Skip buildings for movement logic (handled by safety fill)
        if unit['unit_type'] in ['hatchery', 'nydusNetwork', 'nydusCanal']:
            continue
        
        if uid == self.bait_id:
            # Bait moves to enemy base
            if enemy_cc_pos:
                action = self.get_move_direction(unit['coords'], enemy_cc_pos)
                if self.validate(uid, action, obs):
                    actions[uid] = action
        else:
            # Others move to Nydus Network
            if nydus_pos:
                action = self.get_move_direction(unit['coords'], nydus_pos)
                if self.validate(uid, action, obs):
                    actions[uid] = action
                    
    # Safety Fill
    for uid in obs['ally']:
        if uid not in actions:
            avail = obs['ally'][uid]['available_actions']
            if 'stop' in avail:
                actions[uid] = 'stop'
            elif avail:
                actions[uid] = avail[0]
                
    return actions, trigger_met

"""
        elif idx == 1:
            return """
def execute(self, obs):
    # Phase 2: Unload
    # 我们可以直接读取上一阶段设定的 self.bait_id，虽然这阶段可能不用
    actions = {}
    trigger = False
    
    # 假设我们让所有单位出来
    for uid in obs['ally']:
        if obs['ally'][uid]['unit_type'] == 'nydusNetwork':
            actions[uid] = 'unload_all'
            
    # Trigger logic (simplified)
    if len(obs['ally']) > 2:
        trigger = True
        
    return actions, trigger
"""
        return "def execute(self, obs): return {}, False"

