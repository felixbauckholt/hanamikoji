from enum import Enum, IntEnum
from multiset import FrozenMultiset
import random

from api import *
from engine import draw_cards, result_of_move, swap_sides # helpers for the bots
from engine import play_game, play_games # to run games

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

    def react_move3(self, gamestate, move, cards):
        return draw_cards(cards, 1)

    def react_move4(self, gamestate, move, cards_A, cards_B):
        return random.choice([cards_A, cards_B])

class KeriRandom(RobertRandom):
    "First hides highest card, then discards lowest cards, then plays 3 and 4; it reacts randomly"
    def choose_move(self, gamestate):
        mt = [mt for mt in MoveType if not gamestate.own_state.moves[mt]][0]
        hand = gamestate.own_state.hand
        if mt == MoveType.Move1:
            return Move1(cards=FrozenMultiset([max(hand)]))
        elif mt == MoveType.Move2:
            card1 = min(hand)
            card2 = min(hand - FrozenMultiset([card1]))
            return Move2(cards=FrozenMultiset([card1, card2]))
        elif mt == MoveType.Move3:
            return Move3(cards=draw_cards(hand, 3))
        elif mt == MoveType.Move4:
            cards_A = draw_cards(hand, 2)
            cards_B = draw_cards(hand - cards_A, 2)
            return Move4(cards_A=cards_A, cards_B=cards_B)

class SlightlySmarterKeri(KeriRandom):
    def react_move3(self, gamestate, move, cards):
        return FrozenMultiset([max(cards)])

def all_subsets(cards, n):
    l = list(cards)
    def helper(stuff, i, remaining):
        if remaining == 0:
            yield stuff
            return
        for j in range(i, len(l)):
            yield from helper(stuff + (l[j],), j+1, remaining-1)
    return set(map(FrozenMultiset, helper((), 0, n)))

def all_moves(gamestate): # returns a dict of all moves and a list of results after
                         # opponent's reaction
    moves = {}
    hand = gamestate.own_state.hand
    if not gamestate.own_state.moves[MoveType.Move1]:
        for cards in all_subsets(hand, 1):
            move = Move1(cards=cards)
            moves[move] = [result_of_move(gamestate, move)]
    if not gamestate.own_state.moves[MoveType.Move2]:
        for cards in all_subsets(hand, 2):
            move = Move2(cards=cards)
            moves[move] = [result_of_move(gamestate, move)]
    if not gamestate.own_state.moves[MoveType.Move3]:
        for cards in all_subsets(hand, 3):
            move = Move3(cards=cards)
            reacts = all_subsets(cards, 1)
            moves[move] = [result_of_move(gamestate, move, react) for react in reacts]
    if not gamestate.own_state.moves[MoveType.Move4]:
        for cards_A in all_subsets(hand, 2):
            for cards_B in all_subsets(hand-cards_A, 2):
                move = Move4(cards_A=cards_A, cards_B=cards_B)
                reacts = [cards_A, cards_B]
                moves[move] = [result_of_move(gamestate, move, react) for react in reacts]
    #print(len(moves))
    return moves

class GreedyPlayer(Player):
    """
    Iterates over all possible moves, and picks the one maximizing
    .evaluate(newstate), where newstate is the state after the move.

    If the opponent can react, it assumes that the opponent minimizes
    .evaluate(newstate).
    """

    def evaluate(self, gamestate):
        raise NotImplementedError()

    def evaluate_list(self, l): # evaluates a list the opponent can choose from
        return min(self.evaluate(gs) for gs in l)

    def choose_move(self, gamestate):
        # max with key is argmax by the way :P
        moves = all_moves(gamestate)
        return max(moves, key=lambda move:
                self.evaluate_list(moves[move]))

    def react_move3(self, gamestate, move, cards):
        # Note that move is the opponent's move, while gamestate is in "our perspective":
        # To simulate their move with our reaction, we have to swap sides twice
        reacts = all_subsets(cards, 1)
        return max(reacts, key=lambda react:
                self.evaluate(swap_sides(result_of_move(swap_sides(gamestate), move, react))))

    def react_move4(self, gamestate, move, cards_A, cards_B):
        reacts = [cards_A, cards_B]
        return max(reacts, key=lambda react:
                self.evaluate(swap_sides(result_of_move(swap_sides(gamestate), move, react))))

class ExampleGreedyPlayer(GreedyPlayer):
    "Wants all the Pink5s"

    def evaluate(self, gamestate):
        return (gamestate.own_state.played[Card.Pink5]
              + gamestate.own_state.hidden[Card.Pink5]
              - gamestate.opponent_state.played[Card.Pink5])

if __name__ == "__main__":
    print(play_game("Robert", RobertRandom, "Keri", SlightlySmarterKeri, print))
    print(play_games("Robert", RobertRandom, "Keri", SlightlySmarterKeri, 10000))
    #print(play_game("Robert", RobertRandom, "Greedy", ExampleGreedyPlayer, print))
    #print(play_games("Robert", RobertRandom, "Greedy", ExampleGreedyPlayer, 1000))
