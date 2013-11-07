import json
import player as p


class Logger:
    def __init__(self, pOne, pTwo):
        self.games = []
        self.players = [pOne.name, pTwo.name]

    def newGame(self, trumpCard):
        self.game = {'trump': trumpCard.asDict()}
        self.data = []

    def newRound(self, cardsLeft, trashCards):
        self.currentRound = {
            'cardsLeft': cardsLeft,
            'trashCards': [c.asDict() for c in trashCards],
            'turns': []
        }

    def recordMove(self, player, card, table):
        assert card is not None
        turnData = dict()
        turnData['player'] = int(player.name == self.players[1])  # 0 or 1
        turnData['opponentHand'] = [c.asDict() for c in player.opponentHand]
        turnData['nOpponentCards'] = player.numOpponentCards
        if card not in [p.Player.NO_VALID_MOVES, p.Player.PASS_TURN]:
            turnData['card'] = card.asDict()
            turnData['table'] = [c.asDict() for c in table[1:]]  # index 0 is player's move
            turnData['hand'] = [c.asDict() for c in player.hand] + [card.asDict()]
        else:
            turnData['card'] = card
            turnData['table'] = [c.asDict() for c in table]
            turnData['hand'] = [c.asDict() for c in player.hand]
        self.currentRound['turns'].append(turnData)

    def endRound(self, attackSuccess):
        self.currentRound['attackSuccess'] = attackSuccess
        self.data.append(self.currentRound)

    def declareWinner(self, winner):
        self.winner = int(winner.name == self.players[1])
        self.game['winner'] = self.winner
        self.game['data'] = self.data
        self.games.append(self.game)

    def declareTie(self):
        self.winner = -1
        self.game['winner'] = self.winner
        self.game['data'] = self.data
        self.games.append(self.game)

    def write(self, filename, pretty=False):
        with open(filename, 'w') as f:
            if pretty:
                f.write(json.dumps(self.games, sort_keys=True,
                                   indent=2, separators=(',', ': ')))
            else:
                f.write(json.dumps(self.games))