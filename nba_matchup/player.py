import pandas as pd

from .yfs import yfs
from .stats import get_stats, STATS

class Player(object):

    def __init__(self, player_key, player_id,
                 name, status, team, team_key,
                 eligible_positions,
                 selected_position):
        self.player_key = player_key
        self.player_id = player_id
        self.name = name
        self.status = status
        self.team = team
        self.team_key = team_key
        self.eligible_positions = eligible_positions
        self.selected_position = selected_position
        self._stats = None

    @classmethod
    def from_dict(cls, player_dict):
        return Player(
            player_dict['player_key'],
            player_dict['player_id'],
            player_dict['name']['full'],
            player_dict.get('status', None),
            player_dict['editorial_team_full_name'],
            player_dict['editorial_team_key'],
            set(v['position'] for v in player_dict['eligible_positions']),
            player_dict['selected_position'],
        )

    def __str__(self):
        return "Player[{position}]<{name}>".format(
            name=self.name,
            position=self.selected_position
        )

    def __repr__(self):
        return "Player[{position}]('{name}')".format(
            name=self.name,
            position=self.selected_position
        )

    @property
    def stats(self):
        if self._stats is None:
            raise Exception("Haven't computed stats yet")
        df = pd.DataFrame(
            data=[[self.name, self.eligible_positions, self.selected_position, date] + s.values() for
                  date, s
                  in self._stats[0].items()],
            columns=['Name', 'Eligible Positions', 'Position', 'Date'] + STATS
        )
        return df, self._stats[1]

    def set_stats(self, stats):
        self._stats = stats

    def is_out(self):
        return self.status == 'INJ' or self.status == 'O'
