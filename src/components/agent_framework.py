import types
import re
import numpy as np

from termcolor import cprint
import math
import heapq

class CommanderContext:
    """
    这个类作为 'self' 传递给 LLM 生成的代码。
    它不仅存储跨阶段的全局变量，还提供数学计算和战术辅助函数。
    """
    def __init__(self):
        # 1. 基础日志与记忆
        self.logs = []
    
        
    def log(self, message):
        """记录日志，方便调试"""
        formatted_msg = f"[Commander Log]: {message}"
        self.logs.append(formatted_msg)
        print(formatted_msg)

    # ==========================
    # 1. 查询辅助函数 (Query Helpers)
    # ==========================
    
    def get_units_by_type(self, units_dict, type_name):
        """
        获取指定类型的所有单位 ID 列表。
        Usage: self.get_units_by_type(obs['ally'], 'zergling')
        """
        return [uid for uid, unit in units_dict.items() if unit['unit_type'] == type_name]

    def get_unit_pos(self, unit_info):
        """安全获取单位坐标"""
        return unit_info.get('coords', (0, 0))

    # ==========================
    # 2. 数学与空间辅助函数 (Math & Spatial)
    # ==========================

    def get_distance(self, pos1, pos2):
        """
        计算两点之间的欧几里得距离。
        pos 可以是坐标元组 (x, y) 或 包含 'coords' 的单位字典。
        """
        # 如果输入是单位字典，自动提取坐标
        if isinstance(pos1, dict) and 'coords' in pos1:
            pos1 = pos1['coords']
        if isinstance(pos2, dict) and 'coords' in pos2:
            pos2 = pos2['coords']
            
        return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

    def find_closest_enemy(self, ally_pos, enemy_dict):
        """
        寻找距离 ally_pos 最近的敌方单位 ID。
        """
        closest_id = None
        min_dist = float('inf')
        
        for eid, enemy in enemy_dict.items():
            dist = self.get_distance(ally_pos, enemy['coords'])
            if dist < min_dist:
                min_dist = dist
                closest_id = eid
                
        return closest_id, min_dist

    def find_closest_ally(self, target_pos, ally_dict, exclude_id=None):
        """
        寻找距离目标点最近的我方单位 ID (排除掉自身)。
        """
        closest_id = None
        min_dist = float('inf')
        
        for aid, ally in ally_dict.items():
            if exclude_id is not None and aid == exclude_id:
                continue
                
            dist = self.get_distance(target_pos, ally['coords'])
            if dist < min_dist:
                min_dist = dist
                closest_id = aid
                
        return closest_id

    # ==========================
    # 3. 动作辅助函数 (Action Helpers)
    # =========================
    
    def get_move_direction(self, current_pos, target_pos):
        """
        根据当前位置和目标位置，返回 SMAC 的移动指令字符串。
        Coordinates: North=Y+, East=X+
        """
        # 兼容单位字典输入
        if isinstance(current_pos, dict): current_pos = current_pos['coords']
        if isinstance(target_pos, dict): target_pos = target_pos['coords']

        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        
        # 简单的贪婪寻路：优先在距离更远的轴上移动
        if abs(dx) > abs(dy):
            return 'move_east' if dx > 0 else 'move_west'
        else:
            return 'move_north' if dy > 0 else 'move_south'

    def filter_available_actions(self, desired_action_prefix, available_actions):
        """
        从可用动作中筛选。
        例如：想攻击，查找 'attack_enemy_1' 是否在 available_actions 中。
        """
        for action in available_actions:
            if action.startswith(desired_action_prefix):
                return action
        return None
    
    def validate(self, unit_id, action, obs):
        avail = obs['ally'][unit_id]['available_actions']
        
        if action in avail:
            return True
        return False






class LowImplementer:
    def __init__(self, args, env):
        self.args = args
        self.env = env


    def _heuristic(self, x, y):
        '''曼哈顿距离作启发函数'''
        return abs(x[0] - y[0]) + abs(x[1] - y[1])
    
    def _get_neighbors(self, node):
        '''获取相邻位置'''
        x, y = node
        step = int(self.env._move_amount)       
        map_w, map_h = self.env.map_x, self.env.map_y

        # 候选移动方向：北，南，东，西
        candidates = [
            ((x, y + step), "move_north"),
            ((x, y - step), "move_south"),
            ((x + step, y), "move_east"),
            ((x - step, y), "move_west")
        ]
        valid_neighbors = []
        
        # [DEBUG] 只有在调试时开启，平时注释掉，否则刷屏
        # debug_neighbor_logs = [] 

        for(nx, ny), action_name in candidates:
            if 0 <= nx < map_w and 0 <= ny < map_h:
                try:
                    # 注意：请确认 env.pathing_grid 的索引顺序是 [x, y] 还是 [y, x]
                    # 这里假设是 [x, y]
                    grid_score = self.env.pathing_grid[int(nx), int(ny)]
                    if grid_score == 1: # 假设 1 是可通行
                        valid_neighbors.append( ((nx, ny), action_name))
                    # else:
                        # debug_neighbor_logs.append(f"Blocked({nx},{ny})")
                except IndexError:
                    pass
                    
        # if debug_neighbor_logs: cprint(f"Neighbors blocked around {node}: {debug_neighbor_logs}", "magenta")
        return valid_neighbors
    
    def action_name_to_int(self, action_name):
        one_hot = self.env.map_action_name_to_one_hot(action_name)
        if sum(one_hot) > 0: 
            final_action_int = int(np.argmax(one_hot))
            return final_action_int
        cprint(f"[Error] Action name '{action_name}' not found in action mapping! Use 'stop' instead.", "red")
        return 1



    def _print_map_debug(self, start, goal):
        """
        [DEBUG TOOL] 打印当前地图的 ASCII 视图
        1 (True) = 可通行 (.), 0 (False) = 墙 (#)
        """
        map_w, map_h = self.env.map_x, self.env.map_y
        grid = self.env.pathing_grid
        
        cprint(f"\n[MAP VISUALIZATION] Size: {map_w}x{map_h}", "white", "on_blue")
        
        # SMAC地图坐标: x是宽(col), y是高(row)，打印时通常行是y，列是x
        # 注意: 终端打印通常是从上到下(y大到y小)还是y小到y大，取决于你的习惯
        # 这里为了对齐坐标系，我们按 y 从 max 到 min 打印
        
        for y in range(map_h - 1, -1, -1):
            line = f"{y:02d} "
            for x in range(map_w):
                if (x, y) == start:
                    char = 'S' # Start
                    color = 'green'
                elif (x, y) == goal:
                    char = 'G' # Goal
                    color = 'red'
                else:
                    try:
                        val = grid[x, y]
                        if val == 1: 
                            char = '.' 
                            color = 'white'
                        else: 
                            char = '#' 
                            color = 'grey'
                    except IndexError:
                        char = '?'
                        color = 'magenta'
                
                # 简单拼接，带颜色有点难对齐，这里只打印字符
                # 如果需要颜色，终端输出会乱，暂只用字符区分
                line += char + " "
            print(line)
        print("   " + " ".join([f"{x%10}" for x in range(map_w)])) # 打印X轴个位数
        print("   " + " ".join([f"{x//10}" if x>=10 else " " for x in range(map_w)])) # 打印X轴十位数
        print("\n")


    def Astar_search(self, start, goal):
        '''返回next step动作名'''
        start = (int(start[0]), int(start[1])) # SMAC坐标是float，这里转换
        goal = (int(goal[0]), int(goal[1]))


        # cprint(f"\n[A* START] Searching path: {start} -> {goal}", "cyan")
        # self._print_map_debug(start, goal)



        if start == goal:
            return None  
        
        frontier = []
        heapq.heappush(frontier, (0, start))

        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        first_step_action = {} 
        found = False
        limit_steps = 5000 
        steps = 0
        
        closest_node_to_goal = start
        min_dist_to_goal = self._heuristic(start, goal)

        while frontier:
            _, current = heapq.heappop(frontier)
            steps += 1

            dist = self._heuristic(current, goal) # 当前距离目标最近点

            # if steps < 100 or steps % 500 == 0:
            #     action_taken = first_step_action.get(current, "START")
            #     print(f"{steps:<5} | {str(current):<10} | {dist:<10} | {action_taken:<15} | {cost_so_far[current]:<5}")



            if dist < min_dist_to_goal:
                min_dist_to_goal = dist
                closest_node_to_goal = current
            if dist < self.env._move_amount: # 或者 < 4，宽容度
                goal = current 
                found = True
                break

            if steps > limit_steps:
                cprint(f"[A* Timeout] Exceeded {limit_steps} steps. Current: {current}, Goal: {goal}", "yellow")
                break

            neighbors = self._get_neighbors(current)

            
            for next_node, action_name in neighbors:
                new_cost = cost_so_far[current] + self.env._move_amount
                
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self._heuristic(next_node, goal)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current
                    
                    if current == start:
                        first_step_action[next_node] = action_name
                    elif current in first_step_action:
                        first_step_action[next_node] = first_step_action[current]

        if found:
            if goal == start:
                return None 
            return first_step_action.get(goal)
        
        if closest_node_to_goal != start: 
            return first_step_action.get(closest_node_to_goal)
        
        # 如果循环结束没找到 found
        cprint(f"[A* Fail] No path found after {steps} steps.", "magenta")
        return None


    def get_next_action(self, agent_id, target_pos):
        """
        根据目标位置，生成下一个动作指令。
        """
        unit = self.env.get_unit_by_id(agent_id)
        if unit is None: 
            return None
        
        start_pos = (unit.pos.x, unit.pos.y)
        next_action = self.Astar_search(start_pos, target_pos)
        return next_action

    def take_actions(self, high_level_commands,llm_obs_dict):
        actions = np.ones((self.env.n_agents))  # 默认全停

        # cprint(high_level_commands, "yellow")

        for uid, command in high_level_commands.items():
            # cprint(f"\n[LowImplementer] Processing Agent {uid} Command: {command}", "cyan")
            if uid not in llm_obs_dict['ally']:
                cprint(f"[Error] Agent ID {uid} not found in llm_obs_dict['ally']!", "red")
                continue

            ############################################################
            # check action validity
            # if command.startswith('navigate_to_'):
            #     if 'can_move' not in llm_obs_dict['ally'][uid]['available_actions']:
            #         cprint(f"[Warning] Agent {uid} cannot move but got command: {command}", "yellow")
            # else:
            #     if command not in llm_obs_dict['ally'][uid]['available_actions']:
            #         cprint(f"[Warning] Agent {uid} cannot perform action: {command}", "yellow")
            ############################################################

            if llm_obs_dict['ally'][uid]['health'] <= 0:
                final_action_int = 0  # 死亡单位强制 No-Op
            else:
                
                # The agent choose to move
                # high-level navigate cmd: naviagte_to_enemy_{id}
                if isinstance(command, str) and command.startswith('navigate_to_'):
                    final_action_int = 1  # 先默认 Stop
                    if command.startswith('navigate_to_enemy_') :
                        match = re.match(r'navigate_to_enemy_(\d+)', command) or re.match(r'navigate_to_ally_(\d+)', command)
                        if match:
                            target_enemy_id = int(match.group(1))
                            if target_enemy_id in self.env.enemies:
                                target_enemy_unit = self.env.enemies[target_enemy_id]
                                # 只有存活的敌人才有位置信息
                                if target_enemy_unit.health > 0:
                                    target_x, target_y = target_enemy_unit.pos.x, target_enemy_unit.pos.y
                                    specific_action_name = self.get_next_action(uid, (target_x, target_y))
                                    

                                    if specific_action_name:
                                        final_action_int = self.action_name_to_int(specific_action_name)
                                    else:
                                        # A* 返回 None (可能是到了，或者是没路)
                                        cprint(f"A* return None, either already at goal or no way", "yellow") 
                                        pass 
                                else:
                                    # 敌人死了，虽然ID在列表里，但无法移动
                                    cprint(f"Target Enemy {target_enemy_id} is dead.", "yellow") 
                                    pass
                            else:
                                cprint(f"[Error] Target Enemy ID {target_enemy_id} not found in env.enemies!", "red")
                    
                    elif command.startswith('navigate_to_ally_'):
                        match = re.match(r'navigate_to_ally_(\d+)', command)
                        if match:
                            target_ally_id = int(match.group(1))
                            if target_ally_id in self.env.agents:
                                target_ally_unit = self.env.agents[target_ally_id]
                                # 只有存活的盟友才有位置信息
                                if target_ally_unit.health > 0:
                                    target_x, target_y = target_ally_unit.pos.x, target_ally_unit.pos.y
                                    specific_action_name = self.get_next_action(uid, (target_x, target_y))                             

                                    if specific_action_name:
                                        final_action_int = self.action_name_to_int(specific_action_name)
                                    else:
                                        # A* 返回 None (可能是到了，或者是没路)
                                        cprint(f"A* return None, either already at goal or no way", "yellow") 
                                        pass 
                                else:
                                    # 盟友死了，虽然ID在列表里，但无法移动
                                    # cprint(f"[Warn] Target Ally {target_ally_id} is dead. Can't move to dead ally.", "yellow") 
                                    pass
                            else:
                                cprint(f"[Error] Target Ally ID {target_ally_id} not found in env.allies!", "red")
                    # 需要判断A*返回的动作是否在available_actions中
                    
                    available_actions = self.env.get_avail_agent_actions(uid)
                    if available_actions[final_action_int] != 1:
                        final_action_int = 1  # 强制 Stop

                    # else:
                    #     raise ValueError(f"Unknown high-level command format: {command}")
                
                elif isinstance(command, str) and command in llm_obs_dict['ally'][uid]['available_actions']:
                    # The agent choose to attack or use skill or stop
                    final_action_int = self.action_name_to_int(command)
                else:
                    raise ValueError(f"Unknown high-level command or invalid action: {command}; available: {llm_obs_dict['ally'][uid]['available_actions']}")
            
            # 处理 uid 类型
            if type(uid)==str: uid = int(uid)
            actions[uid] = final_action_int
            
        return actions
