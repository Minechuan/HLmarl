# Learning Human-like Strategies for Multi-agent Cooperation in StarCraft II

## 0. Introduction

This repository contains the code for the project "Learning Human-like Strategies for Multi-agent Cooperation in StarCraft II", which is built upon the [SMAC](https://github.com/oxwhirl/smac) environment.

This project is the final project for the course "Reinforcement Learning" of Peking University.


Our main contributions include:
* Experiments on advanced maps from **HLSMAC** benchmark, including 12 challenging maps with human-designed strategies.
* Improved training algorithms based on Qatten -- **Qatten2**.
* Implementation of an **agent framework** with LLM integration.

The agent framework pipeline is as follows:
![pipeline](./documents/pipeline.png)

## 1. Environment Setup

Below is a guidance to set up your development environment for the project (on linux). If you are using Windows, just download and install StarCraft II from Battle.net.


Based on course homework readme, you can set up the environment by following these steps:
1. Cloned this repository to your local machine.
   ```bash
   git clone --depth 1 https://github.com/Minechuan/HLmarl.git
   pip install -e smac/
   ```
2. Downloaded SC2 (linux version) from [github repository](https://github.com/Blizzard/s2client-proto). Unzip the downloaded file and place the extracted folder (e.g., ``StarCraftII``) into the ``3rdparty`` directory of this repository (Hint: password is in README.md).


3. Find the SC2 installation path, e.g., ``/path/to/StarCraft II/``. Move the **12** map files from ``StarCraft2_HLSMAC\Tactics_Maps\HLSMAC_Maps`` to the ``/path/to/StarCraft II/Maps/Tactics_Maps`` (created by yourself). Check the existing maps with:
   ```
   python -m smac.bin.map_list
   ```

4. Other required packages can be installed via:
   ```bash
   pip install -r requirements.txt
   ```

After these steps, you can validate the installation by running a simple test script provided in the repository or by executing a sample training run.

```bash
python src/main.py --config=qatten --env-config=sc2te with env_args.map_name=sdjx_te use_tensorboard=False save_replay=False save_model=False runner=episode batch_size_run=1
```

The ablove only saves sacred logs, just for testing whether the environment works. If you are debugging, you can add ``--no-save`` to avoid saving sacred logs.

## 2. Run the Experiments

### 2.1 Test the learner we have trained:

**Test Qatten2** (with checkpoint provided in ``checkpoints/qatten2``):

>We save the checkpoint whose won rate is not less than 30%. Choose \$NAME\$ from [gmzz_te, sdjx_te, swct_te, jdsr_te, wwjz_te, wzsy_te]

```bash
python src/main.py --config=qatten2 --env-config=sc2te with env_args.map_name=$NAME$ checkpoint_path=./checkpoints/qatten2/$NAME$ test_nepisode=32 save_replay=True runner=episode save_model=False use_tensorboard=False evaluate=True batch_size_run=1
```

**Test MAPPO** (with checkpoint provided in ``checkpoints/mappo``):

[TODO] 下面这条命令跑不通突然跑不通，需要重新试一下

```bash
python src/main.py --config=ippo --env-config=sc2te with env_args.map_name=gmzz_te use_tensorboard=False checkpoint_path=./checkpoints/mappo/gmzz_te test_nepisode=32 save_replay=True runner=episode save_model=False evaluate=True
```

**Test Agent Framework**:

First check if the API worsks:

```bash
python check_api.py
```

If you want to use your own API, modify ``src/config/algs/llm_dhls.yaml``.

Then run the agent framework on a map:

>Because of the limited times we only support following maps. If you want to test other maps, please refer to RUN_AGENT.md to change the necessary configurations.


```bash
python src/main.py --config=llm_dhls --env-config=sc2te with env_args.map_name=dhls_te use_tensorboard=False runner=agent save_replay=True --no-save use_agent_framework=True
```


### 2.2 Run your own experiments:

* If you want to train your own agents with reinforcement learning, please refer to [RUN_RL.md](./documents/RUN_RL.md).
* If you want to test the agents with human-like strategies on other maps, please refer to [RUN_AGENT.md](./documents/RUN_AGENT.md).


## 3. Record demonstration videos and replays

1. Set ``save_replay=True`` in the command line to save replays during testing.
2. Download replays from ``3rdparty/StarCraftII/Replays``.
3. Copy to Windows machine with StarCraft II installed. The detailed path rules are similar to TA's guidance.


## 4. Issues

**Path error**: Can't find the SC2 path. 

Copy to pymarl-like directory, because each pymarl-like repo often need to install starcraft in their own way. Or set the SC2 path manually in the config file or code.

Or link the SC2 path to the target path:

```bash
ln -s $StarCraftII_path$ ./3rdparty/StarCraftII
```


**Replay Error**:
```
ValueError: Unknown game version: 4.10.0. Known versions: ['latest']
```
Linux's replay has old version. Double click replay file. Game will install old version automatically.

If can not open:

```bash
# check replay version
python -m pysc2.bin.replay_version  .\jctq_te.SC2Replay
```
e.g., Version(game_version='5.0.14', build_version=94137, data_version='519EE8D06E384469C652DD58FC6016AC', binary=None)


```python
# update pysc2
# F:\project\Anaconda3\anaconda\envs\smac_env\Lib\site-packages\pysc2\run_configs\lib.py
# append

Version("5.0.14", 94137, "519EE8D06E384469C652DD58FC6016AC", None),
```



