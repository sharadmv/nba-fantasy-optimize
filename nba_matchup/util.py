from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
sns.set(style='white')
import numpy as np
import tqdm

TEAM_COUNT = {
    'G': 1,
    'SG': 1,
    'PG': 1,
    'F': 1,
    'SF': 1,
    'PF': 1,
    'C': 2,
    'Util': 2,
    'IL': 0,
    'BN': 0,
}

def valid_starters(players):
    def generate_roster(players, counts, num_slots):
        if num_slots == 0:
            yield {}
        for player in players:
            for eligible_position in player.eligible_positions:
                if counts[eligible_position] > 0:
                    new_players = players.copy()
                    new_players.remove(player)
                    new_counts = counts.copy()
                    new_counts[eligible_position] -= 1
                    for remaining_roster in generate_roster(new_players,
                                                            new_counts,
                                                            num_slots - 1):
                        yield {player: eligible_position, **remaining_roster}
    for roster in tqdm.tqdm(generate_roster(players, TEAM_COUNT.copy(),
                                            sum(TEAM_COUNT.values()))):
        yield roster

def visualize_matchup(teams, opponent, show_plots=True, **kwargs):
    from .sim import simulate_h2h, CATEGORY_NAMES
    num_samples = kwargs.get('num_samples', 1000)
    week = kwargs.get('week', None)
    fig, ax = plt.subplots(1, 2)
    bar_width = 0.35
    projections = []
    for i, team in enumerate(teams):
        print("===========================================")
        cats, points, scores, projection = simulate_h2h(team.roster(week=week),
                                opponent.roster(week=week), **kwargs)
        print("%s's expected score: %f +/- %f" % (team.manager_name, points.mean(), points.std()))
        print("Expected categories:")
        means = cats.mean(axis=1)
        unique, nums = np.unique(points, return_counts=True)
        counts = defaultdict(int)
        counts.update(dict(zip(unique, nums)))
        winning_prob = sum([counts[p] for p in range(5, 10)]) / num_samples
        probs = np.concatenate([
            (cats[0, ..., :-1] > cats[1, ..., :-1]).mean(axis=0),
            (cats[0, ..., -1:] < cats[1, ..., -1:]).mean(axis=0),
        ])
        table = [["", team.manager_name, opponent.manager_name]]
        for j, cat in enumerate(CATEGORY_NAMES):
            table.append([cat] + list(means[:, j]) + [probs[..., j]])
        print(tabulate(table))
        print("%s has a %f chance of beating %s" % (
            team.manager_name,
            winning_prob,
            opponent.manager_name,
        ))
        ax[0].bar(np.arange(10) + i * bar_width, [counts[p] / num_samples for p
                                                  in range(10)], 0.1, align='center',
                    alpha=0.5, label='%s-%u' % (team.manager_name, i))
        ax[0].set_xlabel("Score")
        ax[0].set_xticks(np.arange(10) + bar_width / 2)
        ax[0].set_xticklabels(range(10))
        ax[0].set_title("%s's probability of scores" % team.manager_name)
        ax[1].bar(np.arange(len(CATEGORY_NAMES)) + i * bar_width, probs,
                  bar_width, align='center', alpha=0.5, color= ['green' if p >
                                                                0.5 else 'red'
                                                                for p in
                                                                probs],
                  label='%s-%u' % (team.manager_name, i))
        ax[1].set_xticks(np.arange(len(CATEGORY_NAMES)) + bar_width / 2)
        ax[1].set_xticklabels(CATEGORY_NAMES)
        ax[1].set_xlabel("Category")
        ax[1].set_ylabel("Probability of Winning")
        ax[1].set_ylim([0, 1])
        ax[1].set_title("%s vs. %s Simulation" % (team.manager_name, opponent.manager_name))
        projections.append(projection)
    ax[0].legend(loc='best')
    ax[1].legend(loc='best')
    if show_plots:
        plt.show()
    return projections
