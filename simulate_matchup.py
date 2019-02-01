import click
from tabulate import tabulate
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
from nba_matchup import get_league, visualize_matchup, CURRENT_WEEK
league = get_league()

@click.command()
@click.option('--team1', type=str, default=None)
@click.option('--team2', type=str, default=None)
@click.option('--num_days', type=int, default=14)
@click.option('--num_samples', type=int, default=50000)
@click.option('--week', type=int, default=CURRENT_WEEK)
def main(team1, team2, num_days, num_samples, week):
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
    visualize_matchup([team1], team2, num_days=num_days, num_samples=num_samples,
                      week=week)

if __name__ == "__main__":
    main()
