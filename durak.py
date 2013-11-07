from itertools import product
import random
import argparse
import player


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


def playGame(args, pOne, pTwo):
    deck = getDeck(args.suits)
    trumpCard = deck.pop() 
    trumpSuit = trumpCard.suit
    deck.insert(0, trumpCard)
    
    pOne.refillHand(deck)
    pTwo.refillHand(deck)
    attacker, defender = getPlayOrder(pOne, pTwo, trumpSuit)

    while True:
        if args.verbose == 2:
            print "\nTrump card: ", trumpCard
            print "Cards left: ", len(deck)
            print "%s cards left: " % pOne.name, len(pOne.hand)
            print "%s cards left: " % pTwo.name, len(pTwo.hand)

        table = []
        while True:
            attacker.attack(table)
            if not attacker.success or len(attacker.hand) == 0: break
            defender.defend(table, trumpSuit)
            if not defender.success or len(defender.hand) == 0: break

        if len(deck) == 0 and (len(defender.hand) == 0 or len(attacker.hand) == 0):
            break

        if (defender.success and not attacker.success) or len(defender.hand) == 0:
            if args.verbose >= 1:
                print "%s wins the round and gets to attack." % defender.name
            attacker.refillHand(deck)
            defender.refillHand(deck)
            attacker, defender = defender, attacker
        elif (attacker.success and not defender.success) or len(attacker.hand) == 0:
            if args.verbose >= 1:
                print "%s wins the round and remains the attacker." % attacker.name
            defender.hand.extend(table)
            attacker.refillHand(deck)
            defender.refillHand(deck)

    if len(defender.hand) == 0:
        if len(attacker.hand) > 1:
            if args.verbose >= 1:
                print "%s wins!" % defender.name
            defender.wins += 1
        else:
            attacker.attack(table)
            if attacker.success and args.verbose >= 1:
                print "Tie game!"
            else:
                if args.verbose >= 1:
                    print "%s wins!" % defender.name
                defender.wins += 1
    elif len(attacker.hand) == 0:
        if len(defender.hand) > 1:
            if args.verbose >= 1:
                print "%s wins!" % attacker.name
            attacker.wins += 1
        else:
            defender.defend(table, trumpSuit)
            if defender.success and args.verbose >= 1:
                print "Tie game!"
            else:
                if args.verbose >= 1:
                    print "%s wins!" % attacker.name
                attacker.wins += 1


def main():
    args = parseArgs()
    pOne, pTwo = getPlayers(args.cpus, args.verbose)
    for i in range(args.numGames):
        playGame(args, pOne, pTwo)
    print "%s: %d / %d" % (pOne.name, pOne.wins, args.numGames)
    print "%s: %d / %d" % (pTwo.name, pTwo.wins, args.numGames)

if __name__ == '__main__':
    main()