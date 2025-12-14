import copy
from components.episode_buffer import EpisodeBatch
#from controllers.n_controller import NMAC
from controllers.basic_controller import BasicMAC as NMAC
from components.action_selectors import categorical_entropy
from utils.rl_utils import build_gae_targets
import torch as th
from torch.optim import Adam
from utils.value_norm import ValueNorm

class PPOLearner:
    def __init__(self, mac, scheme, logger, args):
        self.args = args
        self.n_agents = args.n_agents
        self.n_actions = args.n_actions
        self.mac = mac
        self.logger = logger

        self.last_target_update_step = 0
        self.critic_training_steps = 0

        self.log_stats_t = -self.args.learner_log_interval - 1

        # a trick to reuse mac
        dummy_args = copy.deepcopy(args)
        dummy_args.n_actions = 1
        dummy_args.agent_output_type = "q" # 强制告诉 Critic：你不是输出动作概率的，你是输出普通数值的！这样 BasicController 就会把它当成普通 Q 值处理，跳过 Mask 逻辑
        self.critic = NMAC(scheme, None, dummy_args)
        self.params = list(mac.parameters()) + list(self.critic.parameters())

        self.optimiser = Adam(params=self.params, lr=args.lr)
        self.last_lr = args.lr

        self.use_value_norm = getattr(self.args, "use_value_norm", False)
        if self.use_value_norm:
            self.value_norm = ValueNorm(1, device=self.args.device)
        
    def train(self, batch: EpisodeBatch, t_env: int, episode_num: int):
        # Get the relevant quantities
        rewards = batch["reward"][:, :-1]
        actions = batch["actions"][:, :-1]
        terminated = batch["terminated"][:, :-1].float()
        mask = batch["filled"][:, :-1].float()
        mask[:, 1:] = mask[:, 1:] * (1 - terminated[:, :-1]) # 确保如果 Episode 提前结束了（terminated），后面的数据都被标记为无效。
        avail_actions = batch["avail_actions"][:, :-1]
        
        old_probs = batch["probs"][:, :-1]  # PPO 是比较 当前策略 和 旧策略。旧策略的概率是 Runner 跑的时候存在 Batch 里的，这里直接拿出来。
        old_probs[avail_actions == 0] = 1e-10 
        old_logprob = th.log(th.gather(old_probs, dim=3, index=actions.long())).detach() # probs 是所有动作的概率 [0.1, 0.2, 0.7...]，actions 是实际选的动作索引 [2]。这里提取出当时选的那个动作对应的概率。旧概率是常数，不需要计算梯度，必须切断反向传播。
        mask_agent = mask.unsqueeze(2).repeat(1, 1, self.n_agents, 1)
        
        # targets and advantages
        with th.no_grad():
            old_values = []
            self.critic.init_hidden(batch.batch_size)
            for t in range(batch.max_seq_length):
                agent_outs = self.critic.forward(batch, t=t)
                old_values.append(agent_outs)
            old_values = th.stack(old_values, dim=1) 

            if self.use_value_norm: # 默认用了
                value_shape = old_values.shape
                values = self.value_norm.denormalize(old_values.view(-1)).view(value_shape)

            advantages, targets = build_gae_targets(rewards.unsqueeze(2).repeat(1, 1, self.n_agents, 1), 
                    mask_agent, values, self.args.gamma, self.args.gae_lambda)

            if self.use_value_norm:
                targets_shape = targets.shape
                targets = targets.reshape(-1)
                self.value_norm.update(targets)
                targets = self.value_norm.normalize(targets).view(targets_shape)
        
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-6) # 把adv归一化成N(0,1), 稳定Actor梯度更新
        
        # PPO Loss, 这里开始更新参数
        for _ in range(self.args.mini_epochs):
            # Critic
            values = []
            self.critic.init_hidden(batch.batch_size)
            for t in range(batch.max_seq_length-1):
                agent_outs = self.critic.forward(batch, t=t)
                values.append(agent_outs)
            values = th.stack(values, dim=1) 

            # value clip
            values_clipped = old_values[:,:-1] + (values - old_values[:,:-1]).clamp(-self.args.eps_clip,
                                                                                self.args.eps_clip) # 限制 Critic 的更新幅度，不要偏离 old_values 太多

            # 0-out the targets that came from padded data
            td_error = th.max((values - targets.detach())** 2, (values_clipped - targets.detach())** 2)
            masked_td_error = td_error * mask_agent
            critic_loss = 0.5 * masked_td_error.sum() / mask_agent.sum() # 让 Critic 的预测值 V(s) 尽可能接近 真实回报 returns

            # Actor
            pi = []
            self.mac.init_hidden(batch.batch_size)
            for t in range(batch.max_seq_length-1):
                agent_outs = self.mac.forward(batch, t=t)
                pi.append(agent_outs)
            pi = th.stack(pi, dim=1)  # Concat over time

            pi[avail_actions == 0] = 1e-10
            pi_taken = th.gather(pi, dim=3, index=actions.long())
            log_pi_taken = th.log(pi_taken)
            
            ratios = th.exp(log_pi_taken - old_logprob)
            surr1 = ratios * advantages
            surr2 = th.clamp(ratios, 1-self.args.eps_clip, 1+self.args.eps_clip) * advantages
            actor_loss = -(th.min(surr1, surr2) * mask_agent).sum() / mask_agent.sum()
            
            # entropy
            entropy_loss = categorical_entropy(pi).mean(-1, keepdim=True) # mean over agents
            entropy_loss[mask == 0] = 0 # fill nan
            entropy_loss = (entropy_loss * mask).sum() / mask.sum()
            loss = actor_loss + self.args.critic_coef * critic_loss - self.args.entropy * entropy_loss / entropy_loss.item()

            # Optimise agents
            self.optimiser.zero_grad()
            loss.backward()
            grad_norm = th.nn.utils.clip_grad_norm_(self.params, self.args.grad_norm_clip)
            self.optimiser.step()


        if t_env - self.log_stats_t >= self.args.learner_log_interval:
            mask_elems = mask_agent.sum().item()
            self.logger.log_stat("advantage_mean", (advantages * mask_agent).sum().item() / mask_elems, t_env)
            self.logger.log_stat("actor_loss", actor_loss.item(), t_env)
            self.logger.log_stat("entropy_loss", entropy_loss.item(), t_env)
            self.logger.log_stat("grad_norm", grad_norm, t_env)
            self.logger.log_stat("lr", self.last_lr, t_env)
            self.logger.log_stat("critic_loss", critic_loss.item(), t_env)
            self.logger.log_stat("target_mean", (targets * mask_agent).sum().item() / mask_elems, t_env)
            self.log_stats_t = t_env


    def cuda(self):
        self.mac.cuda()
        self.critic.cuda()

    def save_models(self, path):
        self.mac.save_models(path)
        th.save(self.optimiser.state_dict(), "{}/agent_opt.th".format(path))

    def load_models(self, path):
        self.mac.load_models(path)
        # Not quite right but I don't want to save target networks
        self.optimiser.load_state_dict(th.load("{}/agent_opt.th".format(path), map_location=lambda storage, loc: storage))
