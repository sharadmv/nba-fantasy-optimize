from .yfs import yfs, LEAGUE_KEY
from .player import Player

def get_free_agents(num_agents):
    if num_agents == 0: return
    result = yfs._get("https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/players;status=FA;count={count};sort=AR".format(
        league_key=LEAGUE_KEY,
        count=num_agents
    )).json()
    for key, value in result['fantasy_content']['league'][1]['players'].items():
        if key == 'count':
            continue
        player_dict = {}
        for prop in value['player'][0]:
            if isinstance(prop, dict):
                for k, v in prop.items():
                    player_dict[k] = v
        player_dict['selected_position'] = "BN"
        yield Player.from_dict(player_dict)
