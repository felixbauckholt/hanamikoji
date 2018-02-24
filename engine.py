from collections import namedtuple
from enum import Enum
from multiset import FrozenMultiset
import random

from api import *

constant_None = lambda x: None

def modify_namedtuple(nt, **kwd): # apply some functions to entries of a namedtuple
    d = {key: f(getattr(nt, key))
            for (key, f) in kwd.items()}
    return nt._replace(**d)

def censor_cards(cards):
    return FrozenMultiset({Card.Unknown: len(cards)})

def censor_move(move):
    if move_type(move) in [MoveType.Move1, MoveType.Move2]:
        return modify_namedtuple(move, cards=censor_cards)
    return move

def censor_gamestate(gamestate, just_keys=False):
    gamestate = modify_namedtuple(gamestate,
        own_state      = lambda state: modify_namedtuple(state, key=constant_None),
        opponent_state = lambda state: modify_namedtuple(state, key=constant_None)
    )
    if just_keys: return gamestate
    return modify_namedtuple(gamestate,
        pile = censor_cards,
        opponent_state = lambda opponent_state:
            modify_namedtuple(opponent_state,
                hand=censor_cards,
                hidden=censor_cards,
                discarded=censor_cards)
    )

def draw_cards(cards, n):
    return FrozenMultiset(random.sample(list(cards), n))

def deal(oldstate=None, keys=None):
    if oldstate is not None:
        favors=[oldstate.own_state.favors, oldstate.opponent_state.favors]
        keys=[oldstate.own_state.key, oldstate.opponent_state.key]
    else:
        favors=[(0,)*7 for i in range(2)]
        assert(keys is not None)
    cards = all_cards
    empty = FrozenMultiset()
    states = []
    for i in range(2):
        hand = draw_cards(cards, 6)
        cards -= hand
        states.append(PlayerState(
            hand=hand,
            played=empty,
            hidden=empty,
            discarded=empty,
            favors=favors[i],
            key=keys[i],
            moves=(0,)*4,
            started=(i == 0)
        ))
    return GameState(own_state=states[0], opponent_state=states[1], pile=cards)

def swap_sides(gamestate):
    return gamestate._replace(own_state=gamestate.opponent_state, opponent_state=gamestate.own_state)


class GameEnd(Exception):
    def __init__(self, winner):
        self.winner = winner


def endgame(winner, players, log=constant_None):
    log("Player %s won!" % winner)
    for key, player in players.items():
        player.notify_gameover(key == winner)
    raise GameEnd(winner)

def draw(gamestate, players, log=constant_None):
    card = draw_cards(gamestate.pile, 1)
    players[gamestate.own_state.key].notify_draw(censor_gamestate(gamestate), card)
    log("Player %s drew card %s" % (gamestate.own_state.key, card))
    return modify_namedtuple(gamestate,
        pile = lambda x : x - card,
        own_state = lambda own_state :
            modify_namedtuple(own_state, hand = lambda x : x + card)
    )

def do_move(gamestate, players, log=constant_None):
    own_k = gamestate.own_state.key
    opp_k = gamestate.opponent_state.key
    censored_gs = censor_gamestate(gamestate)
    censored_opp_gs = censor_gamestate(swap_sides(gamestate))

    move = players[own_k].choose_move(gamestate)
    if not validate_move(gamestate, move):
        log("Player %s chose invalid move: %r" % (own_k, move))
        endgame(opp_k, players, log)
    players[opp_k].notify_move(censored_opp_gs, censor_move(move))
    log("Player %s chose move %s" % (own_k, move))

    hidden, discarded, own_played, opp_played = (no_cards,)*4
    mt = move_type(move)
    if mt == MoveType.Move1:
        hidden += move.cards
    elif mt == MoveType.Move2:
        discarded += move.cards
    elif mt == MoveType.Move3:
        react = players[opp_k].react_move3(censored_opp_gs, move.cards)
        if not (validate_cardset(react, size = 1) and react <= move.cards):
            log("Player %s chose invalid react_move3: %r" % (opp_k, react))
            endgame(own_k, players, log)
        players[own_k].notify_react_move3(censored_gs, move, react)
        log("Player %s chose react_move3 %s" % (opp_k, react))
        opp_played += react
        own_played += move.cards - react
    elif mt == MoveType.Move4:
        react = players[opp_k].react_move4(censored_opp_gs, move.cards_A, move.cards_B)
        if not (react == move.cards_A or react == move.cards_B):
            log("Player %s chose invalid react_move4: %r" % (opp_k, react))
            endgame(own_k, players, log)
        players[own_k].notify_react_move4(censored_gs, move, react)
        log("Player %s chose react_move4 %s" % (opp_k, react))
        opp_played += react
        own_played += (move.cards_A + move.cards_B) - react

    return modify_namedtuple(gamestate,
        own_state = lambda own_state : modify_namedtuple(own_state,
            hand      = lambda x : x - (hidden + discarded + own_played + opp_played),
            played    = lambda x : x + own_played,
            hidden    = lambda x : x + hidden,
            discarded = lambda x : x + discarded,
            moves     = lambda moves : tuple(b or (i == mt) for i, b in enumerate(moves))
        ),
        opponent_state = lambda opponent_state : modify_namedtuple(opponent_state,
            played = lambda x : x + opp_played
        )
    )

def play_round(gamestate, players, log=constant_None):
    log("State after dealing: %s" % (gamestate,))
    for gs in [gamestate, swap_sides(gamestate)]:
        players[gs.own_state.key].notify_deal(censor_gamestate(gs))
    for i in range(8):
        gamestate = draw(gamestate, players, log)
        gamestate = do_move(gamestate, players, log)
        gamestate = swap_sides(gamestate)

    assert(len(gamestate.pile) == 1)
    assert(gamestate.own_state.moves == gamestate.opponent_state.moves == (True,)*4)
    for gs in [gamestate, swap_sides(gamestate)]:
        players[gs.own_state.key].notify_reveal(censor_gamestate(gs, just_keys=True))

    # TODO: change favors, figure out if someone won
    log("Did somebody win? I'm too lazy to find out, let's just play another round...")
    return gamestate

def play_game(key_A, class_A, key_B, class_B, log=constant_None):
    players = {key_A: class_A(), key_B: class_B()}
    gamestate = deal(keys=[key_A, key_B])
    try:
        while True:
            gamestate = deal(swap_sides(play_round(gamestate, players, log)))
    except GameEnd as e:
        return e.winner

