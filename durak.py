from itertools import product
import random
import argparse
import player

class Card:
    SUITS = [0, 1, 2, 3]
    SUIT_LETTERS = {0:'C', 1:'H', 2:'D', 3:'S'}
    ROYALS = {11:'J', 12:'Q', 13:'K', 14:'A'} 
    RANKS = [6, 7, 8, 9, 10, 11, 12, 13, 14]

    def __init__(self, suit, rank):
        self.rank = rank
        self.suit = suit
    
    def __repr__(self):
        rankString = Card.ROYALS.get(self.rank, str(self.rank))
        suitString = Card.SUIT_LETTERS.get(self.suit)
        return '<Card %s %s>' % (rankString, suitString)

    def __str__(self):
        rankString = Card.ROYALS.get(self.rank, str(self.rank))
        suitString = Card.SUIT_LETTERS.get(self.suit)
        return '%s of %s' % (rankString, suitString)


def parseArgs():
    parser = argparse.ArgumentParser(description='Play a two-player game of Durak.')
    parser.add_argument('--suits', type=int, default=4,
                        choices=[2, 3, 4], help="Number of suits to use")
    parser.add_argument('--cpus', type=int, default=0,
                        choices=[0, 1, 2], help="Number of computer players")
    parser.add_argument('--verbose', type=int, default=2,
                        choices=[0, 1, 2], help="Verbosity of prompts")
     
    return parser.parse_args()

def getDeck(numSuits):
    """
    Returns a shuffled deck of Durak cards, using |numSuits| different suits.
    Index 0 is the bottom of the deck, and index -1 is the top of the deck.
    """
    suits = Card.SUITS[:numSuits]
    
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

def main():
    args = parseArgs()

    deck = getDeck(args.suits)
    pOne, pTwo = getPlayers(args.cpus, args.verbose)
    trumpCard = deck.pop() 
    trumpSuit = trumpCard.suit
    deck.insert(0, trumpCard)
    
    # TODO choose who goes first
    attacker, defender = pOne, pTwo

    while (len(pOne.hand) > 0 and len(pTwo.hand) > 0) or len(deck) > 0:
        attacker.refillHand(deck)
        defender.refillHand(deck)
        
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
         
        if (defender.success and not attacker.success) or len(defender.hand) == 0:
            print "%s wins the round and gets to attack." % defender.name
            attacker, defender = defender, attacker
        elif (attacker.success and not defender.success) or len(attacker.hand) == 0:
            print "%s wins the round and remains the attacker." % attacker.name
            defender.hand.extend(table)
        
    # TODO handle ties
    # TODO print winner

if __name__ == '__main__':
    main()

