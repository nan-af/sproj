import json
import sys
import threading

import zmq

from solo import Solo


class Peer(Solo):
    def __init__(self) -> None:
        # Hacky but I can't figure out how to get IP address from within Mininet
        # Update: there's a Python library `netifaces`
        # TODO: use that instead
        self.IP = sys.argv[1]
        self.PORT = sys.argv[2]
        self.TR_REQ_ADDR = 'tcp://'+sys.argv[3]+':'+sys.argv[4]
        self.TR_SUB_ADDR = 'tcp://'+sys.argv[3]+':'+str(int(sys.argv[4])+1)

        context = zmq.Context()
        self.tr_sub = context.socket(zmq.SUB)
        self.tr_req = context.socket(zmq.REQ)

        self.peers = set()

    def sub_tracker(self) -> None:
        print(f"Connecting to tracker's PUB socket at {self.TR_SUB_ADDR}")
        self.tr_sub.connect(self.TR_SUB_ADDR)
        self.tr_sub.setsockopt(zmq.SUBSCRIBE, b'tracker')

        def listen_sub() -> None:
            while True:
                message = self.tr_sub.recv_multipart()
                self.peers = {x for x in json.loads(message[1].decode())
                              if x != (self.IP+':'+self.PORT)}
                print(self.peers)

        threading.Thread(target=listen_sub).start()

    def connect_tracker(self) -> None:
        print(f"Connecting to tracker's REP socket at {self.TR_REQ_ADDR}")
        self.tr_req.connect(self.TR_REQ_ADDR)

        self.tr_req.send((self.IP+':'+self.PORT).encode())
        self.tr_req.recv()     # receiving list of peers from tracker.
        # Not saving in a variable because it's redundant; the SUB socket is going to take care of this anyways.
        # Necessary to receive though because of the REQ/REP socket sending pattern.
        # There's probably a better way


if __name__ == "__main__":
    peer = Peer()
    peer.sub_tracker()
    peer.connect_tracker()
