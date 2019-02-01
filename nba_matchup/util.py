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

def visualize_matchup(team1, team2, **kwargs):
    from .sim import simulate_h2h, CATEGORY_NAMES
    num_samples = kwargs.get('num_samples', 1000)
    cats, points, scores = simulate_h2h(team1.roster,
                           team2.roster, **kwargs)
    print("%s's expected score: %f +/- %f" % (team1.manager_name, points.mean(), points.std()))
    print("Expected categories:")
    means = cats.mean(axis=1)
    unique, nums = np.unique(points, return_counts=True)
    counts = defaultdict(int)
    counts.update(dict(zip(unique, nums)))
    winning_prob = sum([counts[p] for p in range(5, 10)]) / num_samples
    table = [["", team1.manager_name, team2.manager_name]]
    for i, cat in enumerate(CATEGORY_NAMES):
        table.append([cat] + list(means[:, i]))
    print(tabulate(table))
    print("%s has a %f chance of beating %s" % (
        team1.manager_name,
        winning_prob,
        team2.manager_name,
    ))
    fig, ax = plt.subplots()
    ax.bar(list(range(10)), [counts[p] / num_samples for p in range(10)], align='center',
           alpha=0.5)
    ax.set_xlabel("Score")
    ax.set_xticks(range(10))
    ax.set_title("%s's probability of scores" % team1.manager_name)
    fig, ax = plt.subplots()
    probs = np.concatenate([
        (cats[0, ..., :-1] > cats[1, ..., :-1]).mean(axis=0),
        (cats[0, ..., -1:] < cats[1, ..., -1:]).mean(axis=0),
    ])
    ax.bar(CATEGORY_NAMES, probs, align='center', alpha=0.5, color=
           ['green' if p > 0.5 else 'red' for p in probs])
    ax.set_xlabel("Category")
    ax.set_ylabel("Probability of Winning")
    ax.set_ylim([0, 1])
    ax.set_title("%s vs. %s Simulation" % (team1.manager_name,
                                           team2.manager_name))
    plt.show()
