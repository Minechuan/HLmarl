import numpy as np
from termcolor import cprint

def find_enemy_information(all_agent_obs):
    """
    Function to find the enemy information that contains the largest number of enemies visible.
    If an enemy can only be seen by one agent, we will use that agent's information throughout the episode.
    enemy:{
        'id': int,
        'unit_type': str,
        'coords': (x, y),
        'health': float,
        'shield': float,
    }
    """
    enemy_dict = {}
    enemy_info_list = [agent_obs['tactical']['visible_enemies'] for agent_obs in all_agent_obs]
    

    
    for i,visible_enemies in enumerate(enemy_info_list):
        if visible_enemies == []:
            continue
        else: # there are enemies visible
            for enemy in visible_enemies:
                # if enemy not already recorded, add to dict
                if enemy['id'] not in enemy_dict:
                    enemy_dict[enemy['id']] = {}
                    enemy_dict[enemy['id']]['unit_type'] = enemy['unit_type']
                    
                    # get abs position
                    agent_pos = (all_agent_obs[i]['self_info']['pos_x'], all_agent_obs[i]['self_info']['pos_y'])                    
                    enemy_dict[enemy['id']]['coords'] = (enemy['pos_x'], enemy['pos_y'])
                    enemy_dict[enemy['id']]['health'] = enemy['health']
                    enemy_dict[enemy['id']]['shield'] = enemy['shield']

    return enemy_dict

def find_ally_information(all_agent_obs):
    """
    Function to find the ally information for all agents.
    ally:{
        'id': int,
        'unit_type': str,
        'coords': (x, y),
        'health': float,
        'shield': float,
        'available_actions': List[int],
        'unavailable_reason': str,
    }
    """
    ally_dict = {}
    
    # simplify ally information
    for agent_obs in all_agent_obs:
        ally_dict[agent_obs['agent_id']] = {}
        ally_dict[agent_obs['agent_id']]['status'] = agent_obs['status']
        # print("Agent ID:", agent_obs['agent_id'], "Status:", agent_obs['status'])
        # 
        #     ally_dict[agent_obs['agent_id']]['health'] = -1
        #     ally_dict[agent_obs['agent_id']]['unit_'] = -1
        # else: 
            
        ally_dict[agent_obs['agent_id']]['unit_type'] = agent_obs['self_info']['unit_type']


        ally_dict[agent_obs['agent_id']]['coords'] = (agent_obs['self_info']['pos_x'], agent_obs['self_info']['pos_y'])
        ally_dict[agent_obs['agent_id']]['health'] = agent_obs['self_info']['health']
        ally_dict[agent_obs['agent_id']]['shield'] = agent_obs['self_info']['shield']
        ally_dict[agent_obs['agent_id']]['available_actions'] = agent_obs['available_actions']
        ally_dict[agent_obs['agent_id']]['unavailable_reason'] = agent_obs['unavailable_reason']
        
        # if ally_dict[agent_obs['agent_id']]['status'] == 'dead':
        #     cprint(f"Agent available actions: {ally_dict[agent_obs['agent_id']]['available_actions']}", 'red')

    return ally_dict








def simplify_obs(all_agent_obs):
    """
    Function to simplify the raw observation dictionary for easier processing.
        1. obs["ally"]: dict
        2. obs["enemy"]: dict
        3. obs["step"]: int
    """

    # get enemy information
    # if enemy can only be seen by one agent, the whole time use that agent's info
    # print all_agent_obs keys
    
    
    simple = {}
    enemy_info = find_enemy_information(all_agent_obs)
    simple['enemy'] = enemy_info


    ally_info = find_ally_information(all_agent_obs)
    simple['ally'] = ally_info
    simple['step'] = all_agent_obs[0]['step']
    return simple