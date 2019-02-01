import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style='white')
from collections import defaultdict
import numpy as np
import click
from tabulate import tabulate
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
from nba_matchup import get_league, simulate_h2h, CURRENT_WEEK, CATEGORY_NAMES, hill_climb, visualize_matchup, get_free_agents
league = get_league()

@click.command()
@click.option('--team1', type=str, default=None)
@click.option('--team2', type=str, default=None)
@click.option('--num_days', type=int, default=14)
@click.option('--num_samples', type=int, default=50000)
@click.option('--week', type=int, default=CURRENT_WEEK)
@click.option('--num_fa', type=int, default=0)
@click.option('--num_iters', type=int, default=100)
def main(team1, team2, num_days, num_samples, week, num_fa, num_iters):
    league = get_league()
    print(tabulate([["Team", "Manager"]] + [[t.name, t.manager_name] for t in league.teams]))
    if team1 is None:
        team1 = league.current_team
    else:
        team1 = league.team_by_owner(team1)
    if team2 is None:
        team2 = league.get_matchup(team1, week=week)
    else:
        team2 = league.team_by_owner(team2)
    def roster_score(roster):
        cats, points, scores = simulate_h2h(roster,
                            team2.roster,
                            num_days=num_days, num_samples=num_samples,
                            week=week)
        unique, nums = np.unique(points, return_counts=True)
        counts = defaultdict(int)
        counts.update(dict(zip(unique, nums)))
        winning_prob = sum([counts[p] for p in range(5, 10)]) / num_samples
        return winning_prob
    print("Current roster:", roster_score(team1.roster))
    for player, position in team1.roster.positions.items():
        print(player.name, position)
    roster = team1.roster
    old_roster = roster
    for agent in get_free_agents(num_fa):
        print("Adding", agent)
        roster = roster.add(agent, "BN")
    team1.set_roster(roster)
    roster, score = hill_climb(roster, roster_score,
                               ignore_players={team1.roster[16]},
                               num_steps=num_iters)
    print("New roster:", score)
    for player, position in roster.positions.items():
        print(player.name, position)

    def team_generator():
        for r in [old_roster, roster]:
            team1.set_roster(r)
            yield team1

    visualize_matchup(team_generator(), team2,
                      num_days=num_days, num_samples=100000,
                      week=week)
    team1_stats = team1.roster.stats()[0]
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(team1_stats.groupby("Name").mean().round(2))

if __name__ == "__main__":
    main()
