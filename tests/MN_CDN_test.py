#!/usr/bin/env python

import json
import sys

from pathlib import Path
from time import strftime
from mininet.log import lg, info
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch
from mininet.topo import SingleSwitchTopo


def soloTest(net, distinct_files=10, requests=100, file_sizes=10):
    server_ip = net.hosts[0].IP()
    server_port = net.hosts[0].newPort()

    net.hosts[0].sendCmd(f'pipenv run python server/server.py {server_port}')
    net.hosts[0].readline()

    for host in net.hosts[1:]:
        host.sendCmd(
            f'pipenv run python tests/test_solo.py "http://{server_ip}:{server_port}" {distinct_files} {requests} {file_sizes}')

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

    net.hosts[0].sendInt()
    server_output = net.hosts[0].waitOutput()
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


def create_test_stop(k, client_type, test_args=[]):
    lg.setLogLevel('info')

    info("*** Initializing Mininet and kernel modules\n")
    OVSKernelSwitch.setup()

    info("*** Creating network\n")
    network = Mininet(SingleSwitchTopo(k=k), switch=OVSKernelSwitch,
                      waitConnected=True)

    info("*** Starting network\n")
    network.start()

    info("*** Running CDN test\n")
    outputs = soloTest(network, *test_args)

    info("*** Stopping network\n")
    network.stop()

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
