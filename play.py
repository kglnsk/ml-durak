import argparse
import pickle
import numpy as np

import durak2 as dk
import agent as agt
import util


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Play a two-player game of Durak against a random-policy opponent.')
    parser.add_argument('-a', '--agent', type=str, default='simple',
                        choices=['human', 'random', 'simple', 'reflex', 'simple++'], help="Agent type")
    parser.add_argument('-o', '--opponent', type=str, default='simple',
                        choices=['human', 'random', 'simple', 'reflex', 'simple++'], help="Opponent type")
    # parser.add_argument('-v', '--verbose', type=int, default=1,
    #                     choices=[0, 1, 2], help="Verbosity of prompts")
    parser.add_argument('-n', '--numGames', type=int, default=100,
                        help="Number of games to play")
    parser.add_argument('-t', '--train', action='store_true', help='Train the AI')
    return parser.parse_args()


def getAgent(agentType, playerNum):
    if agentType == 'human':
        return agt.HumanAgent(playerNum)
    elif agentType == 'random':
        return agt.RandomAgent()
    elif agentType == 'simple':
        return agt.SimpleAgent()
    elif agentType == 'reflex':
        return agt.ReflexAgent(playerNum)
    elif agentType == 'simple++':
        return agt.SimpleEnhancedAgent(playerNum)


def TDUpdate(state, nextState, reward, w, eta=1e-1):
    features = util.extractFeatures(state)
    value = util.logisticValue(w, features)
    residual = reward - value
    if nextState is not None:
        nextFeatures = util.extractFeatures(nextState)
        residual += util.logisticValue(w, nextFeatures)
    gradient = value * (1 - value) * features
    newWeights = w + eta * residual * gradient
    return newWeights


def train(args):
    w_atk = np.random.normal(0, 1e-2, (util.NUM_FEATURES,))
    w_def = np.random.normal(0, 1e-2, (util.NUM_FEATURES,))
    w_atk[-1] = 0
    w_def[-1] = 0

    agents = [getAgent(args.agent, 0), getAgent(args.agent, 1)]
    for agent in agents:
        agent.setAttackWeights(w_atk)
        agent.setDefendWeights(w_def)

    g = dk.Durak()
    for i in xrange(args.numGames):
        attacker = g.getFirstAttacker()
        defender = int(not attacker)
        while True:
            preAttack = None
            preDefend = None
            while True:
                preAttack = g.getState(attacker)
                attack(g, attacker, agents[attacker])
                postAttack = g.getState(defender)
                if g.roundOver():
                    break
                elif preDefend is not None:
                    w_def = TDUpdate(preDefend, postAttack, 0, w_def)
                    for agent in agents:
                        agent.setDefendWeights(w_def)

                preDefend = postAttack
                defend(g, defender, agents[defender])
                postDefend = g.getState(attacker)
                if g.roundOver():
                    break
                else:
                    w_atk = TDUpdate(preAttack, postDefend, 0, w_atk)
                    for agent in agents:
                        agent.setAttackWeights(w_atk)

            if g.gameOver():
                if g.isWinner(attacker):
                    w_atk = TDUpdate(g.getState(attacker), None, 1, w_atk)
                    w_def = TDUpdate(g.getState(defender), None, 0, w_def)
                else:
                    w_def = TDUpdate(g.getState(defender), None, 1, w_def)
                    w_atk = TDUpdate(g.getState(attacker), None, 0, w_atk)
                for agent in agents:
                    agent.setAttackWeights(w_atk)
                    agent.setDefendWeights(w_def)
                break

            g.endRound()

            # Edge case, the defender from the last round won
            if g.gameOver():
                w_def = TDUpdate(g.getState(defender), None, 1, w_def)
                w_atk = TDUpdate(g.getState(attacker), None, 0, w_atk)
                for agent in agents:
                    agent.setDefendWeights(w_def)
                    agent.setAttackWeights(w_atk)
                break
            else:
                w_def = TDUpdate(preDefend, g.getState(defender), 0, w_def)
                w_atk = TDUpdate(preAttack, g.getState(attacker), 0, w_atk)
                for agent in agents:
                    agent.setDefendWeights(w_def)
                    agent.setAttackWeights(w_atk)

            attacker = g.attacker
            defender = int(not attacker)

        if i % 50 == 0:
            print 'Training iteration: %d / %d' % (i, args.numGames)
            randomAgent = agt.RandomAgent()
            simpleAgent = agt.SimpleAgent()
            winCounts = {'random': 0, 'simple': 0}
            for _ in xrange(500):
                winVsRandom = play(dk.Durak(), [randomAgent, agents[0]])
                winVsSimple = play(dk.Durak(), [simpleAgent, agents[0]])
                winCounts['random'] += winVsRandom
                winCounts['simple'] += winVsSimple
            with open('results.csv', 'a') as f:
                row = [i, winCounts['random'], winCounts['simple']]
                row.extend(w_atk)
                row.extend(w_def)
                np.savetxt(f, np.array(row)[:, None].T, delimiter=',', fmt='%.4e')

            # save weights
            with open('%s_attack_%d.bin' % (args.agent, i), 'w') as f_atk:
                pickle.dump(w_atk, f_atk)
            with open('%s_defend_%d.bin' % (args.agent, i), 'w') as f_def:
                pickle.dump(w_def, f_def)

        g.newGame()

    with open('%s_attack.bin' % args.agent, 'w') as f_atk:
        pickle.dump(w_atk, f_atk)
    with open('%s_defend.bin' % args.agent, 'w') as f_def:
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
    for i in xrange(args.numGames):
        winner = play(g, agents)
        winCounts[winner] += 1
        print 'Game %d winner: %d' % (i, winner)
        g.newGame()
    print 'Win percentages:'
    print 'Agent: %d/%d' % (winCounts[0], args.numGames)
    print 'Opponent: %d/%d' % (winCounts[1], args.numGames)


if __name__ == '__main__':
    args = parseArgs()
    if args.train and args.agent in ['reflex']:
        train(args)
    else:
        main(args)