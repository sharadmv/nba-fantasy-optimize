import tqdm

def hill_climb(roster, score, num_steps = 1000, ignore_players=set(),
               ignore_injured=False):
    current_score = score(roster)
    print("Starting roster score:", current_score)
    yield roster, current_score
    for _ in tqdm.trange(num_steps):
        candidate_roster = roster.random_swap(ignore_players=ignore_players,
                                              ignore_injured=ignore_injured)
        candidate_score = score(candidate_roster)
        if candidate_score > current_score:
            print("Found a better roster:", candidate_score)
            roster, current_score = candidate_roster, candidate_score
            yield roster, current_score
