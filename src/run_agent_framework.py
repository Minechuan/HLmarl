

'''
Step 1: Load video and VLM model
(Can also load VLM exist respose for the video)
'''


'''
Step 2: Load agent_runner and repeat the main loop
'''


import datetime
from functools import partial
from math import ceil
import numpy as np
import os
import pprint
import time
import threading
import torch as th
from types import SimpleNamespace as SN
from utils.logging import Logger
from utils.timehelper import time_left, time_str
from os.path import dirname, abspath

# Registries
from runners import REGISTRY as r_REGISTRY
from components.transforms import OneHot




def run_agent(_run, _config, _log):
    # check args sanity
    _config = args_sanity_check(_config, _log)

    args = SN(**_config)
    args.device = "cuda" if args.use_cuda else "cpu"
    print(f"Using device {args.device}")


    # sacred is on by default

    # Run and train
    run_agent_framework(args=args)

    # Clean up after finishing
    print("Exiting Main")


def run_agent_framework(args):

    # Init runner so we can get env info
    runner = r_REGISTRY[args.runner](args=args)
    assert args.runner == "agent", "Only agent runner is supported in the current framework."


    print("Agent starting playing rounds".format(args.play_nepisode))

    


    battle_result_list = []
    episode_return_list = []
    print("#" * 20)
    for i in range(args.play_nepisode):
       
        print(f"Starting episode {i+1}/{args.play_nepisode}")
        battle_result, episode_return = runner.run()
        battle_result_list.append(battle_result)
        episode_return_list.append(episode_return)

        print(f"Episode {i+1} finished.\n")
        print("#" * 20)
    
    '''Summary of all episodes'''
    mean_won_rate = sum(1 for result in battle_result_list if result==True) / len(battle_result_list)
    print("All episodes completed.")
    print(f"Mean won rate: {mean_won_rate:.2f}")

    if args.save_replay:
        runner.save_replay()

    # Making sure framework really exits
    runner.close_env()
    os._exit(os.EX_OK)

    

def args_sanity_check(config, _log):

    # set CUDA flags
    # config["use_cuda"] = True # Use cuda whenever possible!
    if config["use_cuda"] and not th.cuda.is_available():
        config["use_cuda"] = False
        _log.warning("CUDA flag use_cuda was switched OFF automatically because no CUDA devices are available!")

    if config["test_nepisode"] < config["batch_size_run"]:
        config["test_nepisode"] = config["batch_size_run"]
    else:
        config["test_nepisode"] = (config["test_nepisode"]//config["batch_size_run"]) * config["batch_size_run"]

    # assert (config["run_mode"] in ["parallel_subproc"] and config["use_replay_buffer"]) or (not config["run_mode"] in ["parallel_subproc"]),  \
    #     "need to use replay buffer if running in parallel mode!"

    # assert not (not config["use_replay_buffer"] and (config["batch_size_run"]!=config["batch_size"]) ) , "if not using replay buffer, require batch_size and batch_size_run to be the same."

    # if config["learner"] == "coma":
    #    assert (config["run_mode"] in ["parallel_subproc"]  and config["batch_size_run"]==config["batch_size"]) or \
    #    (not config["run_mode"] in ["parallel_subproc"]  and not config["use_replay_buffer"]), \
    #        "cannot use replay buffer for coma, unless in parallel mode, when it needs to have exactly have size batch_size."

    return config
