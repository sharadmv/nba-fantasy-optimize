import dataclasses
import functools
import pathlib

from typing import Optional, Union

import yaml
import yaspin
import yfpy

@dataclasses.dataclass
class YFS:
  config_dir: Union[pathlib.Path, str]

  def __post_init__(self):
    self.config_dir = pathlib.Path(self.config_dir)
    with (self.config_dir / 'league.yaml').open('r') as fp:
      league_config = yaml.safe_load(fp)

    self._yfs = yfpy.YahooFantasySportsQuery(
      self.config_dir,
      league_id=str(league_config['league_id']),
      game_code=league_config['game_code'])

  @functools.cached_property
  def league(self) -> yfpy.League:
    with yaspin.yaspin('Loading league info'):
      return self._yfs.get_league_info()

  @functools.cached_property
  def current_user(self) -> yfpy.User:
    with yaspin.yaspin('Loading user info'):
      return self._yfs.get_current_user()

  @functools.cached_property
  def current_team(self) -> yfpy.Team:
    for team in self.league.teams_ordered_by_standings:
      team = team['team']
      managers = (team.managers if isinstance(team.managers, list) else
          [team.managers])
      for manager in managers:
        manager = manager['manager']
        if manager.guid == self.current_user.guid:
          return team
    raise ValueError('Couldn\'t find current team.')

  def get_roster(self, *, team_id: Optional[str] = None, week: Optional[int] =
      None) -> yfpy.models.Roster:
    team_id = team_id or self.current_team.team_id
    week = week or self.league.current_week
    return self._yfs.get_team_roster_by_week(team_id, chosen_week=week)

