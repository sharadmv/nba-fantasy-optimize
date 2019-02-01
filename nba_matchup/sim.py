import datetime
import numpy as np
from nba_matchup import CURRENT_WEEK, START_DATE

CATS = [
   'FGA', 'FGM', 'FTA', 'FTM', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO'
]
CATEGORY_NAMES = [
   'FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO'
]

IGNORE_POSITIONS = ['BN', 'IL']

def simulate_h2h(roster1, roster2, week=CURRENT_WEEK, num_days=14, num_samples=10000):
    teams = [roster1, roster2]
    results = []
    base = START_DATE + datetime.timedelta(days=7 * (week - 1))
    for team in teams:
        team_stats, player_games = team.stats(num_days, base_date=base)
        team_stats = team_stats[(team_stats["GP"] > 0) & (team_stats["Position"] != "BN") & (team_stats["Position"] != "IL")]
        mean_stats = team_stats.groupby("Name").mean()
        names = set(team_stats["Name"])
        num_games = [len(p) for p, player in zip(player_games, team) if player.name in names]
        mean_stats["Num Games"] = num_games
        std_stats = team_stats.groupby("Name").std(ddof=0)
        std_stats["Num Games"] = np.zeros_like(num_games)
        results.append((mean_stats, std_stats))
    scores = [simulate_team(team, num_samples=num_samples) for team in results]
    cats, points = score(*scores)
    return cats, points, scores

def simulate_team(team, num_samples=100):
    sample = np.random.normal(loc=np.tile(team[0][CATS].mul(team[0]["Num Games"], axis=0) , [num_samples, 1, 1]),
                              scale=np.tile(team[1][CATS].mul(team[0]["Num Games"], axis=0), [num_samples, 1, 1]))
    return sample

def score(team1, team2):
    cats = []
    for team in [team1, team2]:
        team = team.sum(axis=1)
        fg_percent = team[..., 1] / team[..., 0]
        ft_percent = team[..., 3] / team[..., 2]
        cats.append(np.concatenate([fg_percent[..., None], ft_percent[..., None], team[..., 4:]], -1))
    cats = np.stack(cats)
    scores = (cats[0, ..., :-1] > cats[1, ..., :-1]).sum(axis=-1) + (cats[0, ..., -1] < cats[1, ..., -1]).astype(np.int64)
    return cats, scores
