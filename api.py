from collections import namedtuple
from enum import Enum, IntEnum
from multiset import FrozenMultiset

class Card(IntEnum):
    Red2    = 0
    Yellow2 = 1
    Purple2 = 2
    Blue3   = 3
    Orange3 = 4
    Green4  = 5
    Pink5   = 6
    Unknown = 7

all_cards = FrozenMultiset({
    Card.Red2:    2,
    Card.Yellow2: 2,
    Card.Purple2: 2,
    Card.Blue3:   3,
    Card.Orange3: 3,
    Card.Green4:  4,
    Card.Pink5:   5
})
no_cards = FrozenMultiset()

Move1 = namedtuple("Move1", ["cards"])
Move2 = namedtuple("Move2", ["cards"])
Move3 = namedtuple("Move3", ["cards"])
Move4 = namedtuple("Move4", ["cards_A", "cards_B"])

class MoveType(IntEnum):
    Move1 = 0
    Move2 = 1
    Move3 = 2
    Move4 = 3

def move_type(move):
    return {
            Move1: MoveType.Move1,
            Move2: MoveType.Move2,
            Move3: MoveType.Move3,
            Move4: MoveType.Move4
    }.get(type(move), None)

PlayerState = namedtuple("PlayerState", [
    "hand",      # cardset
    "played",    # cardset
    "hidden",    # cardset
    "discarded", # cardset
    "favors",    # 7-tuple of -1 (opponent's favor), 0 (neutral) or 1 (player's favor)
    "moves",     # 4-tuple of False (not played yet) or True (played)
    "started",   # boolean (did the player start the round)
    "key"        # engine internal, replaced with None
])

GameState = namedtuple("GameState", ["own_state", "opponent_state", "pile"])

class Player(object):
    def __init__(self): # one instance of a player class per game
        pass

    def choose_move(self, gamestate):
        # return a move m such that validate_move(m, gamestate)
        raise NotImplementedError()

    def react_move3(self, gamestate, cards):
        # return a cardset c such that validate_cardset(c, size=1) and c <= cards
        raise NotImplementedError()

    def react_move4(self, gamestate, cards_A, cards_B):
        # return a cardset c such that c == cards_A or c == cards_B
        raise NotImplementedError()

    def notify_deal(self, gamestate):
        pass

    def notify_draw(self, oldstate, card):
        pass

    def notify_move(self, oldstate, move):
        pass

    def notify_react_move3(self, oldstate, own_move, card):
        pass

    def notify_react_move4(self, oldstate, own_move, cards):
        pass

    def notify_reveal(self, gamestate): # uncensored gamestate at the end of a round
        pass

    def notify_gameover(self, won):
        pass

def validate_cardset(cards, known = False, size = None):
    if not isinstance(cards, FrozenMultiset): return False
    if size is not None and len(cards) != size: return False
    for c in cards.distinct_elements():
        if not isinstance(c, Card): return False
        if known and c is Card.Unknown: return False
    return True

def validate_move(gamestate, move):
    mt = move_type(move)
    if mt is None: return False
    if gamestate.own_state.moves[mt]: return False
    if mt == MoveType.Move1:
        return validate_cardset(move.cards, known=True, size=1) and move.cards <= gamestate.own_state.hand
    if mt == MoveType.Move2:
        return validate_cardset(move.cards, known=True, size=2) and move.cards <= gamestate.own_state.hand
    if mt == MoveType.Move3:
        return validate_cardset(move.cards, known=True, size=3) and move.cards <= gamestate.own_state.hand
    if mt == MoveType.Move4:
        if not validate_cardset(move.cards_A, known=True, size=2): return False
        if not validate_cardset(move.cards_B, known=True, size=2): return False
        return move.cards_A + move.cards_B <= gamestate.own_state.hand
