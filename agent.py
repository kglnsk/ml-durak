import random
import math

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
        if dk.Durak.END_ROUND not in cards:
            print 'Your options: ', cards
            index = util.readIntegerInRange(0, len(cards),
                                            'Select a card to begin attack: ')
        else:
            cards.remove(dk.Durak.END_ROUND)
            print 'Your options: ', cards
            index = util.readIntegerInRange(-1, len(cards),
                                            'Select a card to attack (-1 to stop): ')

        if index == -1:
            return dk.Durak.END_ROUND
        else:
            return cards[index]

    def getDefendCard(self, cards, game):
        self.printInfo(game)
        cards.remove(dk.Durak.END_ROUND)
        print 'Your options: ', cards
        index = util.readIntegerInRange(-1, len(cards),
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
        sortedCards = sorted(cards, key=lambda c: c.rank)
        trumpCards = filter(lambda c: c.suit == trumpSuit, sortedCards)
        nonTrumpCards = filter(lambda c: c.suit != trumpSuit and c.suit != -1, sortedCards)
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


def logisticValue(weights, features):
    z = sum(weight * feature for weight, feature in zip(weights, features))
    return 1.0 / (1 + math.exp(-z))


class ReflexAgent(Agent):
    def __init__(self, atkWeights, defWeights):
        self.w_atk = atkWeights
        self.w_def = defWeights

    def chooseAction(self, cards, game, weights):
        pass

    def getAttackCard(self, cards, game):
        return self.chooseAction(cards, game, self.w_atk)

    def getDefendCard(self, cards, game):
        return self.chooseAction(cards, game, self.w_def)