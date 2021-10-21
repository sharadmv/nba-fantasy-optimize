import functools
import pprint as _pprint

import tabulate
import yfpy

@functools.singledispatch
def pprint(obj: object, **kwargs) -> None:
  _pprint.pprint(obj, **kwargs)


@pprint.register
def _(roster: yfpy.models.Roster, *, include_bench: bool = False,
    include_injured: bool = False) -> None:
  ignore = {'BN', 'IL'}
  if include_bench:
    ignore.remove("BN")
  if include_injured:
    ignore.remove("IL")
  table = []
  for player in roster.players:
    player = player['player']
    position = player.selected_position.position
    if position not in ignore:
      table.append([position, player.name.full])
  print(tabulate.tabulate(table))
