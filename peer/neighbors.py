import json
import sys
import threading

import zmq

from .solo import Solo


class Peer(Solo):
    def __init__(self, ip, port, tr_ip, tr_port) -> None:
        # Hacky but I can't figure out how to get IP address from within Mininet
        # Update: there's a Python library `netifaces`
        # TODO: use that instead
        self.IP = ip
        self.PORT = int(port)
        self.TR_REQ_ADDR = 'tcp://'+tr_ip+':'+tr_port
        self.TR_SUB_ADDR = 'tcp://'+tr_ip+':'+str(int(tr_port)+1)

        super().__init__()

        self.context = zmq.Context()
        self.tr_sub = self.context.socket(zmq.SUB)      # tracker SUBSCRIBE
        self.tr_req = self.context.socket(zmq.REQ)      # tracker REQUEST
        self.pr_pub = self.context.socket(zmq.PUB)      # peer PUBLISH
        self.pr_rep = self.context.socket(zmq.REP)      # peer REPLY

        self.pr_rep.bind(f'tcp://*:{self.PORT}')
        self.pr_pub.bind(f'tcp://*:{self.PORT+1}')

        self.peers = {}
        self.peer_files = {}

        self.sub_tracker()
        self.connect_tracker()

        threading.Thread(target=self.listen_peer_rep).start()

    def sub_tracker(self) -> None:
        print(f"Connecting to tracker's PUB socket at {self.TR_SUB_ADDR}")
        self.tr_sub.connect(self.TR_SUB_ADDR)
        self.tr_sub.setsockopt(zmq.SUBSCRIBE, b'tracker')

        threading.Thread(target=self.listen_tr).start()

    def listen_tr(self) -> None:
        while True:
            self.update_peers(
                json.loads(
                    # [0] is topic, [1] is the actual message
                    self.tr_sub.recv_multipart()[1]
                    .decode()
                )
            )

    def connect_tracker(self) -> None:
        print(f"Connecting to tracker's REP socket at {self.TR_REQ_ADDR}")
        self.tr_req.connect(self.TR_REQ_ADDR)

        self.tr_req.send_json((self.IP, self.PORT))
        self.tr_req.recv()    # receiving list of peers from tracker.
        # Not saving in a variable because it's redundant; the SUB socket is going to take care of this anyways.
        # Necessary to receive though because of the REQ/REP socket sending pattern.
        # There's probably a better way. TODO: Find that better way.

    def update_peers(self, new_peer_list):
        # self.peers = {Connection(x, self.context) for x in new_peer_list
        #               if x != (self.IP+':'+self.PORT)}
        for peer in new_peer_list:
            peer = tuple(peer)
            if peer not in self.peers \
                    and peer != (self.IP, self.PORT):
                print('New peer:', peer)
                new_peer = Connection(peer, self.context)
                self.peers[peer] = new_peer

                threading.Thread(target=self.listen_peer_pub,
                                 args=(new_peer,)).start()

        print('Peers:', self.peers)

    def listen_peer_pub(self, peer):
        while True:
            msg = peer.sub.recv_multipart()
            addr = tuple(json.loads(msg[2].decode()))

            for file in json.loads(
                msg[1].decode()
            ):
                file = tuple(file)
                self.peer_files[file] = addr
                print(self.peer_files)

    def listen_peer_rep(self):
        while True:
            msg = self.pr_rep.recv_json()
            self.pr_rep.send_json(self.cache.get(tuple(msg)))

    def get(self, server: str, id: int, size: int):
        if data := self.cache.get((server, id, size)):
            return data
        if peer := self.peer_files.get((server, id, size)):
            peer_con = self.peers[peer].req

            peer_con.send_json((server, id, size))
            data = peer_con.recv_json()

            return data

        data = self.get_from_server(server, id, size)

        self.pr_pub.send_multipart(
            (b'file_list',
             json.dumps(list(self.cache.keys())).encode(),
             json.dumps((self.IP, self.PORT)).encode()
             ))

        return data


class Connection():
    def __init__(self, address, context):
        self.ip = address[0]
        self.port = int(address[1])
        self.address_req = f'{self.ip}:{self.port}'
        self.address_sub = f'{self.ip}:{self.port+1}'
        self.sub = context.socket(zmq.SUB)
        self.req = context.socket(zmq.REQ)

        self.sub.connect('tcp://'+self.address_sub)
        self.sub.setsockopt(zmq.SUBSCRIBE, b'file_list')

        self.req.connect('tcp://'+self.address_req)

    # def __eq__(self, other):
    #     return str(self) == str(other)

    # def __hash__(self):
    #     return hash(self.address_req)

    # def __repr__(self):
    #     return self.address_req


if __name__ == "__main__":
    peer = Peer(*sys.argv[1:5])
    # peer.sub_tracker()
    # peer.connect_tracker()
