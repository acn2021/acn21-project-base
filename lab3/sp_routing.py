# Copyright 2020 Lin Wang

# This code is part of the Advanced Computer Networks (2020) course at Vrije 
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

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet, ethernet, ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

from kruskal import kruskal

import topo

class SPRouter(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    NUMBER_OF_PORTS_PER_SWITCH = 4

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(self.NUMBER_OF_PORTS_PER_SWITCH)
        self.mac_to_port = {}
        self.flood_ports_switches = dict()
        self.initialized = False
        self.edge_switches = []
        self.ipv4_dests = dict()
        self.custom_topo = None
        self.raw_links = []

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Switches and links in the network
        switches = get_switch(self, None)
        links = get_link(self, None)
        switches = [switch.dp.id for switch in switches]
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links]

        for switch in switches:
            occupied_ports = []
            outgoing = 0
            for link in links:
                if link[0] == switch:
                    outgoing += 1
                    occupied_ports.append(link[2]["port"])
            if outgoing == int(self.topo_net.num_ports/2):
                self.edge_switches.append((switch, occupied_ports.copy()))

            occupied_ports.clear()


        if self.initialized or not (len(links) == self.topo_net.num_ports * len(self.topo_net.switches) - self.topo_net.num_ports**2):
            return

        # Get Minimal Spanning Tree
        mst = kruskal(switches,links)
        self.custom_topo = topo.MininetTopology(switches, links)
        self.raw_links = links
        extra_edges = []
        for edge in links:
            for other in mst:
                a, b, _ = edge
                c, d, _ = other
                if (a,b) == (d, c):
                    extra_edges.append(edge)
        mst = mst + extra_edges
            
        # mst will be used for flooding, not the full network. Not forgetting edge-switches.

        # Initializing the flooding of the ports.
        for switch in switches:
            self.flood_ports_switches[str(switch)] = []
        
        for edge in mst:
            self.flood_ports_switches[str(edge[0])].append(edge[2])
        
        # Find open ports in the edge-switches to also flood.
        for pair in self.edge_switches:
            switch, ports_used = pair
            for i in range(1, self.topo_net.num_ports+1):
                if i not in ports_used and {'port': i} not in self.flood_ports_switches[str(switch)]:
                    self.flood_ports_switches[str(switch)].append({'port': i})

        self.initialized = True
        print("Controller initialized...")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def get_flooding_ports(self, dpid, port_in):
        flood_ports = []
        raw = self.flood_ports_switches[str(dpid)]
        for port in raw:
            flood_ports.append(port["port"])
        if port_in in flood_ports:
            flood_ports.remove(port_in)
        return flood_ports

    def construct_shortest_path(self, src_dpid, dst_dpid):
        if src_dpid == dst_dpid:
            return []
        src = None
        dst = None
        for switch in self.custom_topo.switches:
            if switch.id == src_dpid:
                src = switch
            if switch.id == dst_dpid:
                dst = switch
        tp = topo.Paths(self.custom_topo)
        path = tp.construct_path(src, dst)
        path = [x.id for x in path]
        return path


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
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})


        # Parsing the data into a packet
        pkt = packet.Packet(msg.data)

        # Whether request/response is ARP or IP
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        # LLDP protocol for the Ryu controller, a.k.a. not needed
        if not arp_pkt and not ip_pkt or eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        if arp_pkt:
            src = arp_pkt.src_ip
            dst = arp_pkt.dst_ip
        else:
            src = ip_pkt.src
            dst = ip_pkt.dst

        ##### Shortest Path Routing #####
        if not src in self.ipv4_dests:
            self.ipv4_dests[src] = (dpid, in_port)
        
        # Find next switch to be reached and add to flowtable of the switch
        if dst in self.ipv4_dests:
            # Calculate path between dpids
            src_dpid = dpid
            dst_dpid = self.ipv4_dests[dst][0]
            path = self.construct_shortest_path(src_dpid, dst_dpid)
            if len(path) == 0:
                # at source
                out_port = self.ipv4_dests[dst][1]
            else:
                dst_dpid = path[1]
                for link in self.raw_links:
                    if link[0] == src_dpid and link[1] == dst_dpid:
                        out_port = link[2]['port']

            match = parser.OFPMatch(in_port=in_port, ipv4_dst=dst, ipv4_src=src)
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions)

            data = msg.data
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out) 
            return
        ##### Flooding using mst (Minimal Spanning Tree) #####

        # Reached if flooding is needed
        actions = []
        out_ports = self.get_flooding_ports(dpid, in_port)
        for port in out_ports:
            actions.append(parser.OFPActionOutput(port))

        match = parser.OFPMatch(in_port=in_port, ipv4_dst=dst, ipv4_src=src)
    
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)