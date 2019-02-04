from yaspin import yaspin
import requests
import pandas as pd
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool
import datetime
from functools import partial
from .yfs import yfs, LEAGUE_KEY

STAT_MAP = {
    'MINUTES_PLAYED': 'MP',
    'FIELD_GOALS_MADE': 'FGM',
    'FIELD_GOAL_ATTEMPTS': 'FGA',
    'THREE_POINTS_MADE': '3PTM',
    'THREE_POINT_ATTEMPTS': '3PTA',
    'FREE_THROWS_MADE': 'FTM',
    'FREE_THROW_ATTEMPTS': 'FTA',
    'OFFENSIVE_REBOUNDS': 'OREB',
    'TOTAL_REBOUNDS': 'REB',
    'TURNOVERS': 'TO',
    'DEFENSIVE_REBOUNDS': 'DREB',
    'ASSISTS': 'AST',
    'STEALS': 'ST',
    'BLOCKS': 'BLK',
    'FOULS': 'F',
    'POINTS': 'PTS',
}

STATS = list(STAT_MAP.values()) + [
    'GP'
]

class Stats(object):

    def __init__(self, stats):
        self.stats = stats.items()
        self.mapped_stats = stats

    def __getitem__(self, stat):
        return self.mapped_stats[stat]

    def keys(self):
        return STATS

    def values(self):
        return [self[stat] for stat in STATS]

    def as_dict(self):
        return self.mapped_stats

    @classmethod
    def from_dict(cls, stats_dict):
        if stats_dict is None:
            return None
        return Stats(stats_dict)

    def __add__(self, other):
        if not isinstance(other, Stats):
            return Stats(self.mapped_stats.copy())
        added_stats = {}
        for k in STATS:
            if self[k] is None and other[k] is None:
                added_stats[k] = None
            elif self[k] is None:
                added_stats[k] = other[k]
            elif other[k] is None:
                added_stats[k] = self[k]
            else:
                added_stats[k] = self[k] + other[k]
        return Stats(added_stats)

    def __radd__(self, other):
        return self.__add__(other)

def get_stat_day(date, player_keys):
    stat_json = (
        yfs._get('https://fantasysports.yahooapis.com/fantasy/v2/players;player_keys={players}/stats;type=date;date={date}'.format(
            date=date.isoformat(),
            players=','.join(player_keys)
        )).json()['fantasy_content']
    )
    stats = {}
    for i, (key, value) in enumerate(stat_json['players'].items()):
        if key == 'count':
            continue
        val = value['player'][1]['player_stats']['stats']
        if val[0]['stat']['value'] == '-':
            val = None
        stats[i] = val
    return stats


SCHEDULE_URL = "https://sports.yahoo.com/site/api/resource/sports.team.schedule;count=250;sched_state_alias=current_with_postseason;team_key={team_key}"
STATS_URL = "https://graphite-secure.sports.yahoo.com/v1/query/shangrila/gameLogBasketball?lang=en-US&playerId={player_key}&season=2018"

def get_all_stats(player_key, team_key, player_name):
    with yaspin(text="Getting stats for %s" % player_name, color='cyan'):
        player_key = "nba" + player_key[3:]
        team_key = "nba" + team_key[3:]
        response = requests.get(STATS_URL.format(player_key=player_key)).json()
        results = response['data']['players'][0]['playerGameStats']
        games = {}
        for game in results:
            game_date = datetime.datetime.strptime(game['game']['startTime'][:10], "%Y-%m-%d").date()
            stats = {}
            for stat in game['stats']:
                if stat['statId'] in STAT_MAP:
                    try:
                        stats[STAT_MAP[stat['statId']]] = float(stat['value'])
                    except:
                        stats[STAT_MAP[stat['statId']]] = stat['value']
            stats["GP"] = 1.
            games[game_date] = stats
        response = requests.get(SCHEDULE_URL.format(team_key=team_key)).json()
        results = response['service']['schedule']['games']
        dates = set()
        for game in results:
            dates.add(datetime.datetime.strptime(game[6:-2], "%Y%m%d").date())
        return games, dates

def convert_stat(stat):
    return Stats.from_dict(stat)

def get_stats(players, base_date=datetime.date.today(), num_days=7, num_threads=10):
    player_info = [(p.player_key, p.team_key, p.name) for p in players]
    base = base_date
    date_list = set([min(base, datetime.date.today()) - datetime.timedelta(days=x + 1) for x in range(num_days)])
    week_dates = set([base + datetime.timedelta(days=x) for x in range(7)])
    pool = Pool(num_threads)
    game_stats = pool.starmap(get_all_stats, player_info)
    date_stats, games = [], []
    for player, (stats, dates) in zip(players, game_stats):
        stats = {date: convert_stat(stat) for date, stat in stats.items() if date in
                 date_list}
        dates = {d for d in dates if d in week_dates}
        date_stats.append(stats)
        games.append(dates)
    return zip(date_stats, games)

NOTE_URL = 'https://basketball.fantasysports.yahoo.com/nba/160419/playernote?init=1&view=notes&pid={player_id}'

def get_player_games(player_id, start_date, end_date):
    soup = BeautifulSoup(requests.get(NOTE_URL.format(player_id=player_id)).json()["content"], features="html.parser")
    today = datetime.datetime.now()
    dates = [datetime.datetime.strptime(s.text + " " + str(today.year), "%b %d %Y") for s in soup.find_all("td", {"class": "date first"})]
    dates = [d for d in dates if
             start_date <= d.date() < end_date]
    return dates

def get_games(player_ids, start_date, end_date, num_threads=10):
    pool = Pool(num_threads)
    return pool.map(partial(get_player_games, start_date=start_date, end_date=end_date), player_ids)
