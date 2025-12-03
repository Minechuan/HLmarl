# Multi-Agent Reinforcement Learning (MARL)



## 0. Basic Reference 

Make sure to understand the environment before experiments


### SMAC Environment
The [StarCraft Multi-Agent Challenge (SMAC)](https://github.com/oxwhirl/smac) environment is a widely used benchmark for evaluating multi-agent reinforcement learning algorithms. It provides a set of scenarios where multiple agents must cooperate to achieve a common goal, such as defeating enemy units or completing tasks.

### pymarl

[pymarl](https://github.com/oxwhirl/pymarl) is a framework for implementing and testing multi-agent reinforcement learning algorithms. It provides a modular architecture that allows researchers to easily experiment with different algorithms, environments, and configurations.


### Other frameworks

Like [pymarl2](https://github.com/hijkzzz/pymarl2), [ReszQ](https://github.com/xmu-rl-3dv/ResQ/tree/main/ResZ/src), [wqmix](https://github.com/oxwhirl/wqmix), etc. they are all based on pymarl and provide implementations of various MARL algorithms and enhancements. So we suggest you to start with pymarl first. To train or test other exclusive algorithms, you can **refer to** their respective repositories for specific instructions. **Copy** the ``learners/xxx.py``, ``modules/xxx.py`` and ``config/algs/xxx.yaml`` to our codebase and make small adjustments, which is based on pymarl.


## 1. Environment Setup

Below is a guidance to set up your development environment for the project (on linux). If you are using Windows, just download and install StarCraft II from Battle.net.


Based on course homework readme, you can set up the environment by following these steps:


1. Down load and install StarCraft II. You can download it from [Blizzard's official website](https://starcraft2.com/en-us/download). After downloading, install the game and make sure it is working properly.
2. Install the required Python packages (I suggest conda env with python 3.9). Install the SMAC environment by running the following commands in your terminal:
   ```bash
   git clone https://github.com/oxwhirl/smac.git
   pip install -e smac/
   ```
3. Change ``smac\smac`` with the folder ``StarCraft2_HLSMAC\smac\smac``, which is unzipped from the ``StarCraft2_HLSMAC.zip`` downloaded from *PKU RL courses*.
4. Find the SC2 installation path, e.g., ``/path/to/StarCraft II/``. Move the **12** map files from ``StarCraft2_HLSMAC\Tactics_Maps\HLSMAC_Maps`` to the ``/path/to/StarCraft II/Maps/Tactics_Maps`` (created by yourself). 


list all available maps by running:

```bash
python -m smac.bin.map_list
```



## 2. Training: To train the agents, you can use the following command:

refering to: https://github.com/oxwhirl/pymarl#watching-starcraft-ii-replays


```bash
python3 src/main.py --config=qatten --env-config=sc2te with env_args.map_name=sdjx_te use_tensorboard=True
```

Run a different algorithm, e.g., Qatten2:

```bash
python3 src/main.py --config=qatten2 --env-config=sc2te with env_args.map_name=sdjx_te use_tensorboard=True local_results_path="results_ENVNAME_qatten2"
```

On Linux you can use parallel training. For example, to train with 1024 environments in parallel, you can use:

```yaml
# orinal config file:
runner: "episode" # Runs 1 env for an episode
batch_size_run: 1

# change to:
runner: "parallel" # Runs multiple envs in parallel
batch_size_run: 1024 # e.g., 1024
```


You can use ``use_tensorboard`` to visualize the training process in TensorBoard. 



## 3. Deployment: To deploy the trained agents, you can use the following command:

``save_replay`` option allows saving replays of models which are loaded using ``checkpoint_path``. Once the model is successfully loaded, ``test_nepisode`` number of episodes are run on the test mode and a .SC2Replay file is saved in the Replay directory of StarCraft II. Please make sure to use the **episode runner** if you wish to save a replay, i.e., ``runner=episode``. The name of the saved replay file starts with the given ``env_args.replay_dir`` and ``env_args.replay_prefix`` (map_name if empty). Following is an example command to run a trained model and save the replay:

```bash
python3 src/main.py --config=qmix --env-config=sc2 with env_args.map_name=2s3z checkpoint_path=path/to/checkpoint test_nepisode=1 save_replay=True runner=episode env_args.save_replay_prefix=2s3z save_model=False use_tensorboard=False
```

To watch the replay, you have two options:

1. Store the model checkpoint and copy it to Windows. Run on the above command on Windows machine.
2. Directly run on Linux machine. And copy the replay file to Windows machine.



To watch the replay, you can use following command on Windows machine/double click the replay file:

```bash
python -m pysc2.bin.play --norender --replay <path-to-replay>
```



## 4. Issues



**Stdout Error on Windows**

If you encounter an encoding error related to `stdout` while running the environment on Windows. Maybe the original config is output to a ``.txt`` file. You can change ``main.py`` to print to output to command directly.



**Path error**: Can't find the SC2 path. 

Copy to pymarl-like directory, because each pymarl-like repo often need to install starcraft in their own way. Or set the SC2 path manually in the config file or code.

Or link the SC2 path to the target path:

```bash
ln -s $StarCraftII_path$ ./3rdparty/StarCraftII
```


**kill** existing SC2 process:

```
killall -9 Main_Thread
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



