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

1. Unit IDs in `obs` are INTEGERS.
2. `actions` must be a dict with exactly one action for every alive unit in `obs['ally']`.
3. Always validate desired actions against `unit_data['available_actions']`. If unavailable, prefer `'stop'` if present; otherwise pick the first available action.
4. Do NOT reference units, IDs, buildings, or fields not present in `obs`.
5. Trigger logic MUST be verifiable from `obs`. If the natural-language trigger is ambiguous or not determinable from `obs`, set `trigger_met = False`.
6. Do NOT output any text except the Python function. No explanations, no markdown, no comments outside the function. Output must start with `def execute(self, obs):`.

### AVAILABLE HELPERS

Use these helpers if present on `self`:

* self.get_units_by_type(units_dict, type_name)
* self.get_distance(pos1, pos2)
* self.find_closest_enemy(ally_pos, enemy_dict)
* self.get_move_direction(cur, target)
* self.validate(unit_id, action, obs)

If you call a helper `self.validate(...)` and return False, perhaps the terrain is preventing us from moving forward; consider exploring other available action directions.


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

### PHASE INSTRUCTION

Phase {current_event_idx + 1}/{len(events)}
Strategy: "{current_event['strategy']}"
Trigger (natural language): "{current_event['trigger']}"

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
3. Validate desired actions against `unit_data['available_actions']`. Fallback: 'stop' if available, else first available.
4. Do NOT invent units, IDs, or fields not present in `obs`.
5. If a persistent ID stored on `self` (e.g. self.bait_id) is missing from `obs['ally']`, treat it as dead and do not reference it for targeting or movement.
6. Trigger must be verifiable from `obs`. If ambiguous, set `trigger_met = False`.
7. Do NOT output any text except the Python function. The output must start with `def execute(self, obs):`.

### SNAPSHOT
```json
{json.dumps(current_obs, indent=2)}
```

### PHASE INSTRUCTION

Strategy: "{current_event['strategy']}"
Trigger (natural language): "{current_event['trigger']}"
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
* If you call a helper `self.validate(...)` and return False, perhaps the terrain is preventing us from moving forward; we could consider exploring other available action directions.

### SAFETY / DEBUGGING

* Avoid complex reasoning chains; prefer explicit, checkable conditions.
* Do not change variable names listed in existing persistent fields.

### OUTPUT CONSTRAINT (RESTATE)

* Output ONLY the Python function `def execute(self, obs):`. No extra text.
  """
   return prompt

