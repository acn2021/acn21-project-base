# Copyright 2021 Misha Rigot

# This code is part of the Advanced Computer Networks course at VU 
# Amsterdam.

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

from typing import Dict, Optional

class IDMapping:
    """Stores the mapping for a Fattree, deployed in a Mininet virtual network,
    working with a Ryu controller.

    You can convert several values (also in reverse), for example:

    - Fattree node id to mininet node name: 
        10.0.0.2 <-> h1
        10.0.2.1 <-> s16
    - Fattree node id to dpid:
        10.0.0.2 <-> 1
        10.0.2.1 <-> 16
    - Fattree node id to mininet IP ($ h0 ifconfig):
        10.0.0.2 <-> 10.0.0.1

    The mininet host name is an auto-increment integer prefixed by the type of the node, 
    'h' for host and 's' for switch.
    The fat tree id/address is based on the implementation of the paper given in the course.
    The datapath id is an integer.
    The ip is an auto-increment, e.g.: 10.0.0.1, 10.0.0.2, etc.
    """

    def __init__(self, topo) -> None:
        self.node_id_to_mininetid: Dict[str, str] = {}
        self.ip_to_node_id_mapping: Dict[str, str] = {}
        self._generate_mapping(topo)

    def get_dpid(self, node_id: str) -> Optional[str]:
        """Return the dpid mapped to the given node id.

        Args:
            node_id (str): the node id to get the dpid for

        Returns:
            Optional[str]: the dpid, or None if no mapping exists
        """
        value = self.node_id_to_mininetid.get(node_id)
        if (value is None): 
            return None

        result = value.replace("h", "").replace("s", "")
        return result

    def get_mininet_id(self, node_id: str) -> Optional[str]:
        """Return the mininet id, e.g. h0 or s16.

        Args:
            node_id (str): Fattree address e.g. 10.0.0.2
        Returns:
            Optional[str]: the corresponding mapping to the mininet id, e.g. h0
        """
        return self.node_id_to_mininetid.get(node_id)

    def get_node_id_from_dpid(self, dpid: str) -> Optional[str]:
        """Return the node id mapped to the given dpid.

        Args:
            dpid (str): the dpid to get the node id for

        Returns:
            Optional[str]: the node id, or None if no mapping exists
        """
        for node_id, mininet_id in self.node_id_to_mininetid.items():
            _dpid = mininet_id.replace("h", "").replace("s", "")
            if (str(_dpid) == str(dpid)):
                return str(node_id)
        return None

    def get_node_id_from_ip(self, ip: str) -> Optional[str]:
        """Return the node id mapped to the given ip.

        Args:
            ip (str): the mininet IP to get the node id for

        Returns:
            Optional[str]: the node id, or None if no mapping exists
        """
        return self.ip_to_node_id_mapping.get(ip)


    def get_ip(self, node_id: str) -> Optional[str]:
        """Returns the IP address of the fattree node_id given. 

        Args:
            node_id (str): e.g. 10.0.0.2

        Returns:
            Optional[str]: corresponding IP address, e.g. 10.0.0.1
        """
        for ip, _node_id in self.ip_to_node_id_mapping.items():
            if (node_id == _node_id):
                return ip
        raise KeyError(f"Could not find ip for node id {node_id}.")

    def _generate_mapping(self, topo):
        """For each server- and switch's id, map a mininet id to it,
        e.g. h0 or s16.

        Args:
            topo (Fattree): topology to generate the mapping for
        """
        dpid_auto_increment = 0
        for server in topo.servers:
            self._add_mininet_mapping(server.id, f"h{dpid_auto_increment}")
            self._add_ip_mapping(server.id, dpid_auto_increment)
            dpid_auto_increment += 1
        for switch in topo.switches:
            self._add_mininet_mapping(switch.id, f"s{dpid_auto_increment}")
            dpid_auto_increment += 1

    def _add_mininet_mapping(self, node_id: str, mininet_id: str) -> None:
        """Add a new mapping entry. Returns false if it already exists.

        Args:
            node_id (str): node id, e.g. 10.0.4.1
            mininet_id (str): mininet id, e.g. h0 or s16

        Returns:
            bool: True when successfully added
        """
        if (self.node_id_to_mininetid.get(node_id)):
            raise MappingAlreadyExistsException(
                f"Mapping between {node_id} and {mininet_id} already exists")
        self.node_id_to_mininetid[str(node_id)] = str(mininet_id)

    def _add_ip_mapping(self, node_id: str, mininet_id: int) -> None:
        """Map an IP

        Args:
            node_id (str): [description]
            mininet_id (int): [description]

        Raises:
            MappingAlreadyExistsException: [description]
        """
        ip = f"10.0.0.{str(mininet_id + 1)}"
        if (self.ip_to_node_id_mapping.get(ip)):
            raise MappingAlreadyExistsException(
                f"Mapping between ip {ip} and node_id {node_id} already exists")
        self.ip_to_node_id_mapping[ip] = node_id

    def __str__(self) -> str:
        """Returns the mapping as a string representation useful for printing/debugging.
        """
        result = "***node id to mininet id mapping:\n\n"
        for k, v in self.node_id_to_mininetid.items():
            result += f"node id: {k}, dpid: {v}\n"

        result += "\n***ip to node_id mapping:\n\n"
        for k, v in self.ip_to_node_id_mapping.items():
            result += f"ip: {k}, node_id: {v}\n"
        return result

class MappingAlreadyExistsException(Exception):
    pass