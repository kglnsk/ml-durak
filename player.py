import random
import util

class Player(object):
    def __init__(self, verbose):
        self.hand = []
        self.name = random.randint(0, 1000000)
        self.verbose = verbose

    def attack(self, table):
        """
        Given |table| a list of cards on the table, where table[0] is the
        top card, the player can choose a valid attacking card to play, or
        give up the attack. self.success must be set to True or False depending
        on the player's action.
        """
        raise NotImplementedError("Abstract function requires overriding")

    def defend(self, table, trumpSuit):
        """
        Given |table| a list of cards on the table, where table[0] is the top
        card, and |trumpSuit|, the player can choose a valid defending card
        to play, or surrender to the attacker. self.success must be set to
        True or False depending on the player's action.
        """
        raise NotImplementedError("Abstract function requires overriding")

    def refillHand(self, deck):
        while len(self.hand) < 6 and len(deck) > 0:
            self.hand.append(deck.pop())
        self.hand.sort(key=lambda c: (c.suit, c.rank))
    
    def getAttackingCards(self, table):
        """
        Valid attacking cards are those of the same rank as any
        of the cards on the table.
        """
        validRanks = set([card.rank for card in table])
        return filter(lambda c: c.rank in validRanks, self.hand)

    def getDefendingCards(self, aCard, trumpSuit):
        """
        Valid defending cards are those of the same suit as the attacking card,
        but of higher rank. If the attacking card is not a trump card, any trump
        cards are also valid attacking cards.
        """
        cards = filter(lambda c: c.suit == aCard.suit and c.rank > aCard.rank,
                       self.hand)
        if aCard.suit != trumpSuit:
            cards.extend(filter(lambda c: c.suit == trumpSuit, self.hand))
        return cards
    

class HumanPlayer(Player):
    """
    Given a list of cards to play, the human player inputs the 0-based index
    of the card s/he wants to play.
    """
    def __init__(self, verbose):
        super(HumanPlayer, self).__init__(verbose)
        self.rename()

    def attack(self, table):
        if self.verbose >= 1:
            print "----ATTACK----"
            print "  Your hand: ", self.hand
            print "  The table: ", table

        if len(table) == 0:
            i = util.readIntegerInRange(0, len(self.hand), 
                                        "  Select a card to begin attack, %s: " % self.name)
            table.insert(0, self.hand.pop(i))
            self.success = True
        else:
            attackingOptions = self.getAttackingCards(table)
            if len(attackingOptions) == 0: 
                if self.verbose >= 1: 
                    print "  You cannot attack."
                self.success = False
                return
            
            print "  Attacking options: ", attackingOptions 
            i = util.readIntegerInRange(-1, len(attackingOptions),
                                        "  Select a card, %s (-1 to stop attack): " % self.name)
            if i == -1: 
                self.success = False
                return
            table.insert(0, attackingOptions[i])
            self.hand.remove(attackingOptions[i])
            self.success = True

        if self.verbose >= 2:
            print "  Your hand: ", self.hand
            print "  The table: ", table

    def defend(self, table, trumpSuit):
        if self.verbose >= 1:
            print "----DEFEND----"
            print "  Your hand: ", self.hand
            print "  The table: ", table
        
        defendingOptions = self.getDefendingCards(table[0], trumpSuit)
        if len(defendingOptions) == 0: 
            if self.verbose >= 1:
                print "  You cannot defend."
            self.success = False
            return

        print "  Defending options: ", defendingOptions
        i = util.readIntegerInRange(-1, len(defendingOptions),
                                    "  Select a card, %s (-1 to surrender): " % self.name)
        if i == -1:
            self.success = False
            return
        table.insert(0, defendingOptions[i])
        self.hand.remove(defendingOptions[i])
        self.success = True
         
        if self.verbose >= 2:
            print "  Your hand: ", self.hand
            print "  The table: ", table

    def rename(self):
        if self.verbose >= 1:
            print "Player %s, what would you like to call yourself?" % self.name

        name = raw_input()
        if name != '': self.name = name


class CPUPlayer(Player):
    def __init__(self, verbose):
        super(CPUPlayer, self).__init__(verbose)

    def attack(self, table):
        if self.verbose >= 1:
            print "----ATTACK----"

        if len(table) == 0:
            i = random.randint(0, len(self.hand) - 1)
            attackCard = self.hand.pop(i)
            table.insert(0, attackCard)
            self.success = True
        else:
            attackingOptions = self.getAttackingCards(table)
            if len(attackingOptions) == 0: 
                self.success = False
                print "  %s cannot attack." % self.name
                return
            
            i = random.randint(-1, len(attackingOptions) - 1)
            if i == -1: 
                self.success = False
                print "  %s gives up the attack." % self.name
                return
            attackCard = attackingOptions[i]
            table.insert(0, attackCard)
            self.hand.remove(attackCard)
            self.success = True
        print "  %s attacks with %s" % (self.name, attackCard)

    def defend(self, table, trumpSuit):
        if self.verbose >= 1:
            print "----DEFEND----"

        defendingOptions = self.getDefendingCards(table[0], trumpSuit)
        if len(defendingOptions) == 0: 
            self.success = False
            print "  %s cannot defend." % self.name
            return

        i = random.randint(-1, len(defendingOptions) - 1)
        if i == -1:
            self.success = False
            print "  %s surrenders." % self.name
            return
        table.insert(0, defendingOptions[i])
        self.hand.remove(defendingOptions[i])
        self.success = True
        print "  %s defends with %s" % (self.name, defendingOptions[i])

