from enum import Enum, IntEnum
from multiset import FrozenMultiset
import random

from api import *
from engine import draw_cards, play_game

class RobertRandom(Player):
    "Plays randomly like Robert: First, it picks a move type, then it picks cards"

    def choose_move(self, gamestate):
        mt = random.choice([mt for mt in MoveType if not gamestate.own_state.moves[mt]])
        hand = gamestate.own_state.hand
        if mt == MoveType.Move1:
            return Move1(cards=draw_cards(hand, 1))
        elif mt == MoveType.Move2:
            return Move2(cards=draw_cards(hand, 2))
        elif mt == MoveType.Move3:
            return Move3(cards=draw_cards(hand, 3))
        elif mt == MoveType.Move4:
            cards_A = draw_cards(hand, 2)
            cards_B = draw_cards(hand - cards_A, 2)
            return Move4(cards_A=cards_A, cards_B=cards_B)

    def react_move3(self, gamestate, cards):
        return draw_cards(cards, 1)

    def react_move4(self, gamestate, cards_A, cards_B):
        return random.choice([cards_A, cards_B])

if __name__ == "__main__":
    print(play_game("RobertA", RobertRandom, "RobertB", RobertRandom, print))
