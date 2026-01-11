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

        
            '''[DEBUG] 每 10 步打印一次 bait_id 和各单位到敌方 CommandCenter 的距离'''
            # if self.current_event_idx == 0:
            #     print(llm_info_dict['ally'][3]['available_actions'])

                # from termcolor import cprint
                # cprint(f"\n[DEBUG] Visible Enemies: {list(llm_info_dict['enemy'].keys())}", "yellow")

                # bait_id = self.commander.bait_id
                # print("Agents load by NydusNetwork",self.env.load.keys())
                # for i, v in llm_info_dict['enemy'].items():
                #     if v['unit_type'] == 'CommandCenter':
                #         coord = v['coords']
                # dist_dict = {}
                # for i, v in llm_info_dict['ally'].items():
                #     dist = self.commander.get_distance(v['coords'], coord)
                #     dist_dict[i] = round(dist,1)
                # print ("Distance:", dist_dict)
                # print(f"bait_id: {bait_id}")
                # print( f"bait action: {high_action[bait_id]}")
                # print(f"bait status: {llm_info_dict['ally'][bait_id]['status']}")
                # print(f"bait agent x y is : {llm_info_dict['ally'][bait_id]['coords']}")
                # for id in [1,2,3]:
                #     print(f"Unit type {llm_info_dict['ally'][id]['unit_type']} id {id} action: {high_action[id]} status: {llm_info_dict['ally'][id]['status']} Coords: {llm_info_dict['ally'][id]['coords']}")
                # for id in [0,1,2,15]:
                #     cprint(f"Unit type {llm_info_dict['ally'][id]['unit_type']} id {id} available act: {llm_info_dict['ally'][id]['available_actions']} action: {high_action[id]}", "green")

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


            actions = self.low_implementer.take_actions(high_action, llm_info_dict)
            # if self.current_event_idx ==1:
            #     for id in [0,1,2,15]:
            #         cprint(f"Low-level action for unit id {id} : {actions[id]}", "blue")
            reward, terminated, env_info = self.env.step(actions)
            reward, delta_enemy, delta_deaths, delta_ally = reward
            episode_return["reward"] += reward
            episode_return["delta_enemy"] += delta_enemy
            episode_return["delta_deaths"] += delta_deaths
            episode_return["delta_ally"] += delta_ally

            self.t += 1
            # get llm info for next step
            llm_info_dict = self.env.get_llm_info_dict()

        cprint(f"\n[System]: Episode finished in {self.t} steps.", "green")
        print(" Episode Summary ********************************")
        for i in llm_info_dict['ally'].values():
            print(f"Unit type {i['unit_type']} status: {i['status']}")
        print("************************************************")
        # log episode statistics
        print(f"AgentRunner.run: Episode completed in {self.t} steps. Logging statistics.")
        print(f"reward: {episode_return['reward']}, delta_enemy: {episode_return['delta_enemy']}, delta_deaths: {episode_return['delta_deaths']}, delta_ally: {episode_return['delta_ally']}")
        print("*********************************")
        battle_result = env_info["battle_won"]
        if battle_result == True:
            cprint("Battle Result: Victory", "green")
        elif battle_result == False:
            cprint("Battle Result: Defeat", "red")
        else:
            cprint("Battle Result: Draw", "yellow")
        print("************************************************")

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
# Event 0 Response:
def execute(self, obs):
    actions = {}
    trigger_met = False

    if not hasattr(self, 'init_done'):
        self.init_done = True

    # Helper function for Euclidean distance
    def get_distance(pos1, pos2):
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    # Identify Enemy Targets
    cc_id = 2
    command_center = obs['enemy'].get(cc_id)
    hellions = [u for u in obs['enemy'].values() if u['unit_type'] == 'HellionTank']

    # Track burrowed units for Trigger logic
    burrowed_units = []

    for uid, unit in obs['ally'].items():
        if unit['available_actions'] == ['no-op']:
            actions[uid] = 'no-op'
            continue
        
        unit_type = unit['unit_type']
        available = unit['available_actions']

        # Handling Hatchery
        if unit_type == 'hatchery':
            actions[uid] = 'stop'
            continue

        # Handling ZerglingBurrowed (Waiting for enemies to leave)
        if unit_type == 'zerglingBurrowed':
            burrowed_units.append(unit)
            actions[uid] = 'stop' if 'stop' in available else available[0]
            continue

        # Handling Zergling (Active)
        if unit_type == 'zergling':
            # Check proximity to any HellionTank
            closest_hellion_dist = float('inf')
            for h in hellions:
                d = get_distance(unit['coords'], h['coords'])
                if d < closest_hellion_dist:
                    closest_hellion_dist = d
            
            # Logic: Burrow if Hellion is close (threshold ~10.0), else Move/Attack CC
            if closest_hellion_dist < 10.0 and 'burrow_down' in available:
                actions[uid] = 'burrow_down'
            else:
                # Attack CC if in range, otherwise move to it
                attack_action = f"attack_enemy_{cc_id}"
                if attack_action in available:
                    actions[uid] = attack_action
                elif command_center: # Only navigate if target exists
                    actions[uid] = f"navigate_to_enemy_{cc_id}"
                else:
                    actions[uid] = 'stop'

    # Trigger Logic: "After the enemy moves away"
    # We satisfy this if we have burrowed units and the threat (Hellions) is no longer close.
    # Using a slightly larger distance (hysteresis) to ensure safety before unburrowing.
    if burrowed_units:
        is_safe = True
        for b_unit in burrowed_units:
            for h in hellions:
                if get_distance(b_unit['coords'], h['coords']) < 12.0:
                    is_safe = False
                    break
            if not is_safe:
                break
        
        if is_safe:
            trigger_met = True

    # Safety fill for any missed units
    for uid in obs['ally']:
        if uid not in actions:
            avail = obs['ally'][uid]['available_actions']
            actions[uid] = 'stop' if 'stop' in avail else avail[0]

    return actions, trigger_met
"""
        if idx == 1:
            return """
def execute(self, obs):
    actions = {}
    trigger_met = False

    if not hasattr(self, 'init_done'):
        self.init_done = True

    # Helper function for Euclidean distance (if needed)
    def get_distance(pos1, pos2):
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    cc_id = 2
    command_center_exists = cc_id in obs['enemy']

    for uid, unit in obs['ally'].items():
        if unit['available_actions'] == ['no-op']:
            actions[uid] = 'no-op'
            continue

        unit_type = unit['unit_type']
        available = unit['available_actions']

        # Hatchery Logic
        if unit_type == 'hatchery':
            actions[uid] = 'stop'
            continue

        # Burrowed Zergling Logic: Unburrow immediately to join the fight
        if unit_type == 'zerglingBurrowed':
            if 'burrow_up' in available:
                actions[uid] = 'burrow_up'
            else:
                actions[uid] = 'stop'
            continue

        # Active Zergling Logic: Advance to destroy Command Center
        if unit_type == 'zergling':
            # Prioritize attacking the Command Center
            attack_cc = f"attack_enemy_{cc_id}"
            
            if attack_cc in available:
                actions[uid] = attack_cc
            elif command_center_exists and 'can_move' in available:
                actions[uid] = f"navigate_to_enemy_{cc_id}"
            else:
                # If CC is destroyed or unreachable, attack any other enemy
                attack_actions = [a for a in available if a.startswith('attack_enemy_')]
                if attack_actions:
                    actions[uid] = attack_actions[0]
                elif 'can_move' in available and obs['enemy']:
                    # Move to the first available enemy if no specific target
                    first_enemy_id = list(obs['enemy'].keys())[0]
                    actions[uid] = f"navigate_to_enemy_{first_enemy_id}"
                else:
                    actions[uid] = 'stop'

    # Safety fill ensures every unit has an action
    for uid in obs['ally']:
        if uid not in actions:
            avail = obs['ally'][uid]['available_actions']
            actions[uid] = 'stop' if 'stop' in avail else avail[0]

    return actions, trigger_met
"""
        if idx == 2:
            return """
def execute(self, obs):
    actions = {}
    trigger_met = False

    # Initialization
    if not hasattr(self, 'init_done'):
        self.init_done = True
        
        # Identify Nydus Network (Network loads, Canal unloads)
        nydus_net_list = self.get_units_by_type(obs['ally'], 'nydusNetwork')
        self.nydus_id = nydus_net_list[0] if nydus_net_list else None

        # Identify Zerglings (Legacy init)
        zerglings = self.get_units_by_type(obs['ally'], 'zergling')
        
        # Select Bait: Zergling farthest from Nydus Network (Legacy logic)
        self.bait_id = None
        if self.nydus_id is not None and zerglings:
            nydus_pos = obs['ally'][self.nydus_id]['coords']
            max_dist = -1.0
            for z_id in zerglings:
                dist = self.get_distance(obs['ally'][z_id]['coords'], nydus_pos)
                if dist > max_dist:
                    max_dist = dist
                    self.bait_id = z_id
        elif zerglings:
            self.bait_id = zerglings[0]
            
        # Store initial health (Legacy)
        if self.bait_id is not None and self.bait_id in obs['ally']:
            self.bait_max_health = obs['ally'][self.bait_id]['health']
        else:
            self.bait_max_health = 35.0

    # Phase 3 Logic
    
    # 1. Check if units are still loaded
    # Loaded units typically have unavailable_reason "The agent is loaded..." or just ['stop'] actions
    # We check if any Zergling or Roach is currently loaded.
    units_still_loaded = False
    mobile_types = ['zergling', 'roach']
    
    for uid, unit in obs['ally'].items():
        if unit['unit_type'] in mobile_types:
            # Check for loaded status via unavailable_reason or restricted actions
            if 'loaded' in unit.get('unavailable_reason', '').lower():
                units_still_loaded = True
                break
            # Fallback: if alive but only 'stop' is available, assume loaded (unless bait/stuck)
            if unit['available_actions'] == ['stop'] and uid != self.bait_id:
                # If bait is alive and stopped, it doesn't count as loaded for the Nydus trigger usually
                # But to be safe, we check if specific loaded reason exists.
                # If unavailable_reason is empty but actions=['stop'], might be purely stopped.
                # However, in the snapshot, loaded units explicitly say "loaded".
                pass

    if not units_still_loaded:
        trigger_met = True

    # 2. Assign Actions
    # Find Nydus Canal (the exit point)
    nydus_canals = self.get_units_by_type(obs['ally'], 'nydusCanal')
    nydus_canal_id = nydus_canals[0] if nydus_canals else None

    for uid, unit in obs['ally'].items():
        if unit['available_actions'] == ['no-op']:
            actions[uid] = 'no-op'
            continue
            
        u_type = unit['unit_type']
        
        # Nydus Canal: Execute Unload
        if u_type == 'nydusCanal':
            if 'NydusCanalUnload' in unit['available_actions']:
                actions[uid] = 'NydusCanalUnload'
            else:
                actions[uid] = 'stop'
            continue
            
        # All other units (including Nydus Network): stop
        # Loaded units can only stop anyway.
        # Bait (if alive) should just wait or stop this phase.
        actions[uid] = 'stop'

    # Safety fill
    for uid in obs['ally']:
        if uid not in actions:
            avail = obs['ally'][uid]['available_actions']
            actions[uid] = 'stop' if 'stop' in avail else avail[0]

    return actions, trigger_met
"""
        if idx == 3:
            return """
def execute(self, obs):
    actions = {}
    trigger_met = False

    # Initialization
    if not hasattr(self, 'init_done'):
        self.init_done = True
        
        # Legacy fields preservation
        nydus_net_list = self.get_units_by_type(obs['ally'], 'nydusNetwork')
        self.nydus_id = nydus_net_list[0] if nydus_net_list else None
        
        zerglings = self.get_units_by_type(obs['ally'], 'zergling')
        # Re-select a theoretical bait just to populate the field if accessed, 
        # though Phase 4 doesn't distinguish bait anymore.
        self.bait_id = zerglings[0] if zerglings else None
        self.bait_max_health = 35.0

    # Phase 4 Logic: Attack Enemy Command Center
    
    # Identify Target: Command Center
    enemy_ccs = self.get_units_by_type(obs['enemy'], 'CommandCenter')
    target_cc = enemy_ccs[0] if enemy_ccs else None

    # Fallback target: Any enemy (if CC is dead or not visible)
    enemies = list(obs['enemy'].keys())
    fallback_target = enemies[0] if enemies else None

    for uid, unit in obs['ally'].items():
        if unit['available_actions'] == ['no-op']:
            actions[uid] = 'no-op'
            continue
            
        u_type = unit['unit_type']
        avail = unit['available_actions']
        
        # Structures (Hatchery, NydusNetwork, NydusCanal) cannot attack or move
        if u_type in ['hatchery', 'nydusNetwork', 'nydusCanal']:
            actions[uid] = 'stop'
            continue
            
        # Combat Units (Zerglings, Roaches)
        
        # 1. If we can attack the CC explicitly, do it.
        if target_cc:
            cc_attack_action = f"attack_enemy_{target_cc}"
            if cc_attack_action in avail:
                actions[uid] = cc_attack_action
                continue
        
        # 2. If we can move, move towards the CC.
        if target_cc and 'can_move' in avail:
            actions[uid] = f"navigate_to_enemy_{target_cc}"
            continue
            
        # 3. Fallback: Attack any enemy within range.
        # Find first available attack action
        any_attack = next((a for a in avail if a.startswith('attack_enemy_')), None)
        if any_attack:
            actions[uid] = any_attack
            continue
            
        # 4. Fallback: Move towards any enemy.
        if fallback_target and 'can_move' in avail:
            actions[uid] = f"navigate_to_enemy_{fallback_target}"
            continue
            
        # 5. Default
        actions[uid] = 'stop'

    # Safety fill
    for uid in obs['ally']:
        if uid not in actions:
            avail = obs['ally'][uid]['available_actions']
            actions[uid] = 'stop' if 'stop' in avail else avail[0]

    return actions, trigger_met
"""


        return "def execute(self, obs): return {}, False"

    def read_events_from_file(self, filepath,idx):
        with open(filepath, 'r') as f:
            lines = f.readlines()
        events = [line.strip() for line in lines if line.strip()]
        return events