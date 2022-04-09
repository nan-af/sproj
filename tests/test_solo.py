import json
from random import randint
import sys

sys.path.append('./')
from peer import solo   # noqa


host = solo.Solo()
out = {}
out['TOTAL'] = int(sys.argv[3])
out['success'] = 0
out['errors'] = {}

for i in range(out['TOTAL']):
    try:
        host.get(sys.argv[1], randint(1, int(sys.argv[2])), int(sys.argv[4]))
    except Exception as e:
        out['errors'][i] = repr(e)
    else:
        out['success'] += 1

print(json.dumps(out, indent=4))
