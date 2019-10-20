from datetime import datetime
import requests

from yaspin import yaspin
import pandas as pd

from nba_stats.util import cache


SCHEDULE_URL = "https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2019/league/00_full_schedule_week.json"


@cache("schedule.json")
def _get_schedule():
    return requests.get(SCHEDULE_URL).json()

def get_schedule():
    with yaspin(text="Loading schedule", color='cyan'):
        schedule_json = _get_schedule()
        raw_data = schedule_json['lscd']
        data = []
        for month_json in raw_data:
            for game in month_json['mscd']['g']:
                date = game['gdte']
                visitor_id = str(game['v']['tid'])
                visitor_abr = game['v']['ta']
                home_id = str(game['h']['tid'])
                home_abr = game['h']['ta']
                data.append([
                    datetime.strptime(date, '%Y-%m-%d'),
                    home_id,
                    home_abr,
                    visitor_id,
                    visitor_abr
                ])
        return pd.DataFrame(columns=[
            'date',
            'home_id', 'home_abbr',
            'away_id', 'away_abbr'
        ], data=data)
