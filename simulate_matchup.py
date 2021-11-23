import numpy as np
import pandas as pd
import pyfiglet
import click
from tabulate import tabulate
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
from nba_matchup import get_league, visualize_matchup, CURRENT_WEEK, print_roster
league = get_league()

@click.command()
@click.option('--team1', type=str, default=None)
@click.option('--team2', type=str, default=None)
@click.option('--num_days', type=int, default=30)
@click.option('--num_samples', type=int, default=50000)
@click.option('--week', type=int, default=CURRENT_WEEK)
@click.option('--half_life', type=float, default=14)
def main(team1, team2, num_days, num_samples, week, half_life):
    league = get_league()
    decay_rate = np.log(2) / half_life
    print(tabulate([["Team", "Manager"]] + [[t.name, t.manager_name] for t in league.teams]))
    if team1 is None:
        team1 = league.current_team
    else:
        team1 = league.team_by_owner(team1)
    if team2 is None:
        team2 = league.get_matchup(team1, week=week)
    else:
        team2 = league.team_by_owner(team2)
    pyfiglet.print_figlet("%s vs. %s" % (team1.manager_name,
                                            team2.manager_name), font='banner',
                          width=160)
    if week:
        pyfiglet.print_figlet("Week %u" % week, font='big')
    print("Roster:")
    print_roster(team1.roster(week=week))
    print("Roster:")
    print_roster(team2.roster(week=week))
    projections = visualize_matchup([team1], team2, num_days=num_days, num_samples=num_samples,
                      week=week, decay_rate=decay_rate)
    #print(projections[0][0].round(2).to_csv())
    print("Projections")
    print("=====================")
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(projections[0][0].round(2))
    print("=====================")
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(projections[0][1].round(2))

if __name__ == "__main__":
    main()
