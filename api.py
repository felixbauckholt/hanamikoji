from collections import namedtuple
from enum import Enum, IntEnum
from multiset import FrozenMultiset

# 0. Introduction
# ===============
#
# After a possibly unhealthy amout of fantasizing about doing this in Haskell, I
# noticed that Python 3 has namedtuples (which are basically algebraic data
# types amirite???), so I *might* have gone overboard in using them.

# 1. Cardsets
# ===========
#
# Every set of cards (even a single card) will be represented as a "cardset",
# that is, a FrozenMultiset of Card objects.
#
# Cardsets are nice, because you can freely use the operations + or -, as well
# as the "sub-multiset" relation <=.
#
# Whenever a card is hidden from a player, it is replaced by an "eighth color",
# Card.Unknown. I hope this is helpful because this means cardsets will always
# have the size you expect.

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

# 2. Moves
# ========
#
# Moves are just namedtuples. Each move object (that is, object of type Move*)
# has an associated move type MoveType.Move*. This move type will be used as a
# key to look up if you performed this move type already (note that IntEnum
# objects behave like ints).

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

# 3. Game states
# ==============

# Just namedtuple of namedtuples. Some state is redundant (for example, the
# fields .own_state.favors and .opponent_state.favors can be deduced from each
# other); the engine will take care of that.

PlayerState = namedtuple("PlayerState", [
    "hand",      # cardset
    "played",    # cardset
    "hidden",    # cardset
    "discarded", # cardset
    "favors",    # 7-tuple of -1 (opponent's favor), 0 (neutral) or 1 (player's favor),
                 #    one for each Card except Card.Unknown
    "moves",     # 4-tuple of False (not played yet) or True (played),
                 #    one for each MoveType
    "started",   # boolean (did the player start the round)
    "key"        # engine internal, will be replaced with None
])

GameState = namedtuple("GameState", ["own_state", "opponent_state", "pile"])

# 4. Players
# ==========

# You will write a subclass of Player, and pass that class (or a fancier factory
# object if you prefer) to the engine, which will create one instance per game.

# To remember what the opponent is doing, you will have to override the notify_*
# methods you care about and use mutable state (sorry). I hope I included enough
# information in each call to notify_* to make reasoning about what your
# opponent did fairly self-contained.

class Player(object):
    def __init__(self): # one instance of a player class per game
        pass

    def choose_move(self, gamestate):
        # return a move m such that validate_move(m, gamestate)
        raise NotImplementedError()

    def react_move3(self, gamestate, move, cards):
        # return a cardset c such that validate_cardset(c, size=1) and c <= cards
        raise NotImplementedError()

    def react_move4(self, gamestate, move, cards_A, cards_B):
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

    def notify_reveal(self, gamestate): # uncensored gamestate at the end of a
                                        # round, before updated favors
        pass

    def notify_gameover(self, won):
        pass

# 4.1 Valid moves
# ===============
#
# To conclude this, I'll specify what constitutes a valid move using the
# following code that's hopefully self-documenting. If it's not, please yell at
# me!

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
