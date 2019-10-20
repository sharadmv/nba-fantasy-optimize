import pandas as pd
from functools import partial
from path import Path
import json
import tempfile

OUTDIR = Path(".data")

if not OUTDIR.exists():
    OUTDIR.mkdir()

class memoize(object):
    def __init__(self, func):
        self.func = func
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.func
        return partial(self, obj)
    def __call__(self, *args, **kw):
        obj = args[0]
        try:
            cache = obj.__cache
        except AttributeError:
            cache = obj.__cache = {}
        key = (self.func, args[1:], frozenset(kw.items()))
        try:
            res = cache[key]
        except KeyError:
            res = cache[key] = self.func(*args, **kw)
        return res


def cache(name, fmt='json'):
    path = OUTDIR / name
    def loc(func):
        def wrapped(*args, **kwargs):
            if not path.exists():
                result = func(*args, **kwargs)
                if fmt == 'json':
                    with open(path, 'w') as fp:
                        json.dump(result, fp)
                elif fmt == 'pandas':
                    with open(path, 'w', newline='') as fp:
                        result.to_csv(fp, index=False)
                return result
            else:
                if fmt == 'json':
                    with open(path, 'r') as fp:
                        return json.load(fp)
                elif fmt == 'pandas':
                    return pd.read_csv(path)
        return wrapped
    return loc
