import json

def get_initial_prompt(events, current_event_idx, victory_condition, current_obs):
   current_event = events[current_event_idx]

   prompt = f"""
You are an expert StarCraft II Commander AI. Produce a single Python function:

    def execute(self, obs):

that implements micro-management for the CURRENT PHASE and returns (actions, trigger_met).

### IMPORTANT USAGE NOTE
- The chat messages already contain prior conversation history (user prompts and assistant replies). If a previous assistant message includes a `def execute(self, obs):` function, you MUST *inherit* its function signature, persistent field names (e.g. self.bait_id), and `self.init_done` convention; modify only the logic required for the current phase. If no previous function exists, produce a full, self-contained `execute`.

### GLOBAL CONTEXT
Victory Condition: {victory_condition}
Mission Plan: {json.dumps(events, indent=2)}

### SNAPSHOT (use only fields present here)
```json
{json.dumps(current_obs, indent=2)}
````

### CRITICAL RULES (ENFORCE)

1. Unit IDs in `obs` are **INTEGERS**.

2. `actions` must be a **dict** with exactly **one action for every alive unit** in `obs['ally']`.

3. **Action Interface**: Each unit has its own `available_actions`.  
   You must choose **exactly one action** according to the rules below.

   - **MOVEMENT**  
     - If `'can_move'` in `available_actions`, you **may** output  
       `navigate_to_enemy_{id}` or `navigate_to_ally_{id}`  
     - `navigate_*` actions are **allowed even if not explicitly listed** in `available_actions`.

   - **ATTACK**  
     - If any action in `available_actions` starts with `attack`, you **may** choose one.  
     - The action **must be chosen directly from** `available_actions`  
       (e.g., `attack_enemy_0`). You must not add suffixes or modify the action name.

   - **SKILL USAGE**  
     - If a special skill exists in `available_actions`, you **may** choose it.  
     - The action **must be chosen directly from** `available_actions`  
       (e.g., `NydusCanalLoad`). You must not add suffixes or modify the action name.

   - **STOP (Mandatory)**  
     - If `available_actions == ['stop']`, you **must** return `stop`.

   - **NO-OP (Mandatory)**  
     - If `available_actions == ['no-op']` (unit is dead), you **must** return `no-op`.

4. Do **NOT** reference units, IDs, buildings, or fields not present in `obs`.

5. Trigger logic **MUST** be verifiable from `obs`.  
   If a natural-language trigger is ambiguous or not determinable from `obs`, set  
   `trigger_met = False`.

6. Do **NOT** output any text except the Python function.  
   - No explanations  
   - No markdown  
   - No comments outside the function  
   - Output **must start with**:
   ```python
   def execute(self, obs):

### AVAILABLE HELPERS

Use these helpers if present on `self`:

* self.get_units_by_type(units_dict, type_name) -> Returns a LIST of integer IDs (e.g. [1, 5]). Do NOT use .keys().
* self.get_distance(pos1, pos2) -> Returns Euclidean distance between two (x, y) positions.
* self.validate(unit_id, action, obs) # Use ONLY for checking ATTACK actions.


### REQUIRED CODE PATTERNS

* Initialization must use the exact pattern:
  if not hasattr(self, 'init_done'):
  self.init_done = True
  # assign persistent fields here (e.g. self.bait_id = <id>)
* At the end of the function include a safety fill to ensure `actions` covers all allies:
  for uid in obs['ally']:
  if uid not in actions:
  actions[uid] = 'stop' if 'stop' in obs['ally'][uid]['available_actions'] else obs['ally'][uid]['available_actions'][0]
* Final return: `return actions, trigger_met`

### PHASE INSTRUCTION (natural language)

* The Trigger is the condition that caused this phase to start.
* The Strategy describes the high-level plan for this phase.
* `trigger_met` must indicate whether the next phase's trigger condition is satisfied.

Phase {current_event_idx + 1}/{len(events)}
Trigger (This phase was triggered by): "{current_event['trigger']}"
Strategy: "{current_event['strategy']}"
Next Phase Trigger: "{events[current_event_idx + 1]['trigger'] if current_event_idx + 1 < len(events) else 'N/A'}"
Victory Condition: {victory_condition}


### EXPECTED STYLE

* Prefer simple, deterministic logic (attack if in range and attack action available; else move toward target).
* Use explicit checks: `if 'attack' in unit_data['available_actions'] and enemy_in_range: actions[uid] = 'attack'`.
* Keep code compact and robust.

### OUTPUT CONSTRAINT (RESTATE)

* Output ONLY the Python function `def execute(self, obs):` (no surrounding text).
* Must follow the initialization and final safety check patterns above.
  """
   return prompt

























def get_subsequent_prompt(events, current_event_idx, victory_condition, existing_memory_keys, current_obs):
   current_event = events[current_event_idx]
   prev_event = events[current_event_idx - 1]

   prompt = f"""
You are the StarCraft II Commander. Produce a single Python function:

    def execute(self, obs):

that implements micro-management for Phase {current_event_idx + 1} and returns (actions, trigger_met).

### CONTEXT: INHERIT FROM HISTORY
- The conversation history (user + assistant messages) is included in the chat. If a previous assistant message contains `def execute(self, obs):`, you MUST preserve that function's signature and any persistent field names listed in the history (e.g. attributes shown in existing_memory_keys). Do not rename those fields.
- If no previous function exists in history, generate a complete `execute` as in the initial prompt.

### CRITICAL RULES
1. Unit IDs in `obs` are INTEGERS.
2. `actions` must contain exactly one action for every alive unit in `obs['ally']`.
3. **Action Interface**: Each unit has its own `available_actions`.  
   You must choose **exactly one action** according to the rules below.

   - **MOVEMENT**  
     - If `'can_move'` in `available_actions`, you **may** output  
       `navigate_to_enemy_{id}` or `navigate_to_ally_{id}`  
     - `navigate_*` actions are **allowed even if not explicitly listed** in `available_actions` but 'can_move' is must listed in `available_actions`.

   - **ATTACK**  
     - If any action in `available_actions` starts with `attack`, you **may** choose one.  
     - The action **must be chosen directly from** `available_actions`  
       (e.g., `attack_enemy_0`). You must not add suffixes or modify the action name.

   - **SKILL USAGE**  
     - If a special skill exists in `available_actions`, you **may** choose it.  
     - The action **must be chosen directly from** `available_actions`  
       (e.g., `NydusCanalLoad`). You must not add suffixes or modify the action name.

   - **STOP (Mandatory)**  
     - If `available_actions == ['stop']`, you **must** return `stop`.

   - **NO-OP (Mandatory)**  
     - If `available_actions == ['no-op']` (unit is dead), you **must** return `no-op`.
4. Do NOT invent units, IDs, or fields not present in `obs`.
5. If a persistent ID stored on `self` (e.g. self.bait_id) is missing from `obs['ally']`, treat it as dead and do not reference it for targeting or movement.
6. Trigger must be verifiable from `obs`. If ambiguous, set `trigger_met = False`.
7. Do NOT output any text except the Python function. The output must start with `def execute(self, obs):`.

### SNAPSHOT
```json
{json.dumps(current_obs, indent=2)}
```

### PHASE INSTRUCTION (natural language)

* The Trigger is the condition that caused this phase to start.
* The Strategy describes the high-level plan for this phase.
* `trigger_met` must indicate whether the next phase's trigger condition is satisfied.

Trigger (This phase was triggered by): "{current_event['trigger']}"
Strategy: "{current_event['strategy']}"
Next Phase Trigger: "{events[current_event_idx + 1]['trigger'] if current_event_idx + 1 < len(events) else 'N/A'}"
Victory Condition: {victory_condition}

### EXISTING PERSISTENT FIELDS (from history)

{existing_memory_keys}

### REQUIRED BEHAVIORS / TEMPLATES

* Keep initialization pattern if present:
  if not hasattr(self, 'init_done'):
  self.init_done = True
  # preserve or set persistent fields only if they are not already present
* Ensure final integrity check to fill missing actions:
  for uid in obs['ally']:
  if uid not in actions:
  actions[uid] = 'stop' if 'stop' in obs['ally'][uid]['available_actions'] else obs['ally'][uid]['available_actions'][0]

### SAFETY / DEBUGGING

* Avoid complex reasoning chains; prefer explicit, checkable conditions.
* Do not change variable names listed in existing persistent fields.

### OUTPUT CONSTRAINT (RESTATE)

* Output ONLY the Python function `def execute(self, obs):`. No extra text.
  """
   return prompt

