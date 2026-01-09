# Run Reinforcement Learning Experiments


## Training: To train the agents, you can use the following command:

refering to: https://github.com/oxwhirl/pymarl


```bash
python src/main.py --config=qatten --env-config=sc2te with env_args.map_name=sdjx_te use_tensorboard=True
```

Run a different algorithm, e.g., Qatten2:

```bash
python src/main.py --config=qatten2 --env-config=sc2te with env_args.map_name=sdjx_te use_tensorboard=True local_results_path="results_ENVNAME_qatten2"
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



## Deployment: To deploy the trained agents, you can use the following command:

``save_replay`` option allows saving replays of models which are loaded using ``checkpoint_path``. Once the model is successfully loaded, ``test_nepisode`` number of episodes are run on the test mode and a .SC2Replay file is saved in the Replay directory of StarCraft II. Please make sure to use the **episode runner** if you wish to save a replay, i.e., ``runner=episode``. The name of the saved replay file starts with the given ``env_args.replay_dir`` and ``env_args.replay_prefix`` (map_name if empty). Following is an example command to run a trained model and save the replay:

```bash
python src/main.py --config=qmix --env-config=sc2 with env_args.map_name=2s3z checkpoint_path=path/to/checkpoint test_nepisode=1 save_replay=True runner=episode env_args.save_replay_prefix=2s3z save_model=False use_tensorboard=False
```

