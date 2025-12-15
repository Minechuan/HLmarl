# Agent Framework Documentation

## Overview

**0.0 VLM Analysis**
Record gameplay videos of a human player (following the player’s perspective) and use the prompt provided below (modifying only the necessary content) to analyze the video, extracting victory conditions and a list of events.

**0.1 Human Fine-tuning**
Manually refine the VLM output to ensure accuracy and clarity. Move the victory condition and event list to `src/config/algs/llm.yaml`.

**0.2 Human Add Enemy ID Mapping**
Skip this step if `enemy_unit_id_dict` already exists in the map configuration.

Identify the corresponding enemy unit type IDs by running the environment or reading the map files (run any environment and print the enemy information). Reference: `smac/smac/env/sc2_tactics/constants/5.0.13/Units.json` to check all enemy IDs and their names.

For the corresponding environment in `smac/smac/env/sc2_tactics/maps/sc2_tactics_maps.py`, add the enemy unit type mapping `enemy_unit_id_dict`:

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

**0.3 LLM Design Action Interface (env specific)**
Using the prompt provided below, design the LLM-facing action interface functions `get_agent_avail_llm_actions(self, agent_id)` (bottom-up) and `get_agent_action_from_llm(self, agent_id, action_id)`. You need to copy the contents of `get_avail_agent_actions` and `get_agent_action`.

Manually integrate the generated functions into `smac/smac/env/sc2_tactics/star36env_xxxx.py`.

**0.4 Run LLM Commander**
Add your API keys to `src/config/algs/llm.yaml` and ensure you have access to the required models.

Run the agent framework with the following command (make sure the flag `use_agent_framework=True` is set):

```bash
python src/main.py --config=llm --env-config=sc2te with env_args.map_name=dhls_te use_tensorboard=False runner=agent save_replay=False --no-save use_agent_framework=True
```

add ``save_replay=True`` if you want to save replays.

Watch the replays using the following command (modify the path to your replay file accordingly):
```bash
python -m pysc2.bin.play --norender --replay ".../Replay/dhls_te_...SC2Replay"
```

---

## 1. VLM Prompt Design

```txt
The video shows a human StarCraft II player performing a high level strategy on a specific map. The player succeeds according to the scenario’s victory determination rules.

Our units, shown in {green: 1 Drone, 3 Larvae}.
Enemy units, shown in {red: 1 Photon Cannon, 1 Pylon}.

Please complete the following tasks:

victory: Identify which unit or building must be destroyed to achieve victory?

describe: Describe the basic structure the map as observable in the video.

analyse: Provide a unit-level analysis of how the player in the video executes the strategy and achieves the victory condition. In the analysis, use “our units” and “enemy units” to refer to the respective sides. If any unit uses a specific ability or maneuver, such as DepotLower or NydusCanalUnload, explicitly mention it (and its target, if it has one).

list: List the important discrete strategies executed by the players and their triggering conditions. In a format like:[{"strategy":..., "trigger":...},...].

Your output must be in English and strictly formatted as a JSON object:
{victory:..., description:..., analysis:..., list:...}

You can only analyze what is observable in the video. If any information is not observable, do not mention it in analysis.
```

---

## 2. Human in the Loop

Manually refine the VLM output to ensure accuracy and clarity. The more detailed the process description, the better the experimental results.

---

## 3. LLM Action Interface

### Bottom-up LLM Action Interface Design Prompt

```txt
You are modifying an SC2Env. Your task is to write exactly ONE Python function:

    get_agent_avail_llm_actions(self, agent_id)

The definitions of the following two functions WILL BE PROVIDED AFTER THIS PROMPT:
    - get_avail_agent_actions(self, agent_id)
    - get_agent_action(self, agent_id, action_id)

You MUST read and reason over their actual implementations before writing the new function.

----------------------------------------------------------------
Function contract
----------------------------------------------------------------
Return:
    avail_action_names, no_action_reason

1. avail_action_names
   - Type: List[str]
   - SC2 action name strings only (e.g. "move_east", "stop", "NydusCanalLoad")
   - Must reflect the agent’s truly available actions

2. no_action_reason
   - Type: str
   - Default: empty string ""

----------------------------------------------------------------
Rules for no_action_reason (strict)
----------------------------------------------------------------
3. no_action_reason MUST be NON-empty ONLY when:
   - The agent’s available actions are effectively limited to:
       a) only "no-op"
       b) only "stop"

4. Required explanations:
   - If only "no-op" is available:
       no_action_reason = "agent is dead"
   - If only "stop" is available:
       give a SPECIFIC reason inferred from the environment logic, e.g.:
         - "The agent is Pylon, action can only be 'stop'"
         - "The agent is loaded by nydusNetwork"

5. In ALL other cases:
   - no_action_reason MUST be "" (empty string)

----------------------------------------------------------------
Implementation constraints (critical)
----------------------------------------------------------------
6. You MUST NOT simply call get_avail_agent_actions and forward its result.
   - You MUST re-integrate its logic inside get_agent_avail_llm_actions
   - This is required to distinguish WHY only "no-op" or "stop" is available
     (e.g., HP <= 0, unit type has no movement ability, unit state is loaded)

7. Action names MUST be obtained programmatically via get_agent_action
   or existing environment mappings. Do NOT hard-code action names.

8. The function MUST be robust to:
   - dead agents
   - loaded / immobilized agents
   - unit-type constraints (e.g. buildings)
   - empty or None action sets

----------------------------------------------------------------
Output format (absolute)
----------------------------------------------------------------
- Output ONLY valid Python code
- Output ONLY the function definition
- No comments, no explanations, no markdown

----------------------------------------------------------------
Goal
----------------------------------------------------------------
Produce a concise, environment-faithful LLM-facing action interface
that exposes both available SC2 action names and precise reasons
when the agent is effectively unable to act.

```

### Top-down LLM Action Interface Design Prompt

```txt
You are given the following two functions from an SC2 environment, two functions WILL BE PROVIDED AFTER THIS PROMPT:

1. get_agent_avail_llm_actions(self, agent_id)  
   - Returns a list of action names (avail_action_names) and a no_action_reason string.  
2. get_avail_agent_actions(self, agent_id)  
   - Returns a vector of length n_actions, indicating which actions are actually available according to environment logic.

Your task is to write a **single Python function**:

    def map_action_name_to_one_hot(self, action_name):

Requirements:

1. Input:  
   - `action_name`: a string that may appear in `avail_action_names` returned by `get_agent_avail_llm_actions`.

2. Output:  
   - A list (or numpy array) of length `self.n_actions`, exactly matching the one-hot representation that `get_avail_agent_actions` would return if only this action were available.

3. Implementation constraints:  
   - Use a dictionary (or other mapping structure) internally to map known action names to their corresponding indices in the one-hot vector.  
   - Handle all standard SC2 action names, including movement, stop, no-op, Nydus actions, and attack actions of the form `attack_enemy_{target_id}`.  
   - Do NOT hard-code the entire output vector for every possible `target_id`; generate attack indices programmatically using `self.n_actions_no_attack`.  
   - Ensure the function is robust and consistent with the original environment logic.

4. Output format:  
   - Only output valid Python code.  
   - Only the function definition.  
   - No comments, no explanations, no markdown.

Goal:  
Produce a concise, reliable, and environment-faithful function that converts any LLM-facing action name into a one-hot vector fully consistent with `get_avail_agent_actions`.

```

---

## LLM Commander Prompt

Refer to the code in `src/components/agent_framework.py` and `src/components/llm_prompt.py` for implementation details.

At each iteration, the commander agent will generate a function, and that function can be executed.


