import random
import datetime
import pandas as pd

from .yfs import yfs, CURRENT_WEEK
from .player import Player
from .stats import get_stats
from .util import valid_starters

__all__ = ['get_teams']

class Roster(object):

    def __init__(self, players, positions):
        self.players = players
        self.positions = positions

    def __getitem__(self, idx):
        return self.players[idx]

    def __iter__(self):
        yield from self.players

    def add(self, player, position):
        return Roster(self.players + [player], {player: position, **self.positions})

    def random_swap(self, ignore_players=set()):
        new_positions = self.positions.copy()
        starters = set(p for p in new_positions if new_positions[p] not in {'IL', 'BN'})
        new_starters = starters
        while starters == new_starters:
            useful_players = list(p for p in self.players
                                if new_positions[p] not in {'IL', 'BN'})
            candidates = []
            while len(candidates) == 0:
                random_choice = None
                while random_choice is None or random_choice in ignore_players:
                    random_choice = random.choice(useful_players)
                candidates = [p for p in self.players if (
                    new_positions[random_choice] in p.eligible_positions
                ) and (new_positions[p] in random_choice.eligible_positions or
                       new_positions[p] == "BN") and p not in ignore_players and p != random_choice]
            candidate = random.choice(candidates)
            new_positions[candidate], new_positions[random_choice] = new_positions[random_choice], new_positions[candidate]
            new_starters = set(p for p in new_positions if new_positions[p] not in
                            {'IL', 'BN'})
        return Roster(self.players, new_positions)

    def player_by_name(self, name):
        for player in self:
            if name == player.name:
                return player

    def stats(self, num_days=14, base_date=datetime.date.today()):
        if any(s._stats is None for s in self):
            for player, stats in zip(self, get_stats(self,
                                                     num_days=num_days,
                                                     base_date=base_date)):
                player.set_stats(stats)
        stats = []
        for player in self:
            stat = player.stats[0]
            stat["Position"] = self.positions[player]
            stats.append(stat)
        stats = pd.concat(stats, ignore_index=True)
        stats["Days Ago"] = [(base_date - d).days for d in stats["Date"]]
        games = [p.stats[1] for p in self]
        return stats, games

class Team(object):

    def __init__(self, team_key, team_id, name,
                 is_current_team,
                 url,
                 waiver_priority,
                 manager_id,
                 manager_name):
        self.team_key = team_key
        self.team_id = team_id
        self.name = name
        self.is_current_team = is_current_team
        self.url = url
        self.waiver_priority = waiver_priority
        self.manager_name = manager_name
        self.manager_id = manager_id
        self._roster = None
        self._stats = {}

    def roster(self, week=None):
        if self._roster is None:
            self._roster = get_roster(self.team_key, week=week)
        return self._roster

    def set_roster(self, roster):
        self._roster = roster

    def valid_starters(self, ignore_players=set()):
        possible_starters = [player for player in self.roster if player not in
                             ignore_players]
        return valid_starters(possible_starters)

    @classmethod
    def from_dict(cls, team_dict):
        return Team(
            team_dict.get('team_key', None),
            team_dict.get('team_id', None),
            team_dict.get('name', None),
            team_dict.get('is_owned_by_current_login', False),
            team_dict.get('url', None),
            team_dict.get('waiver_priority', None),
            team_dict.get('manager_id', team_dict['managers'][0]['manager']['manager_id']),
            team_dict.get('manager_name', team_dict['managers'][0]['manager']['nickname']),
        )


    def __str__(self):
        return "Team<{name}>".format(
            name=self.name
        )

    def __repr__(self):
        return "Team('{name}')".format(
            name=self.name
        )

def get_teams(league_key):
    teams_json = yfs.get_leagues_teams([league_key]).json()
    for key, value in teams_json['fantasy_content']['leagues']['0']['league'][1]['teams'].items():
        if key == 'count':
            continue
        team_props = value['team'][0]
        team_dict = {}
        for prop in team_props:
            if isinstance(prop, dict):
                for k, v in prop.items():
                    team_dict[k] = v
        yield Team.from_dict(team_dict)

def get_roster(team_key, week=None):
    roster_props = yfs.get_teams_roster([team_key], week=week).json()['fantasy_content']['teams']['0']['team']
    roster = []
    for key, value in roster_props[1]['roster']['0']['players'].items():
        if key == 'count':
            continue
        player_dict = {}
        for prop in value['player'][0]:
            if isinstance(prop, dict):
                for k, v in prop.items():
                    player_dict[k] = v
        player_dict['selected_position'] = (
            value['player'][1]['selected_position'][1]['position']
        )
        roster.append(Player.from_dict(player_dict))
    return Roster(roster, {p: p.selected_position for p in roster})
