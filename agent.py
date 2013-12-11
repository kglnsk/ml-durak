import random
import copy
import pickle
import numpy as np

import durak2 as dk
import util


class Agent(object):
    def getAttackCard(self, cards, game):
        raise NotImplementedError('Abstract function requires overriding')

    def getDefendCard(self, cards, game):
        raise NotImplementedError('Abstract function requires overriding')


class HumanAgent(Agent):
    def __init__(self, playerNum):
        self.playerNum = playerNum

    def printInfo(self, game):
        opponent = int(not self.playerNum)
        print 'Your hand: ', game.hand[self.playerNum]
        print 'The table: ', game.table
        print 'Trump suit: ', dk.Card.SUITS[game.trumpCard.suit]
        print '# cards left: ', len(game.deck)
        print '# opponent cards: ', len(game.hand[opponent])

    def getAttackCard(self, cards, game):
        self.printInfo(game)
        if cards[-1] != dk.Durak.END_ROUND:
            print 'Your options: ', cards
            index = util.readIntegerInRange(0, len(cards),
                                            'Select a card to begin attack: ')
        else:
            cards.remove(dk.Durak.END_ROUND)
            print 'Your options: ', cards
            index = util.readIntegerInRange(-1, len(cards) - 1,
                                            'Select a card to attack (-1 to stop): ')

        if index == -1:
            return dk.Durak.END_ROUND
        else:
            return cards[index]

    def getDefendCard(self, cards, game):
        self.printInfo(game)
        print 'Your options: ', cards
        index = util.readIntegerInRange(-1, len(cards) - 1,
                                        'Select a card to defend (-1 to surrender): ')
        if index == -1:
            return dk.Durak.END_ROUND
        else:
            return cards[index]


class RandomAgent(Agent):
    def getAttackCard(self, cards, game):
        return random.choice(cards)

    def getDefendCard(self, cards, game):
        return random.choice(cards)


class SimpleAgent(Agent):
    def policy(self, cards, trumpSuit):
        if cards[-1] == dk.Durak.END_ROUND:
            cards = cards[:-1]
        sortedCards = sorted(cards, key=lambda c: c.rank)
        trumpCards = filter(lambda c: c.suit == trumpSuit, sortedCards)
        nonTrumpCards = filter(lambda c: c.suit != trumpSuit, sortedCards)
        if len(nonTrumpCards) > 0:
            return nonTrumpCards[0]
        elif len(trumpCards) > 0:
            return trumpCards[0]
        else:
            return dk.Durak.END_ROUND

    def getAttackCard(self, cards, game):
        return self.policy(cards, game.trumpCard.suit)

    def getDefendCard(self, cards, game):
        return self.policy(cards, game.trumpCard.suit)


### LEARNING AGENTS


class ReflexAgent(Agent):
    def __init__(self, playerNum):
        self.playerNum = playerNum
        try:
            with open('reflex_attack.bin', 'r') as f_atk:
                self.w_atk = pickle.load(f_atk)
        except IOError:
            print 'ReflexAgent: Initializing new attack weights'
            self.w_atk = np.random.normal(0, 1e-2, (util.NUM_FEATURES,))

        try:
            with open('reflex_defend.bin', 'r') as f_def:
                self.w_def = pickle.load(f_def)
        except IOError:
            print 'ReflexAgent: Initializing new defense weights'
            self.w_def = np.random.normal(0, 1e-2, (util.NUM_FEATURES,))

    def setAttackWeights(self, atkWeights):
        self.w_atk = atkWeights

    def setDefendWeights(self, defWeights):
        self.w_def = defWeights

    def chooseAction(self, cards, game):
        return max(cards, key=lambda c: self.getValue(c, game))

    def getValue(self, card, game):
        gameClone = copy.deepcopy(game)
        gameClone.playCard(self.playerNum, card)
        state = gameClone.getState(self.playerNum)

        if state['isAttacker']:
            if card == dk.Durak.END_ROUND:
                state['isAttacker'] = False
                weights = self.w_def
            else:
                weights = self.w_atk
        else:
            weights = self.w_def
            state['hand'].addCards(state['table'].getCards())

        features = util.extractFeatures(state)
        return util.logisticValue(weights, features)

    def getAttackCard(self, cards, game):
        return self.chooseAction(cards, game)

    def getDefendCard(self, cards, game):
        return self.chooseAction(cards, game)


class SimpleEnhancedAgent(SimpleAgent):
    def __init__(self, playerNum):
        self.playerNum = playerNum
        self.depth = 2
        try:
            with open('simple_enhanced_attack.bin', 'r') as f_atk:
                self.w_atk = pickle.load(f_atk)
        except IOError:
            print 'SimpleEnhancedAgent: Initializing new attack weights'
            self.w_atk = np.random.normal(0, 1e-2, (util.NUM_FEATURES,))

        try:
            with open('simple_enhanced_defend.bin', 'r') as f_def:
                self.w_def = pickle.load(f_def)
        except IOError:
            print 'SimpleEnhancedAgent: Initializing new defense weights'
            self.w_def = np.random.normal(0, 1e-2, (util.NUM_FEATURES,))

    def setAttackWeights(self, atkWeights):
        self.w_atk = atkWeights

    def setDefendWeights(self, defWeights):
        self.w_def = defWeights

    def minimaxChoice(self, cards, game):
        opponent = int(not self.playerNum)
        a = float('-inf')
        b = float('+inf')
        return max(cards, key=lambda c:
                   self.getValueRec(opponent, game, c, self.depth, a, b))

    def getValueRec(self, agent, game, card, depth, alpha, beta):
        otherAgent = int(not agent)
        gameClone = copy.deepcopy(game)
        gameClone.playCard(otherAgent, card)
        if gameClone.roundOver():
            gameClone.endRound()

        if gameClone.gameOver() and gameClone.isWinner(self.playerNum):
            return 1
        elif gameClone.gameOver() and gameClone.isLoser(self.playerNum):
            return 0
        elif depth == 0:
            state = gameClone.getState(agent)
            features = util.extractFeatures(state)
            if agent == gameClone.attacker:
                weights = self.w_atk
            else:
                weights = self.w_def
            return util.logisticValue(weights, features)

        if otherAgent == self.playerNum:
            depth -= 1
        if agent == gameClone.attacker:
            cards = gameClone.getAttackOptions(agent)
        else:
            cards = gameClone.getDefendOptions(agent)

        if agent == self.playerNum:
            v = float('-inf')
            for card in cards:
                v = max(v, self.getValueRec(otherAgent, gameClone, card, depth, alpha, beta))
                if v >= beta:
                    return v
                alpha = max(alpha, v)
            return v
        else:
            v = float('+inf')
            for card in cards:
                v = min(v, self.getValueRec(otherAgent, gameClone, card, depth, alpha, beta))
                if v <= alpha:
                    return v
                beta = min(beta, v)
            return v

    def getAttackCard(self, cards, game):
        if len(game.deck) > 0:
            return super(self.__class__, self).getAttackCard(cards, game)
        elif len(cards) == 1:
            return cards[0]
        else:
            return self.minimaxChoice(cards, game)

    def getDefendCard(self, cards, game):
        if len(game.deck) > 0:
            return super(self.__class__, self).getDefendCard(cards, game)
        elif len(cards) == 1:
            return cards[0]
        else:
            return self.minimaxChoice(cards, game)