from modules.agents import REGISTRY as agent_REGISTRY
from components.action_selectors import REGISTRY as action_REGISTRY
from .basic_controller import BasicMAC
import torch as th
from utils.rl_utils import RunningMeanStd
import numpy as np

# This multi-agent controller shares parameters between agents
class NMAC(BasicMAC): # 负责批量为所有环境中的所有 agent 选择动作。先构造输入，前向推理得到 Q 值或策略分布，再用动作选择器选动作。
    def __init__(self, scheme, groups, args):
        super(NMAC, self).__init__(scheme, groups, args)
        
    def select_actions(self, ep_batch, t_ep, t_env, bs=slice(None), test_mode=False):
        # Only select actions for the selected batch elements in bs
        avail_actions = ep_batch["avail_actions"][:, t_ep] # 当前环境步所有动作
        qvals = self.forward(ep_batch, t_ep, test_mode=test_mode) # 得到所有agent的Q值

        chosen_actions = self.action_selector.select_action(qvals[bs], avail_actions[bs], t_env, test_mode=test_mode)
        return chosen_actions

    def forward(self, ep_batch, t, test_mode=False):
        
        if test_mode:
            self.agent.eval()
            
        agent_inputs = self._build_inputs(ep_batch, t)
        # e.g. (8*18, 460) or (128*18, 460)
        assert len(agent_inputs.size()) == 2
        # Explore mode with parallel runners (batch_size_run * n_agents, e) -> (batch_size_run, n_agents, e)
        b, e = agent_inputs.size()
        agent_inputs = agent_inputs.view(ep_batch.batch_size, b // ep_batch.batch_size, e)
        avail_actions = ep_batch["avail_actions"][:, t]
        agent_outs, self.hidden_states = self.agent(agent_inputs, self.hidden_states)

        return agent_outs # (batch_size, n_agents, n_actions)