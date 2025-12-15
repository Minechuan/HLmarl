# Human refinement of LLM agent action interface


## Original VLM output:

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


## After human refinement:

{
    "strategy": "Randomly select a Zergling as bait. Other Zerglings and Roaches move toward the enemy base. The Nydus Network loads the other Zerglings and the Roach into the Nydus Worm.",
    "trigger": "At the start of the battle."
},
{
    "strategy": "Unload all units from the Nydus Canal.",
    "trigger": "The bait Zergling is attacked."
},
{
    "strategy": "Attack the enemy Command Center.",
    "trigger": "All units have been unloaded from the Nydus Canal."
}




