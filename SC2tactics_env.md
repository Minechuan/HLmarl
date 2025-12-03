# Environment Specification

## Observation Space

- **Local Observation (per agent)**
  - **21 dims**
    - 4: Movement availability (whether each direction is free)
    - 8: Grid information
    - 9: Terrain height information
  - **7 × n_enemy dims**
    - 1: Whether the enemy is attackable
    - 3: Enemy distance, Δx, Δy (if visible)
    - 2: Enemy HP and shield
    - 1: Enemy unit type
  - **7 × n_ally dims**
    - 3: Ally distance, Δx, Δy (if visible)
    - 2: Ally HP and shield
    - 1: Ally unit type
    - 1: Ally’s previous action
  - **3 dims**
    - 2: Self HP and shield
    - 1: Self unit type
  - **n_actions × n_ally dims**
    - Previous actions of all allies
  - **1 dim**
    - Current timestep (unused)

**Total Observation Dimension**

$$
\text{obs\_dim} = 21 + 7n_{\text{enemy}} + 7n_{\text{ally}} + 3 + n_{\text{actions}}n_{\text{ally}} + 1
$$

---

## Global State (Used in Mixer)

If `obs_instead_of_state = False`:

- **6 × n_ally dims**
  - For each ally:
    - HP
    - Cooldown (CD)
    - 2D distance to map center
    - Shield ratio
    - Unit type
- **n_actions × n_ally dims**
  - Previous actions of all allies
- **1 dim**
  - Current timestep

**Total State Dimension**

$$
\text{state\_dim} = 6n_{\text{ally}} + n_{\text{actions}}n_{\text{ally}} + 1
$$

If `obs_instead_of_state = True`: concatenated observations are used instead (not used).

---

## Reward Structure

### Battle Reward
$$
\text{reward} = (\text{damage\_to\_enemies} + \text{kill\_bonus}) - (\text{damage\_to\_self} + \text{death\_penalty})
$$

### End Reward
- `code = 1` if enemy is eliminated  
- `code = -1` if own team is eliminated  
- `code = 0` otherwise

**Sparse end reward (unused):**
- +1 each timestep on success  
- −1 each timestep on failure  

**Dense end reward (used):**
- +200 on win  
- −200 on loss  
