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
    """Stores the mapping for a Fattree deployed in a Mininet virtual network working with a Ryu
    controller.

    The mapping exists between two (three) things:
    - a Mininet node name, e.g. h1 for hosts and s1 for switches;
    - a node id/address in the fat tree, e.g. 10.0.0.1;
    - (the mininet node name can be converted to) an OpenFlow dpid (datapath id), 
        e.g. h0 -> 1 or s16 -> 16.

    The mininet host name is an autoincrement integer prefixed by the type of the node, h for host
    and s for switch.
    The fat tree id/address is based on the implementation of the paper given in the course.
    The datapath id is an integer.
    """

    # N_ZEROES_TO_PAD = 16

    def __init__(self, topo) -> None:
        self.mapping: Dict[str, str] = {}
        self._generate_mapping(topo)

    def get_dpid(self, node_id: str) -> Optional[str]:
        """Return the dpid mapped to the given node id.

        Args:
            node_id (str): the node id to get the dpid for

        Returns:
            Optional[str]: the dpid, or None if no mapping exists
        """
        value = self.mapping.get(node_id)
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
        return self.mapping.get(node_id)

    def get_node_id(self, dpid: str) -> Optional[str]:
        """Return the node id mapped to the given dpid.

        Args:
            dpid (str): the dpid to get the node id for

        Returns:
            Optional[str]: the node id, or None if no mapping exists
        """
        for node_id, _dpid in self.mapping.items():
            # if (self._pad_dpid_with_zeroes(_dpid) == self._pad_dpid_with_zeroes(dpid)):
            if (_dpid == dpid):
                return str(node_id)
        return None

    def _generate_mapping(self, topo):
        dpid_auto_increment = 0
        for server in topo.servers:
            self._add_mapping(server.id, f"h{dpid_auto_increment}")
            dpid_auto_increment += 1
        for switch in topo.switches:
            self._add_mapping(switch.id, f"s{dpid_auto_increment}")
            dpid_auto_increment += 1

    def _add_mapping(self, node_id: str, dpid: str) -> None:
        """Add a new mapping entry. Returns false if it already exists.

        Args:
            node_id (str): node id, e.g. 10.0.4.1
            dpid (str): datapath id, e.g. 1

        Returns:
            bool: True when successfully added
        """
        if (self.mapping.get(node_id)):
            raise MappingAlreadyExistsException(
                f"Mapping between {node_id} and {dpid} already exists")
        # self.mapping[node_id] = self._pad_dpid_with_zeroes(dpid)
        self.mapping[str(node_id)] = str(dpid)

    # def _pad_dpid_with_zeroes(self, dpid: str) -> str:
    #     return str(dpid).zfill(self.N_ZEROES_TO_PAD)

    def __str__(self) -> str:
        result = "node id to mininet id mapping:\n"
        for k, v in self.mapping.items():
            result += f"node id: {k}, dpid: {v}\n"
        return result

class MappingAlreadyExistsException(Exception):
    pass