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
    parser = argparse.ArgumentParser(description='Play a two-player game of Durak.')
    parser.add_argument('-s', '--suits', type=int, default=4,
                        choices=[2, 3, 4], help="Number of suits to use")
    parser.add_argument('-c', '--cpus', type=int, default=1,
                        choices=[0, 1, 2], help="Number of computer players")
    parser.add_argument('-v', '--verbose', type=int, default=1,
                        choices=[0, 1, 2], help="Verbosity of prompts")
    parser.add_argument('-n', '--numGames', type=int, default=1,
                        help="Number of games to play")
    parser.add_argument('logFile', help="Where to save the game log file")
    return parser.parse_args()


def getDeck(numSuits):
    """
    Returns a shuffled deck of Durak cards, using |numSuits| different suits.
    Index 0 is the bottom of the deck, and index -1 is the top of the deck.
    """
    suits = Card.SUITS.keys()[:numSuits]
    
    deck = []
    for suit, rank in product(suits, Card.RANKS):
        deck.append(Card(suit, rank))
    random.shuffle(deck)
    return deck


def getPlayers(numCPUs, verbosity):
    if numCPUs == 0:
        return player.HumanPlayer(verbosity), player.HumanPlayer(verbosity)
    elif numCPUs == 1:
        return player.HumanPlayer(verbosity), player.CPUPlayer(verbosity)
    elif numCPUs == 2:
        return player.CPUPlayer(verbosity), player.CPUPlayer(verbosity)


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
    deck = getDeck(args.suits)
    trumpCard = deck.pop() 
    trumpSuit = trumpCard.suit
    deck.insert(0, trumpCard)
    log.newGame(trumpCard)

    pOne.refillHand(deck)
    pTwo.refillHand(deck)
    attacker, defender = getPlayOrder(pOne, pTwo, trumpSuit)
    attacker.isAttacker = True
    defender.isAttacker = False

    trashCards = []
    while True:
        if args.verbose == 2:
            print "\nTrump card: ", trumpCard
            print "Cards left: ", len(deck)
            print "%s cards left: " % pOne.name, len(pOne.hand)
            print "%s cards left: " % pTwo.name, len(pTwo.hand)

        log.newRound(len(deck), trashCards)
        table = []
        while True:
            attackCard = attacker.attack(table)
            defender.removeOpponentCard(attackCard)
            log.recordMove(attacker, attackCard, table)
            if not attacker.success or len(attacker.hand) == 0: break
            defendCard = defender.defend(table, trumpSuit)
            attacker.removeOpponentCard(defendCard)
            log.recordMove(defender, defendCard, table)
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
            attacker.isAttacker = True
            defender.isAttacker = False
        elif (attacker.success and not defender.success) or len(attacker.hand) == 0:
            if args.verbose >= 1:
                print "%s wins the round and remains the attacker." % attacker.name
            attacker.opponentHand.extend(table)
            defender.hand.extend(table)
            # TODO option for attacker to give additional cards
            attacker.refillHand(deck)
            defender.refillHand(deck)
            log.endRound(True)

        attacker.numOpponentCards = len(defender.hand)
        defender.numOpponentCards = len(attacker.hand)

    if len(defender.hand) == 0:
        if len(attacker.hand) == 1:
            attackCard = attacker.attack(table)
            log.recordMove(attacker, attackCard, table)
            if attacker.success:
                if args.verbose >= 1:
                    print "Tie game!"
                log.endRound(True)
                log.declareTie()
                return
        if args.verbose >= 1:
            print "%s wins!" % defender.name
        log.endRound(False)
        defender.wins += 1
        log.declareWinner(defender)
    elif len(attacker.hand) == 0:
        if len(defender.hand) == 1:
            defendCard = defender.defend(table, trumpSuit)
            log.recordMove(defender, defendCard, table)
            if defender.success:
                if args.verbose >= 1:
                    print "Tie game!"
                log.endRound(False)
                log.declareTie()
                return
        if args.verbose >= 1:
            print "%s wins!" % attacker.name
        log.endRound(True)
        attacker.wins += 1
        log.declareWinner(attacker)


def main():
    args = parseArgs()
    pOne, pTwo = getPlayers(args.cpus, args.verbose)
    log = logger.Logger(pOne, pTwo)
    for i in range(args.numGames):
        playGame(args, log, pOne, pTwo)
        pOne.reset()
        pTwo.reset()
    print "%s wins: %d / %d" % (pOne.name, pOne.wins, args.numGames)
    print "%s wins: %d / %d" % (pTwo.name, pTwo.wins, args.numGames)
    log.write(args.logFile, pretty=True)

if __name__ == '__main__':
    main()