from enum import Enum, IntEnum
from multiset import FrozenMultiset
import random

from api import *
from engine import draw_cards, result_of_move, swap_sides # helpers for the bots
from engine import play_game, play_games # to run games
from basic_players import GreedyPlayer

class Felix(GreedyPlayer)
