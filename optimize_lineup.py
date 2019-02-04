import pyfiglet
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
@click.option('--ignore_player', type=str, multiple=True)
@click.option('--half_life', type=float, default=14)
def main(team1, team2, num_days, num_samples, week, num_fa, num_iters,
         ignore_player, half_life):
    league = get_league()
    decay_rate = np.log(2) / half_life
    if team1 is None:
        team1 = league.current_team
    else:
        team1 = league.team_by_owner(team1)
    if team2 is None:
        team2 = league.get_matchup(team1, week=week)
    else:
        team2 = league.team_by_owner(team2)
    pyfiglet.print_figlet("%s vs. %s" % (team1.manager_name,
                                            team2.manager_name), font='big')
    pyfiglet.print_figlet("Week %u" % week, font='banner')
    def roster_score(roster):
        cats, points, scores, _ = simulate_h2h(roster,
                            team2.roster(week=week),
                            num_days=num_days, num_samples=num_samples,
                            week=week, decay_rate=decay_rate)
        unique, nums = np.unique(points, return_counts=True)
        counts = defaultdict(int)
        counts.update(dict(zip(unique, nums)))
        winning_prob = sum([counts[p] for p in range(5, 10)]) / num_samples
        return winning_prob
    print("%s's roster:" % team1.manager_name, roster_score(team1.roster(week=week)))
    print(tabulate([
        [position, player.name] for player, position in
        team1.roster(week=week).positions.items() if position not in {"BN", "IL"}
    ]))
    print("%s's roster:" % team2.manager_name, roster_score(team2.roster(week=week)))
    print(tabulate([
        [position, player.name] for player, position in
        team2.roster(week=week).positions.items() if position not in {"BN", "IL"}
    ]))
    print("Optimizing %'s lineup" % team1.manager_name)
    print("===========================================")
    roster = team1.roster(week=week)
    old_roster = roster
    print("Adding free agents:")
    for agent in get_free_agents(num_fa):
        print(agent.name)
        roster = roster.add(agent, "BN")
    team1.set_roster(roster)
    print("Ignoring players:", ", ".join(ignore_player))
    for roster, score in hill_climb(roster, roster_score,
                               ignore_players={team1.roster(week=week).player_by_name(n)
                                               for n in ignore_player},
                                    num_steps=num_iters):
        pass
    print("New roster")
    print(tabulate([
        [position, player.name] for player, position in
        roster.positions.items() if position not in {"BN", "IL"}
    ]))
    print("Win probability:", score)

    def team_generator():
        for r in [old_roster, roster]:
            team1.set_roster(r)
            yield team1

    projections = visualize_matchup(team_generator(), team2,
                      num_days=num_days, num_samples=100000,
                      week=week, decay_rate=decay_rate)
    with pd.option_context('display.max_rows', None, 'display.max_columns',
                           None, 'display.expand_frame_repr', False):
        print(projections[1][0].round(2))

if __name__ == "__main__":
    main()
