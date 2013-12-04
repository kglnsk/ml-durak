from itertools import product
import random
import argparse
import player
import logger


class Card:
    SUITS = {0: 'C', 1: 'H', 2: 'D', 3: 'S'}
    ROYALS = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
    RANKS = range(6, 14 + 1)

    def __init__(self, suit, rank):
        self.rank = rank
        self.suit = suit

    def __eq__(self, other):
        return \
            isinstance(other, self.__class__) and \
            self.rank == other.rank and \
            self.suit == other.suit

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        rankString = Card.ROYALS.get(self.rank, str(self.rank))
        suitString = Card.SUITS[self.suit]
        return '<Card %s %s>' % (rankString, suitString)

    def __str__(self):
        rankString = Card.ROYALS.get(self.rank, str(self.rank))
        suitString = Card.SUITS[self.suit]
        return '%s of %s' % (rankString, suitString)

    def asDict(self):
        return {'suit': self.suit, 'rank': self.rank}


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Play a two-player game of Durak against a random-policy opponent.')
    parser.add_argument('-p', '--player', type=str, default='simple',
                        choices=['human', 'random', 'simple', 'reflex'], help="Player type")
    parser.add_argument('-v', '--verbose', type=int, default=1,
                        choices=[0, 1, 2], help="Verbosity of prompts")
    parser.add_argument('-n', '--numGames', type=int, default=1,
                        help="Number of games to play")
    parser.add_argument('-l', '--logFile', help="Where to save the game log file")
    return parser.parse_args()


def getDeck(shuffle=True):
    """
    Returns a shuffled deck of Durak cards, using |numSuits| different suits.
    Index 0 is the bottom of the deck, and index -1 is the top of the deck.
    """
    
    deck = []
    for suit, rank in product(Card.SUITS, Card.RANKS):
        deck.append(Card(suit, rank))
    if shuffle:
        random.shuffle(deck)
    return deck


def getPlayers(playerType, verbosity):
    baselinePlayer = player.SimpleCPUPlayer(verbosity)
    if playerType == 'random':
        return player.RandomCPUPlayer(verbosity), baselinePlayer
    elif playerType == 'human':
        return player.HumanPlayer(verbosity), baselinePlayer
    elif playerType == 'simple':
        return player.SimpleCPUPlayer(verbosity), baselinePlayer
    elif playerType == 'reflex':
        return player.ReflexCPUPlayer(verbosity), baselinePlayer


def getPlayOrder(pOne, pTwo, trumpSuit):
    """
    Returns a tuple of (attacker, defender). The first player to attack is the
    player with the lowest ranking trump card in their hand. Used at the very
    beginning of a game of Durak.
    """
    pOneTrumps = filter(lambda c: c.suit == trumpSuit, pOne.hand)
    pTwoTrumps = filter(lambda c: c.suit == trumpSuit, pTwo.hand)
    
    if len(pOneTrumps) == 0 and len(pTwoTrumps) == 0:
        return pOne, pTwo
    elif len(pOneTrumps) == 0:
        return pTwo, pOne
    elif len(pTwoTrumps) == 0:
        return pOne, pTwo
    elif pOneTrumps[0].rank < pTwoTrumps[0].rank:
        return pOne, pTwo
    else:
        return pTwo, pOne


def playGame(args, log, pOne, pTwo):
    deck = getDeck()
    trumpCard = deck.pop() 
    trumpSuit = trumpCard.suit
    deck.insert(0, trumpCard)
    log.newGame(trumpCard)

    pOne.refillHand(deck)
    pTwo.refillHand(deck)
    attacker, defender = getPlayOrder(pOne, pTwo, trumpSuit)
    attacker.isAttacker = True
    defender.isAttacker = False

    table = []
    trashCards = []
    while True:
        if args.verbose >= 1:
            print "\nTrump card: ", trumpCard
            print "Cards left: ", len(deck)
        if args.verbose == 2:
            print "%s cards left: " % pOne.name, len(pOne.hand)
            print "%s cards left: " % pTwo.name, len(pTwo.hand)

        log.newRound(len(deck), trashCards)
        while True:
            attackCard = attacker.attack(table, trumpCard, len(deck),
                                         len(defender.hand), trashCards)
            defender.removeOpponentCard(attackCard)
            log.recordMove(attacker, defender, attackCard, table)
            if not attacker.success or len(attacker.hand) == 0: break

            defendCard = defender.defend(table, trumpCard, len(deck),
                                         len(attacker.hand), trashCards)
            attacker.removeOpponentCard(defendCard)
            log.recordMove(defender, attacker, defendCard, table)
            if not defender.success or len(defender.hand) == 0: break

        if len(deck) == 0 and (len(defender.hand) == 0 or len(attacker.hand) == 0):
            break

        if (defender.success and not attacker.success) or len(defender.hand) == 0:
            if args.verbose >= 1:
                print "%s wins the round and gets to attack." % defender.name
            trashCards.extend(table)
            attacker.refillHand(deck)
            defender.refillHand(deck)
            log.endRound(False)
            attacker, defender = defender, attacker
        elif (attacker.success and not defender.success) or len(attacker.hand) == 0:
            if args.verbose >= 1:
                print "%s wins the round and remains the attacker." % attacker.name
            attacker.addOpponentCards(table)
            defender.addCards(table)
            # TODO option for attacker to give additional cards
            attacker.refillHand(deck)
            defender.refillHand(deck)
            log.endRound(True)

        # Edge case: last round, the defender ran out of cards & the attacker got under
        # 6 cards. The attacker took the rest of the deck, so the defender (new attacker)
        # has 0 cards in his hand.
        if len(deck) == 0 and len(attacker.hand) == 0:
            break
        table = []

    if len(defender.hand) == 0:
        if len(attacker.hand) == 1:
            attackCard = attacker.attack(table, trumpCard, 0, 0, trashCards)
            log.recordMove(attacker, defender, attackCard, table)
            if attacker.success:
                if args.verbose >= 1:
                    print "Tie game!"
                log.endRound(True)
                log.declareTie()
        else:
            if args.verbose >= 1:
                print "%s wins!" % defender.name
            log.endRound(False)
            defender.wins += 1
            log.declareWinner(defender)
    elif len(attacker.hand) == 0:
        if len(defender.hand) == 1:
            defendCard = defender.defend(table, trumpCard, 0, 0, trashCards)
            log.recordMove(defender, attacker, defendCard, table)
            if defender.success:
                if args.verbose >= 1:
                    print "Tie game!"
                log.endRound(False)
                log.declareTie()
        else:
            if args.verbose >= 1:
                print "%s wins!" % attacker.name
            log.endRound(True)
            attacker.wins += 1
            log.declareWinner(attacker)


def main():
    args = parseArgs()
    player.ReflexCPUPlayer.loadWeights()

    pOne, pTwo = getPlayers(args.player, args.verbose)
    log = logger.Logger(pOne, pTwo)
    for i in range(args.numGames):
        playGame(args, log, pOne, pTwo)
        pOne.reset()
        pTwo.reset()
    print "%s wins: %d / %d" % (pOne.name, pOne.wins, args.numGames)
    print "%s wins: %d / %d" % (pTwo.name, pTwo.wins, args.numGames)

    if args.logFile:
        log.write(args.logFile, pretty=True)
    player.ReflexCPUPlayer.writeWeights()

if __name__ == '__main__':
    main()