# SMAC SC2 Tactics Environment Specification

This document outlines the detailed definitions of **Observation**, **State**, and **Reward** in the SMAC environment, using the <span style="font-family: monospace; color: #d63384;">sdjx</span> map as a case study for specific dimension calculations.

---

## 1. Common Dimensions

When calculating the dimensions for State and Observation, the following variables depend on the specific map configuration:

*   **Unit Type Bits**: <span style="color: #0d6efd;">`max(ally_type, enemy_type)`</span> (Length of the One-hot encoding).
*   **Shield**: This dimension exists **only** if the race is **Protoss**; otherwise, it is not present.
*   **Visibility**: If a unit (ally or enemy) is out of sight range or dead, all its corresponding observation features are **zero**.

---

## 2. Observation Space (Local Observation per Agent)

The local observation information obtained by each agent at every timestep.

**General Dimension Formula:**
```math
\text{obs}_{\text{dim}} = 21 + 7 * n_{enemy} + 7 * n_{ally} + 3 + n_{actions} * n_{ally} + 1
```
*(Note: The coefficients 7/3/1 depend on the specific feature configuration, see table below).*

| Feature Category | Detail Item | Dimensions | Description |
| :--- | :--- | :--- | :--- |
| **Move Feats** | <span style="color: #6c757d;">*Sub-total*</span> | **21** | **Movement-related Perception** |
| | Availability | 4 | Move availability markers (North, South, East, West) |
| | Grid Info | 8 | Surrounding grid occupancy information |
| | Terrain Height | 9 | Terrain height data within field of view |
| **Enemy Feats** | <span style="color: #6c757d;">*Sub-total*</span> | **(5/6 + type_bits) × $N_{enemy}$** | **Enemy Unit Info in FOV** |
| | Attackable | 1 | Whether the enemy is within attack range |
| | Distance | 3 | Relative distance ($distance, \Delta x, \Delta y$) |
| | HP / Shield | <span style="color: #d63384;">1 or 2</span> | Health (Includes Shield if Protoss) |
| | Unit Type | `type_bits` | One-hot encoding of enemy unit type |
| **Ally Feats** | <span style="color: #6c757d;">*Sub-total*</span> | **(6/7 + type_bits + n_actions) × $N_{ally}$** | **Ally Unit Info in FOV** |
| | Visible | 1 | Ally is alive and within field of view |
| | Distance | 3 | Relative distance ($distance, \Delta x, \Delta y$) |
| | HP / Shield | <span style="color: #d63384;">1 or 2</span> | Health (Includes Shield if Protoss) |
| | Unit Type | `type_bits` | One-hot encoding of ally unit type |
| | Last Action | `n_actions` | one hot vector of this ally's last action |
| **Own Feats** | <span style="color: #6c757d;">*Sub-total*</span> | **1/2 + type_bits** | **Agent's Own State** |
| | HP / Shield | <span style="color: #d63384;">1 or 2</span> | Own Health (Includes Shield if Protoss) |
| | Unit Type | `type_bits` | One-hot encoding of own unit type |
| **Optional**| Timestep | 1 | Current timestep (Usually normalized) |
---

## 3. Global State (Used in Mixer)

The global state is typically used for Critic or Mixer networks. Its content depends on the parameter `obs_instead_of_state`.

### Case A: `obs_instead_of_state = False` (Standard)

The state vector is concatenated from the following components:

1.  **Ally State**: <span style="color: #198754;">`(4 + Shield + unit_type_bits) × n_ally`</span>
    *   HP, Cooldown, Rel X (to map center), Rel Y (to map center), Shield (if Protoss), Unit Type.
2.  **Enemy State**: <span style="color: #dc3545;">`(3 + Shield + unit_type_bits) × n_enemy`</span>
    *   HP, Rel X (to map center), Rel Y (to map center), Shield (if Protoss), Unit Type.
    *   *Note: Enemy state usually does not contain Cooldown.*
3.  **Last Actions**: <span style="color: #6c757d;">`n_actions × n_ally`</span> (One-hot of previous actions for all allies).
4.  **Timestep**: <span style="color: #6c757d;">`1`</span> (Optional).

### Case B: `obs_instead_of_state = True`

*   Directly concatenates the **Local Observations** of all agents to form the global state.

---

## 4. Reward Structure

### Battle Reward (Step-wise)
Calculation formula:
```math
R_{battle} = (Damage_{\Delta Enemy} + Bonus_{Kill}) - (Damage_{\Delta Self} + Penalty_{Death})
```

### End Reward (Episode Finish)
Extra reward granted based on the battle outcome.

*   **Status Code**:
    *   `1`: All enemies eliminated (Win)
    *   `-1`: All allies eliminated (Loss)
    *   `0`: Timeout or ongoing
*   **Sparse Reward**:
    *   <span style="background-color: #d1e7dd; color: #0f5132; padding: 2px 4px; border-radius: 4px;">+200 (Win)</span>
    *   <span style="background-color: #f8d7da; color: #842029; padding: 2px 4px; border-radius: 4px;">-200 (Loss)</span>
*   **Dense Reward**:
    *   +1 / -1 per timestep based on the result.

---

## 5. Case Study: `sdjx` Map

The following breakdown details the dimension calculation for the `sdjx` map.

### 5.1 Basic Configuration
*   **Agents**: `n_agents = 18` (Ally)
*   **Enemies**: `n_enemies = 17` (Enemy)
*   **Map Special Rules**:
    *   <span style="color: #dc3545; font-weight: bold;">[!]</span> **Medivacs** cannot perform heal/rescue operations in this config.
    *   <span style="color: #dc3545; font-weight: bold;">[!]</span> **Timestep** is NOT observable in either State or Observation.
    *   <span style="color: #dc3545; font-weight: bold;">[!]</span> **Last Action** information is NOT present in the Observation.

### 5.2 Action Space
*   **No-Attack Actions**: 6 (No-op, Stop, Move N/S/E/W)
*   **Total Actions**: <span style="font-weight: bold;">23</span> (`6 + 17 enemies`)

### 5.3 Dimensions & Flags
*   **Unit Type Bits**: <span style="color: #0d6efd;">6</span> (For One-hot encoding. Allies have 2 types, Enemies have 6 types; max is 6).
*   **Agent IDs**:
    *   0-13: Type 48
    *   14-17: Type 54
*   **Environment Parameters**:
    ```python
    param = {
        'obs_all_health': True,
        'obs_instead_of_state': False,
        'obs_last_action': False,  # Note: No last action in Observation
        'obs_own_health': True,
        'obs_pathing_grid': True,
        'obs_terrain_height': True,
        'obs_timestep_number': False,
    }
    ```

### 5.4 State Calculation (Global)

**State Shape Components:**

1.  **Ally Sub-state**: Shape `(18, 10)`
    *   **10 dims** = 4 (HP, CD, Rel_X, Rel_Y) + 6 (Unit Type)
    *   *(Note: Allies are Terran, no Shield)*
2.  **Enemy Sub-state**: Shape `(17, 10)`
    *   **10 dims** = 3 (HP, Rel_X, Rel_Y) + <span style="color: #d63384;">1 (Shield)</span> + 6 (Unit Type)
    *   *(Note: Enemies are Protoss, have Shield)*
3.  **Last Actions**: Shape `(18, 23)`
    *   18 agents × 23 possible actions

**Total State Shape**:
```math
\text{Total} = (18 * 10) + (17 * 10) + (18 * 23) = 180 + 170 + 414 = 764
```

### 5.5 Observation Calculation (Local)

**Observation Shape per Agent:**

1.  **Move Feats**: **21**
2.  **Enemy Feats**: Shape `(17, 12)`
    *   **12 dims** = 1 (Attackable) + 3 (Dist) + <span style="color: #d63384;">2 (HP+Shield)</span> + 6 (Type)
    *   Total: $17 \times 12 = 204$
3.  **Ally Feats**: Shape `(17, 11)`
    *   Exclude self ($18-1=17$).
    *   **11 dims** = 1 (Visible) + 3 (Dist) + 1 (HP) + 6 (Type) 
    *   *(Note: Allies have no Shield; Last Action is OFF per config)*
    *   Total: $17 \times 11 = 187$
4.  **Own Feats**: **7**
    *   **7 dims** = 1 (HP) + 6 (Type)

**Total Observation Shape**:
```math
\text{Total} = 21 + 204 + 187 + 7 = 419
```