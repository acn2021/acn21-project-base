# Copyright 2021 Lin Wang

# This code is part of the Advanced Computer Networks course at Vrije 
# Universiteit Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#!/usr/bin/env python3

from id_mapping import IDMapping
from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types


from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

import topo
import copy

from datetime import datetime

class FTRouter(app_manager.RyuApp):
    """
    ## Core switches
      - terminating first-level prefixes for all pods (10.pod.0.0/16, port)

    ## Pod switches

    ### aggr switches: 
      - destination subnet switch prefix (10.pod.switch.0/24, port)

    ### edge switch:
      - ..


    How to solve the problem in steps:

    1. Find a way to map Fattree node ID to Mininet id and Ryu dpid.
        To solve this, I created a data structure IDMapping, that stores
        for each node its:
            - Mininet name, e.g. h1 for hosts or s1 for switches
            - Its Fattree address, e.g. 10.0.1.2 for hosts or 10.4.1.1 for core switches
        You can then query this data structure to convert between Mininet-name/Fattree-address/dpid.

    2. Obtain port mapping from switches to switches via topology discovery API
    3. Obtain port mapping from switches to servers via ARP

    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(FTRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(4)
        self.id_mapping = IDMapping(self.topo_net)

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        print("*** Switch has entered topo, running get_topology_data()")
        self.logger.info("*** testing logger")

        # Switches and links in the network
        # switches = get_switch(self, None)
        # links = get_link(self, None)

        # The Function get_switch(self, None) outputs the list of switches.
        self.topo_raw_switches = copy.copy(get_switch(self, None))
        # The Function get_link(self, None) outputs the list of links.
        self.topo_raw_links = copy.copy(get_link(self, None))

        print(" \t" + f"Current Links ({len(self.topo_raw_links)}):")
        for l in self.topo_raw_links:
            print (" \t\t" + str(l))

        print(" \t" + f"Current Switches ({len(self.topo_raw_switches)}):")
        for s in self.topo_raw_switches:
            print (" \t\t" + str(s))

        # switches = [switch.dp.id for switch in self.topo_raw_switches]
        # links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in self.topo_raw_links]
        # for sl in switches + links:
        #     print(sl)


    """
    This event is fired when a switch leaves the topo. i.e. fails.
    """
    @set_ev_cls(event.EventSwitchLeave, [MAIN_DISPATCHER, CONFIG_DISPATCHER, DEAD_DISPATCHER])
    def handler_switch_leave(self, ev):
        print("Switch left topo.")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        print("switch_features_handler called from event: ofp_event.EventOFPSwitchFeatures")
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # TODO: handle new packets at the controller

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        # If IPv6 multicast, ignore packet
        if (dst.startswith("33:33")):
            return

        # print(
        #     f"{FTRouter.get_time()} - Packet:"
        #     + f"\n\tARP?: {'true' if (eth.ethertype == ether_types.ETH_TYPE_ARP) else 'false'}"
        #     + f"\n\tIP packet - switch: {dpid} src: {src} dst: {dst} in_port: {in_port}"
        # )

    @staticmethod
    def get_time():
        now = datetime.now()

        current_time = now.strftime("%H:%M:%S")
        return current_time