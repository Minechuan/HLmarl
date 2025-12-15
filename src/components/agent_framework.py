import types
import re
import numpy as np


import math

class CommanderContext:
    """
    这个类作为 'self' 传递给 LLM 生成的代码。
    它不仅存储跨阶段的全局变量，还提供数学计算和战术辅助函数。
    """
    def __init__(self):
        # 1. 基础日志与记忆
        self.logs = []
        
        # 预留一些常用变量名，防止 LLM 幻觉访问不存在的属性
        self.bait_id = None
        self.nydus_id = None
        
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
    # ==========================

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
            return action
        if 'stop' in avail:
            return 'stop'
        return avail[0] if avail else 'stop'







class LowImplementer:
    def __init__(self, args, env):
        self.args = args
        self.env = env

    def take_actions(self, high_level_commands):
        actions = np.ones((self.env.n_agents))  # 默认全停
        for uid, command in high_level_commands.items():
            avail_action = self.env.get_avail_agent_actions(uid)
            one_hot_action = self.env.map_action_name_to_one_hot(command)
            if one_hot_action is not None and avail_action[int(np.argmax(one_hot_action))] == 1:
                # The action is valid, action is a int index
                action = int(np.argmax(one_hot_action))
            else:
                action = 1 if avail_action[1] == 1 else 0  # 停止或无操作
            if type(uid)==str: # "12" -> 12
                uid = int(uid)
            actions[uid] = action
        return actions
