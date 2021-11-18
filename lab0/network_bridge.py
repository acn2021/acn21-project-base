# Copyright 2021 Lin Wang
#
# This code is part of the Advanced Computer Networks (ACN) course at VU 
# Amsterdam.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#!/usr/bin/python

from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import OVSKernelSwitch


class BridgeTopo(Topo):
    "Create a bridge-like customized network topology."

    def __init__(self):

        Topo.__init__(self)

        # Add hosts and switches
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # Add links
        hostLinkBw = 15
        hostLinkDelay = "10ms"

        self.addLink(h1, s1, bw=hostLinkBw, delay=hostLinkDelay)
        self.addLink(h2, s1, bw=hostLinkBw, delay=hostLinkDelay)
        self.addLink(h3, s2, bw=hostLinkBw, delay=hostLinkDelay)
        self.addLink(h4, s2, bw=hostLinkBw, delay=hostLinkDelay)

        switchLinkBw = 20
        switchLinkDelay = "45ms"
        
        self.addLink(s1, s2, bw=switchLinkBw, delay=switchLinkDelay)


topos = {'bridge': (lambda: BridgeTopo())}
