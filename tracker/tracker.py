import json
import sys

import zmq

PORT = int(sys.argv[1])

context = zmq.Context()

new_peer = context.socket(zmq.REP)
new_peer.bind(f"tcp://*:{PORT}")
print(f'New peer socket bound at {PORT}')

old_peers = context.socket(zmq.PUB)
old_peers.bind(f"tcp://*:{PORT+1}")
print(f'Old peers socket bound at {PORT+1}')

peers = set()
out = {}
out['log'] = []
out['errors'] = []

try:
    while True:
        peer_addr = tuple(new_peer.recv_json())

        peers.add(peer_addr)

        out['log'].append(
            f'Received address: {peer_addr},\tTotal number of peers: {len(peers)}')

        new_peer.send_json(list(peers))

        old_peers.send_multipart(
            (b'tracker', json.dumps(list(peers)).encode()))
except KeyboardInterrupt:
    out['count'] = len(out['log'])
    print(json.dumps(out, indent=4))
