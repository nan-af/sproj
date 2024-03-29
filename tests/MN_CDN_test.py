#!/usr/bin/env python

import json
from random import randint
from signal import SIGALRM, alarm, signal
import sys

sys.path.append('/usr/lib/python3.10/site-packages')  # noqa

from pathlib import Path
from time import sleep, strftime
from mininet.log import lg, info
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch
from mininet.topo import Topo, SingleSwitchTopo


def timeout(signum, frame):
    print('Timeout!')
    raise KeyboardInterrupt


signal(SIGALRM, timeout)


class nHopTopo(Topo):
    "Two clusters of sizes a and b, separated by n hops"

    def build(self, k=None, n=20, a=2, b=2):
        if k:
            b = k - a

        # n-1 switches needed for n hops
        switches = [self.addSwitch(f's{i+1}') for i in range(n-1)]

        for i in range(len(switches)-1):
            self.addLink(switches[i], switches[i+1])

        for i in range(a):
            host = self.addHost(f'h{i+1}')
            self.addLink(host, switches[0])

        for i in range(b):
            # continue numbering from where `a` left off
            host = self.addHost(f'h{i+a+1}')
            self.addLink(host, switches[-1])


def soloTest(net, distinct_files=10, requests=100, file_sizes=10):
    server = net.hosts[0]
    server_ip = server.IP()
    # IANA ephemeral ports range. Also RFC 6335.
    server_port = randint(49152, 65535)

    server.sendCmd(f'pipenv run python server/server.py {server_port}')
    server.readline()

    for host in net.hosts[1:]:
        host.sendCmd(
            f'pipenv run python tests/test_solo.py "http://{server_ip}:{server_port}" {distinct_files} {file_sizes} {requests}')

    outputs = {}
    outputs['clients'] = {}

    success = True

    for host in net.hosts[1:]:
        name = str(host)

        outputs['clients'][name] = host.waitOutput()
        print(name, end=' ')
        try:
            outputs['clients'][name] = json.loads(outputs['clients'][name])
        except json.JSONDecodeError:
            print('Error :(', end='')
            success = False
        else:
            if outputs['clients'][name]['errors']:
                print('Error :(', end='')
                success = False
            else:
                print('Success!', end='')
        print()

    server.sendInt()
    server_output = server.waitOutput()
    try:
        outputs['server'] = json.loads(server_output)
    except Exception as e:
        print(repr(e))
        outputs['server'] = server_output
        success = False

    if success:
        print(f'Tested {len(net.hosts)-1} hosts successfully!')
    else:
        print('Some or all hosts returned errors')
    outputs['success'] = success

    return outputs


def peerTest(net, distinct_files=10, requests=100, file_sizes=10):
    server = net.hosts[0]
    server_ip = server.IP()
    # IANA ephemeral ports range. Also RFC 6335.
    server_port = randint(49152, 65535)

    tracker = net.hosts[1]
    tracker_ip = tracker.IP()
    # Subtracting 1 from the IANA range because tracker needs two ports
    tracker_port = randint(49152, 65534)

    server.sendCmd(f'pipenv run python server/server.py {server_port}')
    # server.waitReadable()
    while not (lineout := server.readline()):
        pass
    print(lineout)

    tracker.sendCmd(
        f'pipenv run python tracker/tracker.py {tracker_port}')
    while not (lineout := tracker.readline()):
        pass
    print(lineout)
    while not (lineout := tracker.readline()):
        pass
    print(lineout)

    clients = net.hosts[2:]

    for host in clients:
        host.sendCmd(
            'pipenv run python tests/test_neighbors.py '
            + f'{host.IP()} {randint(49152, 65535)} {tracker_ip} {tracker_port} '
            + f'"http://{server_ip}:{server_port}" {distinct_files} {file_sizes}')
        while not (lineout := host.readline()):
            pass
        print(lineout)
        while not (lineout := host.readline()):
            pass
        print(lineout)

    outputs = {}
    outputs['clients'] = {}
    # outputs['clients']['files'] = {}

    for i in range(int(requests)):
        # outputs['clients']['files'][i] = []
        for host in clients:
            host.write('\n')
            name = str(host)
            sleep(0.020)
            # host.waitReadable()
            # outputs['clients']['files'][i].append((name, host.readline()))
            while not host.readline():
                pass

    for host in net.hosts:
        host.sendInt()

    success = True

    for host in net.hosts[:2]:
        name = str(host)
        # host.waitOutput()
        # while not outputs['clients'][name]:
        try:
            alarm(20)
            outputs['clients'][name] = host.waitOutput(verbose=True)
        except KeyboardInterrupt:
            # os.killpg(host.lastPid, signal.SIGHUP)
            try:
                outputs['clients'][name] = host.read(2**30)
                print(outputs['clients'][name])
            except KeyboardInterrupt:
                outputs['clients'][name] = ''
        finally:
            alarm(0)

        print(name, end=' ')
        try:
            outputs['clients'][name] = json.loads(outputs['clients'][name])
        except json.JSONDecodeError:
            print('Error :(')
            success = False
        else:
            if outputs['clients'][name]['errors']:
                print('Error :(')
                success = False
            else:
                print('Success!')
        # print(f'{name} complete')
    # for host in clients:
    #     outputs['clients'][name] = {}

    if success:
        print(f'Tested {len(clients)} hosts successfully!')
    else:
        print('Some or all hosts returned errors')
    outputs['success'] = success

    return outputs


def create_test_stop(k, client_type, test_args=[]):
    lg.setLogLevel('info')

    info("*** Initializing Mininet and kernel modules\n")
    OVSKernelSwitch.setup()

    info("*** Creating network\n")
    network = Mininet(nHopTopo(k=k, a=1 if client_type == 'solo' else 2), switch=OVSKernelSwitch,
                      waitConnected=True)
    # network = Mininet(SingleSwitchTopo(k=k), switch=OVSKernelSwitch,
    #                   waitConnected=True)

    info("*** Starting network\n")
    network.start()

    info(f"*** Running CDN {client_type} test\n")
    if client_type == 'peer':
        outputs = peerTest(network, *test_args)
    else:
        outputs = soloTest(network, *test_args)

    outputs['stats'] = {}
    info("*** Collecting stats\n")
    #     outputs['clients'][str(host)]['stats'] = json.loads(
    #         host.cmd('ip -stats -json link'))
    for s in network.switches:
        outputs['stats'][str(s)] = json.loads(s.cmd('ip -stats -json link'))

    # info("*** Stopping network\n")
    # network.stop()

    return outputs


if __name__ == '__main__':
    client_type, num_of_hosts = sys.argv[1:3]
    num_of_hosts = int(num_of_hosts)

    outputs = create_test_stop(num_of_hosts+2 if client_type == 'peer' else num_of_hosts+1,
                               client_type,
                               sys.argv[3:6])

    if len(sys.argv) > 6:
        outfile = Path(sys.argv[6])
    else:
        outfile = Path('/tmp/mn_' +
                       sys.argv[1] + '_' + strftime('%H.%M.%S') + '.json')

    outfile.touch(0o777)
    outfile.write_text(json.dumps(outputs, indent=4))

    print('JSON log written to', outfile)
