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
