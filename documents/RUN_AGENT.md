# Agent Framework Documentation

## Overview -- The Agent Framework Pipeline


* [Important] For VLM has hallucination which has not been fixed yet We recommend to *skip* step 1,2 and *design* `src/config/algs/llm_$ENV$.yaml` directly based on your knowledge of the map.
* [Important] Step 1,2,3,4 are the steps before core reasoning module. The detailed prompt is in [Prompts Used before Core Reasoning Module](./pre_prompt.md)

### 1 VLM Analysis
Record gameplay videos of a human player (following the player’s perspective) and use the prompt provided below (modifying only the necessary content) to analyze the video, extracting victory conditions and a list of events.

### 2 Human Fine-tuning
Manually refine the VLM output to ensure accuracy and clarity. Move the victory condition and event list to `src/config/algs/llm_$ENV$.yaml`.

### 3 Human Add Enemy ID Mapping: *Necessary*
Skip this step if `enemy_unit_id_dict` already exists in the map configuration.

Identify the corresponding enemy unit type IDs by running the environment or reading the map files (run any environment and print the enemy information). Reference: `smac/smac/env/sc2_tactics/constants/5.0.13/Units.json` to check all enemy IDs and their names.

**For the corresponding environment in `smac/smac/env/sc2_tactics/maps/sc2_tactics_maps.py`, add the enemy unit type mapping `enemy_unit_id_dict`**: for example, for `dhls_te`, modify the configuration as follows:

```python
"dhls_te": {  
    "n_agents": 16,
    ...
    "map_type": "dhls",
    "support_info": {
        ...
        'enemy_unit_id_dict': {
            'CommandCenter': 18,
            'SiegeTank': 33,
            'Marine': 48,
        }
    }
},
```

### 4 LLM Design Action Interface (env specific) : *Necessary*
Using the prompt provided to design the LLM-facing action interface functions with llm assistance.
* `get_agent_avail_llm_actions(self, agent_id)` (bottom-up) and 
* `get_agent_action_from_llm(self, agent_id, action_id)`(top-down).

You need to copy the contents of `get_avail_agent_actions` and `get_agent_action` to feed these functions.

Manually integrate (paste) the generated functions into `smac/smac/env/sc2_tactics/star36env_xxxx.py`.

### 5 Run LLM Commander: *Necessary*
Add your API keys to `src/config/algs/llm_xxxx.yaml` and ensure you have access to the required models.

Run the agent framework with the following command (make sure the flag `use_agent_framework=True` is set):

```bash
python src/main.py --config=llm_xxxx --env-config=sc2te with env_args.map_name=xxxx_te use_tensorboard=False runner=agent save_replay=True --no-save use_agent_framework=True
```

