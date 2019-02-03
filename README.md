# nba-fantasy-optimize
Optimizes NBA fantasy lineup

This repo uses the Yahoo Fantasy Sports API to simulate matchups between any two players in the league (especially your upcoming matchup).
It accomplishes this by pulling historical data about each player and fitting a simple model to the data. It then uses this model to simulate the head-to-head outcome of the matchup.

It spits out several metrics:
* Projected aggregated stats for the matchup (the expected matchup totals for each category for each player on each team)
* Projected category values
* Projected scores for each player
* Probability of a win in the matchup

It also optimizes your lineup using win probability as a score for a roster. It accomplishes this via a random hill-climbing search that can also pull on the free-agent list for players.

# Installation
First, clone this repo. Then run:
```bash
$ pipenv install
```
That should handle the rest!

# Usage
First, create an app on the Yahoo Developer Network [here](https://developer.yahoo.com/apps/). Once you obtain the consumer key and secret key, put them in a file called `oauth.json` with keys `"consumer_key"` and `"consumer_secret"` respectively.

There are two scripts available and both will initially prompt you to log into your Yahoo account and will save the OAuth token from then on.
1. `simulate_lineup.py` - this script simulates your current lineup against your upcoming matchup
2. `optimize_lineup.py` - this script swaps around your starters along with free-agents to maximize your probability of winning in your upcoming matchup

There are a few important parameters for both scripts:
* `--num_samples` - this parameter controls the number of simulations run when evaluating lineups. The higher the more accurate, but the slower the program will run
* `--num_days` - this parameter controls how many days of data going backwards we use to fit the model
* `--week` - this parameter decides the week of the fantasy league the program will be run for. By default it is the current week.
* `--team1` and `--team2` - these control the two teams that will be matched up against each other. By default, `team1` is your team and `team2` is whoever you are facing in the given week. These can be overridden, however, by specifying the manager's name
* `--num_fa` - for the `optimize_lineup.py` script, specifically, this number specifies the number of free agents to query and search among when optimizing the lineup
