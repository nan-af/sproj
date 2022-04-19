import json
from random import randint
import sys

sys.path.append('./')
from peer import solo   # noqa

server_addr, distinct_files, file_sizes, requests = sys.argv[1:5]
host = solo.Solo()

distinct_files = int(distinct_files)
file_sizes = int(file_sizes)
requests = int(requests)

out = {}
out['total'] = requests
out['success'] = 0
out['errors'] = {}

for i in range(requests):
    try:
        host.get(server_addr,
                 randint(1, distinct_files),
                 file_sizes)
    except Exception as e:
        out['errors'][i] = repr(e)
    else:
        out['success'] += 1

print(json.dumps(out, indent=4))
