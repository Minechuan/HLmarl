# LLM Observation & Action Example for SC2 Tactics Environment










## Example: LLM Available Actions


Agent hatchery Available Actions: (['stop'], "The agent is Hatchery, action can only be 'stop'")
Agent nydusNetwork Available Actions: (['stop', 'NydusCanalLoad', 'attack_enemy_0'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent zergling Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent roach Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent roach Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent roach Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent roach Available Actions: (['stop', 'move_north', 'move_south', 'move_east', 'move_west'], '')
Agent nydusCanal Available Actions: (['stop'], "The agent is Nyduscanal, action can only be 'stop'")



## Example: simplified obs


Simplified Obs Key: enemy, 
Sample Value: {
    2: {'unit_type': 'SiegeTank', 'coords': (42.193359375, 58.21533203125), 'health': 175.0, 'shield': 0.0}, 
    4: {'unit_type': 'SiegeTank', 'coords': (45.003662109375, 57.690673828125), 'health': 175.0, 'shield': 0.0}, 
    9: {'unit_type': 'Marine', 'coords': (43.253662109375, 58.752197265625), 'health': 45.0, 'shield': 0.0}, 
    7: {'unit_type': 'Marine', 'coords': (42.565185546875, 59.440673828125), 'health': 45.0, 'shield': 0.0}, 
    1: {'unit_type': 'Marine', 'coords': (44.003662109375, 58.690673828125), 'health': 45.0, 'shield': 0.0}, 
    10: {'unit_type': 'Marine', 'coords': (43.253662109375, 59.440673828125), 'health': 45.0, 'shield': 0.0}, 
    5: {'unit_type': 'Marine', 'coords': (42.503662109375, 60.190673828125), 'health': 45.0, 'shield': 0.0}, 
    8: {'unit_type': 'Marine', 'coords': (43.942138671875, 59.440673828125), 'health': 45.0, 'shield': 0.0}, 
    0: {'unit_type': 'Marine', 'coords': (43.253662109375, 60.129150390625), 'health': 45.0, 'shield': 0.0}, 
    6: {'unit_type': 'Marine', 'coords': (44.003662109375, 60.190673828125), 'health': 45.0, 'shield': 0.0}, 
    3: {'unit_type': 'CommandCenter', 'coords': (46.5, 64.5), 'health': 1500.0, 'shield': 0.0}}

Simplified Obs Key: ally, 
Sample Value: 
{0: {'status': 'alive', 'unit_type': 'hatchery', 'coords': (15.5, 10.5), 'health': 1500.0,  'shield': 0.0, 'available_actions': ['stop'], 'unavailable_reason': "The agent is Hatchery, action can only be 'stop'"},
1: {'status': 'alive', 'unit_type': 'nydusNetwork', 'coords': (28.5, 11.5), 'health': 850.0, 'shield': 0.0, 'available_actions': ['stop', 'NydusCanalLoad', 'attack_enemy_0'], 'unavailable_reason': ''}, 
2: {'status': 'alive', 'unit_type': 'zergling', 'coords': (21.510009765625, 14.73828125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 3: {'status': 'alive', 'unit_type': 'zergling', 'coords': (21.885009765625, 13.61328125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 4: {'status': 'alive', 'unit_type': 'zergling', 'coords': (21.885009765625, 15.86328125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 5: {'status': 'alive', 'unit_type': 'zergling', 'coords': (22.260009765625, 14.36328125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 6: {'status': 'alive', 'unit_type': 'zergling', 'coords': (22.260009765625, 15.11328125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 7: {'status': 'alive', 'unit_type': 'zergling', 'coords': (23.010009765625, 12.86328125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 8: {'status': 'alive', 'unit_type': 'zergling', 'coords': (24.135009765625, 13.61328125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 9: {'status': 'alive', 'unit_type': 'zergling', 'coords': (24.135009765625, 15.86328125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 10: {'status': 'alive', 'unit_type': 'zergling', 'coords': (24.885009765625, 14.73828125), 'health': 35.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 11: {'status': 'alive', 'unit_type': 'roach', 'coords': (23.010009765625, 13.7998046875), 'health': 145.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 12: {'status': 'alive', 'unit_type': 'roach', 'coords': (23.010009765625, 14.73828125), 'health': 145.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 13: {'status': 'alive', 'unit_type': 'roach', 'coords': (23.010009765625, 15.6767578125), 'health': 145.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 14: {'status': 'alive', 'unit_type': 'roach', 'coords': (23.948486328125, 14.73828125), 'health': 145.0, 'shield': 0.0, 'available_actions': ['stop', 'move_north', 'move_south', 'move_east', 'move_west'], 'unavailable_reason': ''}, 15: {'status': 'alive', 'unit_type': 'nydusCanal', 'coords': (61.5, 63.5), 'health': 300.0, 'shield': 0.0, 'available_actions': ['stop'], 'unavailable_reason': "The agent is Nyduscanal, action can only be 'stop'"}}

Simplified Obs Key: step, Sample Value: 0

