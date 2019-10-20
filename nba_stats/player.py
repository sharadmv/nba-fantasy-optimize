from nba_api.stats.static import players
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.endpoints import commonallplayers

from nba_stats.util import memoize, cache
from nba_stats import model


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
        self._nba_id = None

    @property
    def active(self):
        return (self.selected_position != 'BN' and
                self.selected_position != 'IL')

    @property
    def injured(self):
        return self.selected_position != 'IL'

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


    @property
    def nba_id(self):
        if self._nba_id is None:
            players = get_player_data()
            player = players[
                players["DISPLAY_FIRST_LAST"] == self.name
            ].iloc[0]
            self._nba_id = player['PERSON_ID']
        return self._nba_id

    @memoize
    def games(self, season=None,
              season_type=None,
              **kwargs):
        game_finder = leaguegamefinder.LeagueGameFinder(
            player_id_nullable=self.nba_id,
            season_nullable=season,
            season_type_nullable=season_type,
        **kwargs)
        games = game_finder.get_data_frames()[0]
        games['player'] = self.name
        return games

    @classmethod
    def from_name(cls, full_name):
        players = get_player_data()
        player = players[
            players['DISPLAY_FIRST_LAST'] == full_name
        ].iloc[0]
        return Player(**dict(
            full_name=player['DISPLAY_FIRST_LAST'],
            id=player['PERSON_ID'],
            team_id=player['TEAM_ID'],
        ))


    @classmethod
    def from_id(cls, id):
        players = get_player_data()
        player = players[
            players['PERSON_ID'] == id
        ].iloc[0]
        return Player(**dict(
            full_name=player['DISPLAY_FIRST_LAST'],
            id=player['PERSON_ID'],
            team_id=player['TEAM_ID'],
        ))


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


    def fit_model(self, **kwargs):
        games = self.games(**kwargs)
        return model.fit(games)


@cache('player.csv', fmt='pandas')
def get_player_data():
    data = commonallplayers.CommonAllPlayers(
        is_only_current_season=1
    ).get_data_frames()[0]
    return data
