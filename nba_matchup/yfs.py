from yaspin import yaspin
import datetime
from yahoo_oauth import OAuth2
from fantasy_sport import FantasySport

__all__ = ['yfs', 'LEAGUE_KEY', 'CURRENT_WEEK', 'START_DATE']

LEAGUE_KEY = "nba.l.51967"

oauth = OAuth2(None, None, from_file='oauth.json', base_url='https://fantasysports.yahooapis.com/fantasy/v2/')
yfs = FantasySport(oauth, fmt='json')

with yaspin(text="Fetching league data", color='cyan'):
    response = yfs.get_leagues([LEAGUE_KEY]).json()['fantasy_content']['leagues']['0']['league'][0]
START_DATE = datetime.datetime.strptime(response['start_date'], "%Y-%m-%d").date()
while START_DATE.weekday() != 0:
    START_DATE -= datetime.timedelta(days=1)
diff = datetime.datetime.today().date() - START_DATE
CURRENT_WEEK = None #response.get('current_week', diff.days // 7)
