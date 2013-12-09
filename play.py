import argparse

import durak2 as dk
import agent


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Play a two-player game of Durak against a random-policy opponent.')
    parser.add_argument('-p', '--player', type=str, default='simple',
                        choices=['human', 'random', 'simple', 'reflex'], help="Player type")
    parser.add_argument('-v', '--verbose', type=int, default=1,
                        choices=[0, 1, 2], help="Verbosity of prompts")
    parser.add_argument('-n', '--numGames', type=int, default=1,
                        help="Number of games to play")
    parser.add_argument('-t', '--train', action='store_true', help='Train the AI')
    return parser.parse_args()


def train(args):
    pass


def attack(g, playerNum, agent):
    actions = g.getAttackOptions(playerNum)
    card = agent.getAttackCard(actions, g)
    g.playCard(playerNum, card)


def defend(g, playerNum, agent):
    actions = g.getDefendOptions(playerNum)
    card = agent.getDefendCard(actions, g)
    g.playCard(playerNum, card)


def play(g, agents):
    attacker = g.getFirstAttacker()
    defender = int(not attacker)
    while True:
        while True:
            attack(g, attacker, agents[attacker])
            if g.roundOver():
                break
            defend(g, defender, agents[defender])
            if g.roundOver():
                break

        if g.gameOver():
            break
        g.endRound()

        # Edge case: last round, the defender ran out of cards & the attacker got under
        # 6 cards. The attacker took the rest of the deck, so the defender (new attacker)
        # has 0 cards in his hand.
        if g.gameOver():
            break

        attacker = g.attacker
        defender = int(not attacker)

    return g.winner


def main(args):
    winCounts = [0, 0]
    g = dk.Durak()
    agents = [agent.RandomAgent(), agent.RandomAgent()]
    for _ in xrange(args.numGames):
        winner = play(g, agents)
        winCounts[winner] += 1
        g.newGame()
    print 'Win percentages:'
    print 'Player 1: %d/%d' % (winCounts[0], args.numGames)
    print 'Player 2: %d/%d' % (winCounts[1], args.numGames)


if __name__ == '__main__':
    args = parseArgs()
    if args.train:
        train(args)
    main(args)