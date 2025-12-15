# Prompt for agent framework

## VLM:


The video shows a human StarCraft II player performing a high level strategy on a specific map. The player succeeds according to the scenario’s victory determination rules.

Our units, shown in green: 1 Drone, 3 Larvae.
Enemy units, shown in red: 1 Photon Cannon, 1 Pylon.

Please complete the following tasks:

victory: Identify which unit or building must be destroyed to achieve victory?

describe: Describe the basic structure the map as observable in the video.

analyse: Provide a unit-level analysis of how the player in the video executes the strategy and achieves the victory condition. In the analysis, use “our units” and “enemy units” to refer to the respective sides. If any unit uses a specific ability or maneuver, such as DepotLower or NydusCanalUnload, explicitly mention it (and its target, if it has one).

list: List the important discrete strategies executed by the players and their triggering conditions. In a format like:[{"strategy":..., "trigger":...},...].

Your output must be in English and strictly formatted as a JSON object:
{victory:..., description:..., analysis:...}

You can only analyze what is observable in the video. If any information is not observable, do not mention it in analysis.



### Example Output (DHLS)： 






The video shows a human StarCraft II player performing a high level strategy on a specific map. The player succeeds according to the scenario’s victory determination rules.

Our units, shown in green: 9 Zerglings, 4 Roaches, 1 Hatchery, 1 Nydus Network, 1 Nydus Worm.
Enemy units, shown in red: 8 Marines, 2 Siege Tanks, 1 Command Center.

Please complete the following tasks:

victory: Identify which unit or building must be destroyed to achieve victory?

describe: Describe the basic structure the map as observable in the video.

analyse: Provide a unit-level analysis of how the player in the video executes the strategy and achieves the victory condition. In the analysis, use “our units” and “enemy units” to refer to the respective sides. If any unit uses a specific ability or maneuver, such as DepotLower or NydusCanalUnload, explicitly mention it (and its target, if it has one).

list: List the important discrete strategies executed by the players and their triggering conditions. In a format like:[{"strategy":..., "trigger":...},...].

Your output must be in English and strictly formatted as a JSON object:
{victory:..., description:..., analysis:...}

You can only analyze what is observable in the video. If any information is not observable, do not mention it in analysis.



```json

{
  "victory": "The victory condition is to destroy the enemy Command Center.",
  "description": "The map features a green, grassy terrain with elevation changes (cliffs). There are two distinct areas shown: a starting area for the Zerg player containing a Hatchery and Nydus Network, and a separate Terran base area located on a plateau or across a distance, fortified with a Command Center, Siege Tanks, and Marines.",
  "analysis": "The player executes a surprise infiltration strategy using the Nydus Network. Initially, the player loads 'our units' (4 Roaches and 9 Zerglings) into the Nydus Network. The player then utilizes the Nydus Network to summon a Nydus Worm (via the `NydusCanal` ability) directly inside the 'enemy units' base, positioning it immediately adjacent to the enemy Command Center and behind the defensive line of two Siege Tanks. \n\nAs the Nydus Worm emerges, the enemy Siege Tanks begin attacking it. The Nydus Worm acts as a decoy and damage sponge, absorbing the high-damage tank fire. Once the worm is fully active, the player uses the `NydusCanalUnload` ability. The Roaches are unloaded first to provide a durable front line, followed quickly by the swarming Zerglings. While the Nydus Worm takes the brunt of the initial defense, 'our units' close the distance, destroying the Siege Tanks and surrounding the Command Center. Although the Nydus Worm is eventually destroyed by the enemy fire, the Zerg army is successfully deployed and proceeds to destroy the enemy base.",
  "list": [
    {
      "strategy": "Nydus Infiltration",
      "trigger": "Availability of Nydus Network and target location within the enemy base."
    },
    {
      "strategy": "Rapid Army Deployment",
      "trigger": "Completion of the Nydus Worm construction (emergence)."
    },
    {
      "strategy": "Damage Absorption (Distraction)",
      "trigger": "Enemy Siege Tanks engaging the emerging Nydus Worm."
    },
    {
      "strategy": "Swarm Attack",
      "trigger": "Successful unloading of units into close proximity of enemy defenses."
    }
  ]
}
```

### Example Output (TLHZ):

The video shows a human StarCraft II player performing a high level strategy on a specific map. The player succeeds according to the scenario’s victory determination rules.

Our units, shown in green: 1 Drone, 3 Larvae.
Enemy units, shown in red: 1 Photon Cannon, 1 Pylon.

Please complete the following tasks:

victory: Identify which unit or building must be destroyed to achieve victory?

describe: Describe the basic structure the map as observable in the video.

analyse: Provide a unit-level analysis of how the player in the video executes the strategy and achieves the victory condition. In the analysis, use “our units” and “enemy units” to refer to the respective sides. If any unit uses a specific ability or maneuver, such as DepotLower or NydusCanalUnload, explicitly mention it (and its target, if it has one).

list: List the important discrete strategies executed by the players and their triggering conditions. In a format like:[{"strategy":..., "trigger":...},...].

Your output must be in English and strictly formatted as a JSON object:
{victory:..., description:..., analysis:...}

You can only analyze what is observable in the video. If any information is not observable, do not mention it in analysis.



```json
{
"victory": "The enemy Photon Cannon must be destroyed.",
"description": "The map features a high-ground industrial platform with metallic flooring. On the left side, there is a cliff edge overlooking a lower level. In the upper right corner, a resource cluster containing mineral fields and a Vespene gas geyser is visible.",
"analysis": "The player executes a 'proxy Spore' counter-strategy using a single **Drone**. Since Zerg defensive structures require 'creep' to be built, and there is no creep in the enemy's proxy location, the player's **Drone** first begins constructing a **Hatchery** near the enemy **Pylon** and building **Photon Cannon**. This action generates a patch of creep. Once the creep spreads, the player cancels the **Hatchery** construction, refunding the **Drone** and most of the minerals. The **Drone** immediately utilizes the lingering temporary creep to construct a **Spore Crawler**. When the **Spore Crawler** completes construction, it automatically attacks the enemy **Photon Cannon**. To ensure victory, the player also commands the **Drone** to attack the **Photon Cannon** with melee strikes, providing the necessary extra damage to destroy the enemy structure before the **Spore Crawler** is lost.",
"list": [
{"strategy": "Generate Creep via Proxy Hatchery", "trigger": "The need to build a Spore Crawler on enemy territory where no creep exists."},
{"strategy": "Cancel Building to Recover Resources", "trigger": "The creep has successfully spread, and the Hatchery is no longer needed."},
{"strategy": "Construct Offensive Spore Crawler", "trigger": "Temporary creep is available on the ground following the Hatchery cancellation."},
{"strategy": "Drone DPS Assist", "trigger": "The Spore Crawler finishes construction and engages the enemy Photon Cannon."}
]
}

```

## LLM: