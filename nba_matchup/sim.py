import datetime
import numpy as np
from nba_matchup import CURRENT_WEEK, START_DATE
import scipy.special as sp

from .util import print_roster

CATS = [
   'FGA', 'FGM', 'FTA', 'FTM', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO'
]
NON_PERCENT_CATS = [
   'FGA', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO'
]
CATEGORY_NAMES = [
   'FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO'
]

IGNORE_POSITIONS = ['BN', 'IL']

def simulate_h2h(roster1, roster2, week=CURRENT_WEEK, num_days=14,
                 num_samples=10000, decay_rate=0.1,
                 include_bench=False,
                 include_injured=False):
    teams = [roster1, roster2]

    diff = (datetime.datetime.today().date() - START_DATE).days // 7
    if week is not None:
        base = START_DATE + datetime.timedelta(days=7 * (week - 1))
    else:
        base = START_DATE + datetime.timedelta(weeks=diff)
    scores, projections = [], []
    week_length = 7 #14 if week == 18 else 7
    ignore = {'BN', 'IL'}
    if include_bench:
        ignore.remove("BN")
    if include_injured:
        ignore.remove("IL")
    for team in teams:
        team_stats, player_games = team.stats(num_days, base_date=base,
                                              week_length=week_length)
        valid_players = set(team_stats[(team_stats["GP"] > 0) &
                                              (include_bench or team_stats["Position"] != "BN")
                                              & (include_injured or team_stats["Position"] !=
                                                 "IL")]['Name'])
        mean, std = compute_average(team_stats, decay_rate=decay_rate)
        num_games = [(player, len(p)) for p, player in zip(player_games,
                                                         team.players)]
        for player, num_game in num_games:
            mean.at[player.name, "Num Games"] = num_game
        for player, num_game in num_games:
            std.at[player.name, "Num Games"] = 0
        score, projection = projected_stats((mean, std), valid_players, num_samples=num_samples)
        valid_index = np.arange(len(mean.index))[mean.index.isin(valid_players)]
        scores.append(score[:, valid_index])
        projections.append(projection)
    cats, points = score_teams(*scores)
    return cats, points, scores, projections

def compute_average(team_stats, decay_rate=0.1):
    team_stats["Weight"] = np.exp(-decay_rate * team_stats["Days Ago"])
    grouped = team_stats.groupby("Name")
    def mean_func(x):
        normed_weights = x['Weight'] / x['Weight'].sum()
        mean = x[CATS].mul(normed_weights, axis=0).sum()
        mean['TFGM'] = mean['FGM'] * len(normed_weights)
        mean['TFGA'] = mean['FGA'] * len(normed_weights)
        mean['TFTM'] = mean['FTM'] * len(normed_weights)
        mean['TFTA'] = mean['FTA'] * len(normed_weights)
        return mean
    def std_func(x):
        data = x[CATS]
        normed_weights = x['Weight'] / x['Weight'].sum()
        mean = data.mul(x["Weight"], axis=0)
        deviation = (data.sub(mean, axis=1) ** 2).mul(x["Weight"], axis=0).sum(axis=0)
        N = deviation.shape[0]
        return np.sqrt(deviation / (N / (N - 1) * x["Weight"].sum()))
    mean = grouped.apply(mean_func)
    std = grouped.apply(std_func)
    return mean, std

def projected_stats(team, valid_players, num_samples=100):
    sample = np.random.normal(loc=np.tile(team[0][NON_PERCENT_CATS].mul(team[0]["Num Games"], axis=0) , [num_samples, 1, 1]),
                              scale=np.tile(team[1][NON_PERCENT_CATS].mul(team[0]["Num Games"], axis=0), [num_samples, 1, 1]))
    projected = team[0].copy()
    projected[NON_PERCENT_CATS] = sample.mean(axis=0)
    ftp = np.random.beta(1. + team[0]['TFTM'], 1. + team[0]['TFTA'] - team[0]['TFTM'],
        [num_samples, len(team[0])])
    fgp = np.random.beta(1. + team[0]['TFGM'], 1. + team[0]['TFGA'] - team[0]['TFGM'],
        [num_samples, len(team[0])])
    fgp[np.isnan(fgp)] = 0.
    ftp[np.isnan(ftp)] = 0.
    fga = np.maximum(sample[..., NON_PERCENT_CATS.index('FGA')].astype(np.int64), 0)
    fta = np.maximum(sample[..., NON_PERCENT_CATS.index('FTA')].astype(np.int64), 0)
    fgm = np.random.binomial(fga, fgp)
    ftm = np.random.binomial(fta, ftp)
    projected['FGM'] = fgm.mean(axis=0)
    projected['FTM'] = ftm.mean(axis=0)
    projected['FG%'] = projected['FGM'] / projected['FGA']
    projected['FT%'] = projected['FTM'] / projected['FTA']
    cols = ['Num Games', 'FGM', 'FGA', 'FG%', 'FTM', 'FTA', 'FT%', '3PTM', 'PTS', 'REB',
        'AST', 'ST', 'BLK', 'TO']
    projected = projected[cols]
    sample = np.concatenate([fgm[..., None], ftm[..., None], sample], axis=-1)
    return sample, projected

def score_teams(team1, team2):
    cats = []
    for i, team in enumerate([team1, team2]):
        team = team.sum(axis=1)
        fg_percent = (team[..., 0] / team[..., 2])
        ft_percent = (team[..., 1] / team[..., 3])
        cats.append(np.concatenate([fg_percent[..., None], ft_percent[..., None], team[..., 4:]], -1))
    cats = np.stack(cats)
    scores = (cats[0][..., :-1] > cats[1][..., :-1]).sum(axis=-1) + (cats[0][..., -1] < cats[1][..., -1]).astype(np.int64)
    return cats, scores
