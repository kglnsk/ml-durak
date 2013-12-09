import argparse
import random
import pickle

import durak2 as dk
import agent


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Play a two-player game of Durak against a random-policy opponent.')
    parser.add_argument('-a', '--agent', type=str, default='simple',
                        choices=['human', 'random', 'simple', 'reflex'], help="Agent type")
    parser.add_argument('-o', '--opponent', type=str, default='simple',
                        choices=['human', 'random', 'simple', 'reflex'], help="Opponent type")
    # parser.add_argument('-v', '--verbose', type=int, default=1,
    #                     choices=[0, 1, 2], help="Verbosity of prompts")
    parser.add_argument('-n', '--numGames', type=int, default=100,
                        help="Number of games to play")
    parser.add_argument('-t', '--train', action='store_true', help='Train the AI')
    return parser.parse_args()


def getAgent(agentType, playerNum):
    if agentType == 'human':
        return agent.HumanAgent(playerNum)
    elif agentType == 'random':
        return agent.RandomAgent()
    elif agentType == 'simple':
        return agent.SimpleAgent()
    elif agentType == 'reflex':
        return agent.ReflexAgent()


def train(args):
    alpha = 1e-1
    numFeatures = 0
    w_atk = [random.gauss(0, 1e-2) for _ in range(numFeatures)]
    w_def = [random.gauss(0, 1e-2) for _ in range(numFeatures)]
    w_atk[-1] = 0
    w_def[-1] = 0

    agents = [getAgent(args.agent, 0), getAgent(args.agent, 1)]
    for agent in agents:
        agent.setWeights(w_atk, w_def)

    g = dk.Durak()
    for i in xrange(args.numGames):
        attacker = g.getFirstAttacker()
        defender = int(not attacker)
        # save game state

        if i % 100 == 0:
            print 'Game: %d / %d' % (i, args.numGames)
        g.newGame()

    # save weights
    with open('%s_attack.bin', 'w') as f_atk:
        pickle.dump(w_atk, f_atk)
    with open('%s_defend.bin', 'w') as f_def:
        pickle.dump(w_def, f_def)

    return w_atk, w_def


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
    agents = [None, None]
    agents[0] = getAgent(args.agent, 0)
    agents[1] = getAgent(args.opponent, 1)

    g = dk.Durak()
    for _ in xrange(args.numGames):
        winner = play(g, agents)
        winCounts[winner] += 1
        g.newGame()
    print 'Win percentages:'
    print 'Agent: %d/%d' % (winCounts[0], args.numGames)
    print 'Opponent: %d/%d' % (winCounts[1], args.numGames)


if __name__ == '__main__':
    args = parseArgs()
    if args.train:
        train(args)
    else:
        main(args)