from multiprocessing import Pool
from functools import partial
from collections import defaultdict
import numpy as np
import datetime
import pandas as pd
import click
from tabulate import tabulate
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
from nba_matchup import get_league, visualize_matchup, CURRENT_WEEK, print_roster, START_DATE, CATEGORY_NAMES, hill_climb, simulate_h2h, brute_force
league = get_league()

def winning_prob(cats, points, scores, num_samples):
    unique, nums = np.unique(points, return_counts=True)
    counts = defaultdict(int)
    counts.update(dict(zip(unique, nums)))
    return sum([counts[p] for p in range(5, 10)]) / num_samples

def ev(cats, points, scores, num_samples):
    return points.mean()

def roster_score(other_roster, num_days, num_samples, week, decay_rate, roster):
    cats, points, scores, _ = simulate_h2h(roster,
                        other_roster,
                        num_days=num_days, num_samples=num_samples,
                        week=week, decay_rate=decay_rate)
    means = cats.mean(axis=1)
    table = []
    probs = np.concatenate([
        (cats[0, ..., :-1] > cats[1, ..., :-1]).mean(axis=0),
        (cats[0, ..., -1:] < cats[1, ..., -1:]).mean(axis=0),
    ])
    for j, cat in enumerate(CATEGORY_NAMES):
        table.append([cat] + list(means[:, j]) + [probs[..., j]])
    result = winning_prob(cats, points, scores, num_samples)
    return result

def matchup(roster, roster_score, num_days, num_samples, week, decay_rate, other_roster):
    for roster, score in hill_climb(roster, partial(roster_score, other_roster, num_days, num_samples, week, decay_rate), ignore_players={}, ignore_injured=True, num_steps=100):
        pass
    return score

def score_team(roster, teams_to_eval,
               num_days, num_samples, week, decay_rate):
    other_rosters = [t.roster(week=week) for t in teams_to_eval]
    pool = Pool(len(teams_to_eval))
    scores = pool.map(partial(matchup, roster, roster_score, num_days, num_samples, week, decay_rate), other_rosters)
    return {k:v for k, v in zip(teams_to_eval, scores)}

@click.command()
@click.option('--team1', type=str, default=None)
@click.option('--team2', type=str, default=None)
@click.option('--num_days', type=int, default=30)
@click.option('--num_samples', type=int, default=50000)
@click.option('--week', type=int, default=CURRENT_WEEK)
@click.option('--half_life', type=float, default=14)
@click.option('--player1', type=str, multiple=True)
@click.option('--player2', type=str, multiple=True)
@click.option('--eval_team', type=str, multiple=True)
def main(team1, team2, num_days, num_samples, week, half_life, player1, player2, eval_team):
    player1_name, player2_name = team1, team2
    decay_rate = np.log(2) / half_life
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
    base = START_DATE + datetime.timedelta(days=7 * (week - 1) + 7)
    week_length = 7
    team1_roster = team1.roster(week=week)
    team2_roster = team2.roster(week=week)
    old_team1_stats, _ = team1_roster.stats(num_days, base_date=base, week_length=week_length)
    old_team1_average = old_team1_stats.mean(axis=0)
    old_team1_average['FG%'] = old_team1_average["FGM"] / old_team1_average["FGA"]
    old_team1_average['FT%'] = old_team1_average["FTM"] / old_team1_average["FTA"]
    old_team2_stats, _ = team2_roster.stats(num_days, base_date=base, week_length=week_length)
    old_team2_average = old_team2_stats.mean(axis=0)
    old_team2_average['FG%'] = old_team2_average["FGM"] / old_team2_average["FGA"]
    old_team2_average['FT%'] = old_team2_average["FTM"] / old_team2_average["FTA"]
    print(f"{team1.manager_name}'s roster:")
    print_roster(team1_roster)
    print(f"{team2.manager_name}'s roster:")
    print_roster(team2_roster)

    new_team1_roster = team1_roster.copy()
    new_team2_roster = team2_roster.copy()
    player1 = set(player1)
    player2 = set(player2)
    for p in player1:
        player = new_team1_roster.player_by_name(p)
        new_team1_roster = new_team1_roster.remove(player)
        new_team2_roster = new_team2_roster.add(player, 'BN')
    for p in player2:
        player = new_team2_roster.player_by_name(p)
        new_team2_roster = new_team2_roster.remove(player)
        new_team1_roster = new_team1_roster.add(player, 'BN')
    team1.set_roster(new_team1_roster)
    print_roster(new_team1_roster, include_bench=True, include_injured=True)
    print_roster(new_team2_roster, include_bench=True, include_injured=True)
    other_players = [team.roster(week=week) for team in league.teams if team.manager_name not in {player1_name, player2_name}]
    teams_to_eval = [league.team_by_owner(name) for name in eval_team]
    print("Evaluating %s" % team1.manager_name)
    old_team1_scores = score_team(team1_roster, teams_to_eval, num_days, num_samples, week, decay_rate)
    team1_scores = score_team(new_team1_roster, teams_to_eval, num_days, num_samples, week, decay_rate)
    improvements = [team1_scores[k] - old_team1_scores[k] for k in old_team1_scores]
    print(tabulate([[k.manager_name, old_team1_scores[k], team1_scores[k], team1_scores[k] - old_team1_scores[k]] for k in old_team1_scores]))
    print("Average improvement:", np.mean(improvements))

    print("Evaluating %s" % team2.manager_name)
    old_team2_scores = score_team(team2_roster, teams_to_eval, num_days, num_samples, week, decay_rate)
    team2_scores = score_team(new_team2_roster, teams_to_eval, num_days, num_samples, week, decay_rate)
    improvements = [team2_scores[k] - old_team2_scores[k] for k in old_team2_scores]
    print(tabulate([[k.manager_name, old_team2_scores[k], team2_scores[k], team2_scores[k] - old_team2_scores[k]] for k in old_team2_scores]))
    print("Average improvement:", np.mean(improvements))

if __name__ == "__main__":
    main()
