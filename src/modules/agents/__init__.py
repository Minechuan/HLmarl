REGISTRY = {}

from .rnn_agent import RNNAgent
from .ff_agent import FFAgent
from .central_rnn_agent import CentralRNNAgent
from .n_rnn_agent import NRNNAgent


REGISTRY["rnn"] = RNNAgent
REGISTRY["ff"] = FFAgent

REGISTRY["central_rnn"] = CentralRNNAgent
REGISTRY["n_rnn"] = NRNNAgent