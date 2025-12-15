## Agent Framework Runner



(For Minghan)

### [当前进度]

当前已经完成了 Agent Frame Work 的整个 pipeline，并在“调虎离山”环境中实现了许多测试，具体的代码参考的在 commit 7 中修改的代码。

对于 LLM 的 function 的 observation，可以参考: ``src/components/llm_prompt.py`` 和 ``src/prompt_example/simple_obs.md`。`

### [遇到的问题]

当前在调虎离山环境中，遇到了一个问题：

当前的智能体的目标是接近地方大本营，根据地图坐标 LLM Function 返回 north，但是当前地形原因智能体到了一个不能向北的悬崖，llm 输出 move north，不能执行，导致当前的**策略规划停滞**。整局都卡在这里。

(llm function) bait action: stop
bait available actions: ['stop', 'move_south', 'move_east', 'move_west']

已经做过的尝试：

1. 给 LLM 更加完善的 prompt，见 ``src/components/llm_prompt.py``。目前认为已经完备。
2. 使用细粒度的描述，减少 trigger 的冲突。见 ``src/config/algs/llm.yaml``，目前已经完善。

### 需要你做的


#### 继续抽象 action space 

可能的解决方案：给大语言模型的 available action 中的 *move+方向** 抽象成靠近、原理某一个己方、敌方单位。在 LLM Function 的输出之后，规划路径。因为 LLM 的 Function 是盲人摸象，不可能探索出一条路径。

> 1. 你需要在 ``smac/smac/env/sc2_tactics/sc2_tactics_env.py`` 中 get_llm_info_dict 函数中对得到的 agents_avail_actions 再进行一次抽象，变成*是否可移动+技能（已经有）*,这一步是很容易的。
>2. 你需要在 ``src/components/agent_framework.py`` 中实现一个路径规划（读取地图，写一个路径规划算法）的函数，输入是当前的 LLM Function 返回的的上层 action（靠近，原理），输出是一个可行的方向（move_north, move_south, move_east, move_west，需要和 available action 对齐）。
>3. 你需要修改 ``src/components/llm_prompt.py`` 中的 prompt，加入新的 available action 的描述。


在这样的设计下，把调虎离山调通是没有问题的。

#### 测试其他环境

由于有的环境 trigger 是隐式的（欲情故纵），不好描述。还有一些环境非常难（偷梁换柱），暂时先不在这些环境下测试。建议你测试(声东击西：可以看看视频自己设置 event 和胜利的条件，但是需要精确的描述：例如*摧毁距离多数 agent 最近的敌方水晶塔*)，确保我们的 pipeline 是可以应用于多个环境的。



### 一定要看：

* 我买了 api key，之后可以找我。
* 随时可以和我讨论。
* 你需要先阅读并理解 [agent_framework.md](agent_framework.md)，以掌握当前 pipeline 的工作流程。
* 你需要看 [src/components/llm_prompt.py](src/components/llm_prompt.py)，理解 prompt 是如何设计的。
* 你需要看 [src/components/agent_framework.py](src/components/agent_framework.py)，理解 agent framework 是如何实现的。

