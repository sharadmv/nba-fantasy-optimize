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
    base = START_DATE + datetime.timedelta(days=7 * (week - 1))
    scores, projections = [], []
    for team in teams:
        team_stats, player_games = team.stats(num_days, base_date=base)
        valid_players = set(team_stats[(team_stats["GP"] > 0) &
                                              (team_stats["Position"] != "BN")
                                              & (team_stats["Position"] !=
                                                 "IL")]['Name'])
        mean_stats = team_stats.groupby("Name").mean()
        num_games = [(player, len(p)) for p, player in zip(player_games,
                                                         team.players)]
        for player, num_game in num_games:
            mean_stats.at[player.name, "Num Games"] = num_game
        std_stats = team_stats.groupby("Name").std(ddof=1)
        for player, num_game in num_games:
            std_stats.at[player.name, "Num Games"] = 0
        score, projection = projected_stats((mean_stats, std_stats), valid_players, num_samples=num_samples)
        valid_index = np.arange(len(mean_stats.index))[mean_stats.index.isin(valid_players)]
        scores.append(score[:, valid_index])
        projections.append(projection)
    cats, points = score_teams(*scores)
    return cats, points, scores, projections

def projected_stats(team, valid_players, num_samples=100):
    sample = np.random.normal(loc=np.tile(team[0][CATS].mul(team[0]["Num Games"], axis=0) , [num_samples, 1, 1]),
                              scale=np.tile(team[1][CATS].mul(team[0]["Num Games"], axis=0), [num_samples, 1, 1]))
    projected = team[0].copy()
    projected[CATS] = sample.mean(axis=0)
    return sample, projected

def score_teams(team1, team2):
    cats = []
    for team in [team1, team2]:
        team = team.sum(axis=1)
        fg_percent = team[..., 1] / team[..., 0]
        ft_percent = team[..., 3] / team[..., 2]
        cats.append(np.concatenate([fg_percent[..., None], ft_percent[..., None], team[..., 4:]], -1))
    cats = np.stack(cats)
    scores = (cats[0, ..., :-1] > cats[1, ..., :-1]).sum(axis=-1) + (cats[0, ..., -1] < cats[1, ..., -1]).astype(np.int64)
    return cats, scores
