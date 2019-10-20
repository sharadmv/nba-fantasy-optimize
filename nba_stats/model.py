import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_probability as tfp
tfd = tfp.distributions
tfb = tfp.bijectors

Root = tfd.JointDistributionCoroutine.Root


def extract(games):
    fga = games['FGA'].dropna().astype(np.float32)
    fgm = games['FGM'].dropna().astype(np.float32)
    fg3a = games['FG3A'].dropna().astype(np.float32)
    fg3m = games['FG3M'].dropna().astype(np.float32)

    fg2a = fga - fg3a
    fg2m = fgm - fg3m
    fg2p = np.sum(fg2m) / np.sum(fg2a)
    fg3p = np.sum(fg3m) / np.sum(fg3a)

    fgp = np.sum(fg2m + fg3m) / np.sum(fg2a + fg3a)

    fta = games['FTA'].dropna().astype(np.float32)
    ftm = games['FTM'].dropna().astype(np.float32)
    ftp = np.sum(ftm) / np.sum(fta)

    ast = games['AST'].dropna().astype(np.float32).mean()

    to = games['TOV'].dropna().astype(np.float32).mean()
    blk = games['BLK'].dropna().astype(np.float32).mean()
    stl = games['STL'].dropna().astype(np.float32).mean()
    pts = games['PTS'].dropna().astype(np.float32).mean()
    reb = games['REB'].dropna().astype(np.float32).mean()
    df = pd.DataFrame(columns=[
        "fga", "fgm", "fg3a", "fg3m", "fg2a", "fg2m",
        "fg2p", "fg3p", "fgp",
        "fta", "ftm", "ftp",
        "ast", "to", "blk", "stl", "pts", "reb"
    ], data=np.array([[
        fga.mean(),
        fgm.mean(),
        fg3a.mean(),
        fg3m.mean(), fg2a.mean(), fg2m.mean(),
        fg2p, fg3p, fgp,
        fta.mean(), ftm.mean(), ftp,
        ast, to, blk, stl, pts, reb
    ]]))
    return df


def fit(*games):
    games = pd.concat(games, axis=0)
    results = games.groupby('player').apply(extract)
    results = results.reset_index().drop(columns=['level_1'])
    players = results['player']
    (
        fga, fgm, fg3a, fg3m, fg2a, fg2m,
        fg2p, fg3p, fgp,
        fta, ftm, ftp,
        ast, to, blk, stl, pts, reb
    ) = [results[col] for col in results.columns
         if col != 'player']
    return players, tfd.JointDistributionNamed({
        'fg2p': tfd.Deterministic(loc=fg2p),
        'fg3p': tfd.Deterministic(loc=fg3p),
        'ftp': tfd.Deterministic(loc=ftp),

        'fg2a': tfd.Poisson(rate=fg2a),
        'fg2m': lambda fg2a, fg2p: tfd.Binomial(
            total_count=fg2a, probs=fg2p),

        'fg3a': tfd.Poisson(rate=fg3a),
        'fga': lambda fg2a, fg3a: tfd.Deterministic(loc=fg2a + fg3a),
        'fgm': lambda fg2m, fg3m: tfd.Deterministic(loc=fg2m + fg3m),
        'fg3m': lambda fg3a, fg3p: tfd.Binomial(
            total_count=fg3a, probs=fg3p),
        'fgp': lambda fg3a, fg3m, fg2a, fg2m: tfd.Deterministic(
            loc=(fg2m + fg3m) / (fg3a + fg3a)
        ),
        'fta':tfd.Poisson(rate=fta),
        'ftm': lambda fta: tfd.Binomial(total_count=fta,
                                        probs=ftp),

        'ast': tfd.Poisson(rate=ast),
        'reb': tfd.Poisson(rate=reb),
        'to': tfd.Poisson(rate=to),
        'blk': tfd.Poisson(rate=blk),
        'stl': tfd.Poisson(rate=stl),
        'pts': lambda ftm, fg2m, fg3m: tfd.Deterministic(
           loc=ftm + 2 * fg2m + 3 * fg3m
        )
    })
