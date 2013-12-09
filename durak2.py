from itertools import product
import random


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

    def __hash__(self):
        return hash((self.rank, self.suit))

    def __repr__(self):
        rankString = Card.ROYALS.get(self.rank, str(self.rank))
        suitString = Card.SUITS.get(self.suit, str(self.suit))
        return '<Card %s %s>' % (rankString, suitString)

    def __str__(self):
        rankString = Card.ROYALS.get(self.rank, str(self.rank))
        suitString = Card.SUITS.get(self.suit, str(self.suit))
        return '%s of %s' % (rankString, suitString)

    @staticmethod
    def getDeck(shuffle=True):
        """
        Returns a shuffled deck of Durak cards.
        Index 0 is the top of the deck, and index -1 is the bottom of the deck.
        """
        deck = []
        for suit, rank in product(Card.SUITS, Card.RANKS):
            deck.append(Card(suit, rank))
        if shuffle:
            random.shuffle(deck)
        return deck


class CardSet(object):
    def __init__(self):
        self.groupedByRank = {rank: set() for rank in Card.RANKS}
        self.groupedBySuit = {suit: set() for suit in Card.SUITS}
        self.size = 0

    def __len__(self):
        return self.size

    def __repr__(self):
        if self.size == 0:
            return '{}'

        cards = ''
        for rank in Card.RANKS:
            for card in self.groupedByRank[rank]:
                cards += repr(card) + ', '
        return '{%s}' % cards[:-2]  # remove last ', '

    def __str__(self):
        return repr(self)

    def addCard(self, card):
        if not isinstance(card, Card):
            raise TypeError

        self.groupedByRank[card.rank].add(card)
        self.groupedBySuit[card.suit].add(card)
        self.size += 1

    def addCards(self, cards):
        for card in cards:
            self.addCard(card)

    def removeCard(self, card):
        if not isinstance(card, Card):
            raise TypeError

        try:
            self.groupedByRank[card.rank].remove(card)
            self.groupedBySuit[card.suit].remove(card)
        except KeyError:
            return
        self.size -= 1

    def getCardsForSuit(self, suit):
        return self.groupedBySuit[suit]

    def getCardsForRank(self, rank):
        return self.groupedByRank[rank]


class Table(CardSet):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.cards = []
        self.seenRanks = set()

    def __len__(self):
        return len(self.cards)

    def __repr__(self):
        return repr(self.cards)

    def __str__(self):
        return str(self.cards)

    def addCard(self, card):
        super(self.__class__, self).addCard(card)
        self.cards.insert(0, card)
        self.seenRanks.add(card.rank)

    def getCards(self):
        return self.cards

    def getTopCard(self):
        return self.cards[0]

    def getSeenRanks(self):
        return self.seenRanks

    def clearTable(self):
        self.__init__()


class Durak:
    END_ROUND = Card(-1, -1)

    def __init__(self):
        self.newGame()

    def newGame(self):
        self.hand = [CardSet(), CardSet()]
        self.opponentHand = [CardSet(), CardSet()]  # for card counting
        self.deck = Card.getDeck()
        self.table = Table()
        self.trash = CardSet()
        self.attacker = None

        self.roundWinner = None
        self.winner = None

        self.trumpCard = self.deck.pop(0)
        self.deck.append(self.trumpCard)
        for _ in xrange(6):
            self.hand[0].addCard(self.deck.pop(0))
        for _ in xrange(6):
            self.hand[1].addCard(self.deck.pop(0))

    def getFirstAttacker(self):
        trumpsA = self.hand[0].getCardsForSuit(self.trumpCard.suit)
        trumpsB = self.hand[1].getCardsForSuit(self.trumpCard.suit)

        if len(trumpsA) == 0 and len(trumpsB) == 0:
            self.attacker = random.randint(0, 1)
        elif len(trumpsA) == 0:
            self.attacker = 1
        elif len(trumpsB) == 0:
            self.attacker = 0
        elif min(trumpsA, key=lambda c: c.rank) > min(trumpsB, key=lambda c: c.rank):
            self.attacker = 1
        else:
            self.attacker = 0

        return self.attacker

    def getAttackOptions(self, player):
        if len(self.table.getSeenRanks()) == 0:
            cards = []
            for rank in Card.RANKS:
                cards.extend(self.hand[player].getCardsForRank(rank))
        else:
            cards = [Durak.END_ROUND]
            for rank in self.table.getSeenRanks():
                cards.extend(self.hand[player].getCardsForRank(rank))
        return cards

    def getDefendOptions(self, player):
        topCard = self.table.getTopCard()
        cards = filter(lambda c: c.rank > topCard.rank,
                       self.hand[player].getCardsForSuit(topCard.suit))
        if topCard.suit != self.trumpCard.suit:
            cards.extend(self.hand[player].getCardsForSuit(self.trumpCard.suit))
        cards.append(Durak.END_ROUND)
        return cards

    def playCard(self, player, card):
        opponent = int(not player)
        if card == Durak.END_ROUND:
            self.roundWinner = opponent
            return

        self.hand[player].removeCard(card)
        self.opponentHand[opponent].removeCard(card)
        self.table.addCard(card)

        if len(self.hand[player]) == 0:
            self.roundWinner = player
            if len(self.deck) == 0:
                self.winner = player

    def refillHands(self):
        while len(self.hand[self.attacker]) < 6 and len(self.deck) > 0:
            self.hand[self.attacker].addCard(self.deck.pop(0))

        defender = int(not self.attacker)
        while len(self.hand[defender]) < 6 and len(self.deck) > 0:
            self.hand[defender].addCard(self.deck.pop(0))

    def endRound(self):
        defender = int(not self.attacker)
        if self.attacker == self.roundWinner:
            self.hand[defender].addCards(self.table.getCards())
            self.opponentHand[self.attacker].addCards(self.table.getCards())
        else:
            self.trash.addCards(self.table.getCards())

        self.table.clearTable()
        self.refillHands()
        if self.attacker != self.roundWinner:
            self.attacker = defender
        self.roundWinner = None

        # Edge case: last round, the defender ran out of cards & the attacker got under
        # 6 cards. The attacker took the rest of the deck, so the defender (new attacker)
        # has 0 cards in his hand.
        if len(self.hand[self.attacker]) == 0 and len(self.deck) == 0:
            self.winner = self.attacker

    def roundOver(self):
        # see playCard for deciding winners
        return self.roundWinner is not None

    def gameOver(self):
        # see playCard for deciding winners
        return self.winner is not None

    def winner(self):
        return self.winner

    def isWinner(self, player):
        return self.gameOver() and player == self.winner

    def isLoser(self, player):
        return self.gameOver() and player != self.winner