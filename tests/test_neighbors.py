import json
from random import randint
import sys

sys.path.append('./')
from peer import neighbors   # noqa

host = neighbors.Peer(*sys.argv[1:5])
server_addr, distinct_files, file_sizes = sys.argv[5:8]

distinct_files = int(distinct_files)
file_sizes = int(file_sizes)

out = {}
out['success'] = 0
out['errors'] = {}

i = 0

try:
    while True:
        input()

        try:
            print(host.get(server_addr,
                           randint(1, distinct_files),
                           file_sizes))
        except Exception as e:
            out['errors'][i] = repr(e)
        else:
            out['success'] += 1
        i += 1

except KeyboardInterrupt:
    out['total'] = i

    out['log'] = host.out

    try:
        print(json.dumps(out, indent=4))
    except TypeError:
        out['host'] = str(out['host'])
        print(json.dumps(out, indent=4))
