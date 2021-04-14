import functools
from multiprocessing import Pool
import random
import itertools
import numpy as np
import tqdm

from .util import print_roster
from .team import TEAM, Roster

def hill_climb(roster, score, num_steps = 1000, ignore_players=set(),
               ignore_injured=False):
    current_score = score(roster)
    yield roster, current_score
    rng = tqdm.trange(num_steps, desc='Optimizing[%.3f]' % current_score)
    for _ in rng:
        candidate_roster = roster.random_swap(ignore_players=ignore_players,
                                              ignore_injured=ignore_injured)
        candidate_score = score(candidate_roster)
        if candidate_score > current_score:
            roster, current_score = candidate_roster, candidate_score
            rng.set_description('Optimizing[%.3f]' % current_score)
            yield roster, current_score

def simulated_annealing(roster, score, num_steps = 1000, ignore_players=set(),
               ignore_injured=False, anneal_start=0.2, anneal_decay=0.990):
    current_score = score(roster)
    yield roster, current_score
    temperature = anneal_start
    rng = tqdm.trange(num_steps, desc='Optimizing[%.3f]' % current_score)
    for _ in rng:
        candidate_roster = roster.random_swap(ignore_players=ignore_players,
                                              ignore_injured=ignore_injured)
        candidate_score = score(candidate_roster)
        if candidate_score > current_score:
            roster, current_score = candidate_roster, candidate_score
            rng.set_description('Optimizing[%.3f, %.3f]' % (current_score, temperature))
            yield roster, current_score
        else:
            accept_prob = (candidate_score - current_score) / temperature
            if np.log(np.random.random()) <= accept_prob:
                roster, current_score = candidate_roster, candidate_score
                rng.set_description('Optimizing[%.3f, %.3f]' % (current_score, temperature))
                yield roster, current_score
        temperature *= anneal_decay

def form_roster(players, team, roster):
    if len(players) == 0:
        return all(v == 0 for v in team.values()), roster
    player = players[0]
    players = players[1:]
    position = None
    eligible = list(player.eligible_positions - {'Util'})
    if all(team[p] == 0 for p in eligible):
        position = 'Util'
    else:
        while position is None or team[position] == 0:
            position = random.choice(eligible)
    roster.positions[player] = position
    roster.players.append(player)
    team[position] -= 1
    return form_roster(players, team.copy(), roster)

# def team_generator(team, positions, remaining_players,
                   # ignore_injured=True, ignore_players=set()):
    # if all([v == 0 for v in team.values()]):
        # yield positions
    # available_positions = {k: v for k, v in team.items() if v > 0}
    # for position, num_slots in available_positions.items():
        # eligible_players = [p for p in remaining_players if
                            # not (ignore_injured and p.status == 'INJ')
                            # and not (p in ignore_players)
                            # and position in p.eligible_positions]
        # for player_combo in itertools.combinations(eligible_players, num_slots):
            # new_team = team.copy()
            # new_positions = positions.copy()
            # for player in player_combo:
                # new_team[position] -= 1
                # new_positions[player] = position
            # yield from team_generator(
                # new_team, new_positions, [p for p in remaining_players if p not in player_combo]
            # )
def score_roster(score, players):
    valid, roster = form_roster(sorted(players, key=lambda x: len(x.eligible_positions)), TEAM.copy(), Roster([], {}))
    if not valid:
        return roster, float('-inf')
    return roster, score(roster)

# def roster_score(other_roster, num_days, num_samples, week, decay_rate, roster):
    # cats, points, scores, _ = simulate_h2h(roster,
                        # other_roster,
                        # num_days=num_days, num_samples=num_samples,
                        # week=week, decay_rate=decay_rate)
    # return winning_prob(cats, points, scores, num_samples)


def brute_force(roster, score, ignore_players=set(), ignore_injured=False):
    num_valid = 0
    eligible_players = [p for p in roster.players if p.status != 'INJ']
    best = (None, float('-inf'))
    pool = Pool(20)
    scores = tqdm.tqdm(
        pool.imap(functools.partial(score_roster, score), itertools.combinations(eligible_players, 10)),
    total=3003)
    best = (None, float('-inf'))
    for roster, s in scores:
        if s > best[1]:
            best = (roster, s)
            scores.set_description(str(best[1]))
            yield best
