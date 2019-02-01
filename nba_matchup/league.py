from .yfs import yfs, LEAGUE_KEY, CURRENT_WEEK
from .team import get_teams

class League(object):

    def __init__(self, teams):
        self.teams = teams
        self.team_map = {
            t.team_key: t for t in self.teams
        }
        self.matchups = {}
        self.current_team = [t for t in teams if t.is_current_team][0]

    def team_by_owner(self, owner):
        for team in self.teams:
            if team.manager_name == owner:
                return team

    def get_matchup(self, team, week=CURRENT_WEEK):
        if (team.team_key, week) not in self.matchups:
            matchups = get_matchups(team.team_key)
            for w, team_key in matchups:
                self.matchups[team.team_key, w] = self.team_map[team_key]
        return self.matchups[team.team_key, week]

def get_league(league_key=LEAGUE_KEY):
    teams = get_teams(league_key)
    return League(list(teams))


def get_matchups(team_key):
    matchups = (
        yfs.get_teams_matchups([team_key]).json()
        ['fantasy_content']['teams']['0']['team'][1]['matchups']
    )
    for key, value in matchups.items():
        if key == 'count':
            continue
        week = value['matchup']['week']
        team_props = value['matchup']['0']['teams']['1']['team']
        team_dict = {}
        for prop in team_props[0]:
            if isinstance(prop, dict):
                for k, v in prop.items():
                    team_dict[k] = v
        matchup = team_dict['team_key']
        yield int(week), matchup
