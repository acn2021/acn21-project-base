from address import Address
from id_mapping import IDMapping


class SwitchRoutingTables:
    """Routing follows this pattern:

    Core switches: 
        ***switch: 10.4.1.1
        10.0.0.0/16 -> 1
        10.1.0.0/16 -> 2
        10.2.0.0/16 -> 3
        10.3.0.0/16 -> 4
    
    Aggregation switches:
        ***switch: 10.0.2.1
        10.0.0.0/24 -> 1
        []
        10.0.1.0/24 -> 2
        []
        0.0.0.0/0 -> 0
        [{'suffix': '0.0.0.2/8', 'port': 3}, {'suffix': '0.0.0.3/8', 'port': 4}]

        ***switch: 10.0.3.1
        10.0.0.0/24 -> 1
        []
        10.0.1.0/24 -> 2
        []
        0.0.0.0/0 -> 0
        [{'suffix': '0.0.0.2/8', 'port': 4}, {'suffix': '0.0.0.3/8', 'port': 3}]

    Edge switches:
        ***switch: 10.0.0.1
        0.0.0.0/0 -> 0
        [{'suffix': '0.0.0.2/8', 'port': 3}, {'suffix': '0.0.0.3/8', 'port': 4}]

        ***switch: 10.0.1.1
        0.0.0.0/0 -> 0
        [{'suffix': '0.0.0.2/8', 'port': 4}, {'suffix': '0.0.0.3/8', 'port': 3}]
    """

    def __init__(self, k, links, id_mapping: IDMapping) -> None:

        self.k = k # number of ports per switch
        self.links = links
        self.id_mapping = id_mapping
        # Routing tables in the form prefix/suffix: output port {"10.2.0.0/24": 0}
        self.prefix_tables = {}

        # Generate the tables
        self._generate_core_switch_routing_tables()
        self._generate_aggr_switch_routing_tables()
        self._generate_edge_switch_routing_tables()
        # print(self)

    def lookup_port(self, src_node_id, dst_node_id):
        dest_address = Address(dst_node_id)
        # print(f"From: {dest_address.raw}")
        # Match on prefix
        for i in range(0, len(self.prefix_tables[src_node_id])):
            row = self.prefix_tables[src_node_id][i]
            # print(f"Compare with prefix: {row['prefix'].raw}")
            if (dest_address.matches(row["prefix"])):
                # print("MATCH!")
                # print(row["port"])
                return row["port"]
            # print("no match")
                
            # Do lookup in suffix table linked to the last entry of the prefix table
            zero_prefix_reached = i == len(self.prefix_tables[src_node_id]) - 1
            if (zero_prefix_reached):
                suffix_table = row["suffix_table"]
                for suffix_row in suffix_table:
                    suffix_address = Address(suffix_row["suffix"])
                    # print(f"Compare with suffix: {suffix_address.raw}")

                    if (dest_address.matches(suffix_address, mode="right-handed")):
                        # print("MATCH!")
                        # print(suffix_row["port"])
                        return suffix_row["port"]
                    # print("no match")

    # def sync_ports(self, get_links_data, id_mapping: IDMapping):
    #     n_updates = 0
    #     # Get correct port data from topo
    #     for link in get_links_data:
    #         src_node_id = id_mapping.get_node_id_from_dpid(link[0])
    #         # print(src_node_id)
    #         dest_node_id = id_mapping.get_node_id_from_dpid(link[1])
    #         # print(link)
    #         port = link[2]["port"]
    #         # Sync prefix tables ports
    #         for switch, table in self.prefix_tables.items():
    #             if (switch == src_node_id): # found table entry that matches current link
    #                 for entry in table:
    #                     prefix = entry["prefix"]
    #                     if (Address(dest_node_id).matches(prefix)):
    #                         # Update
    #                         # print(f"Updating port {entry['port']} with {port}")
    #                         if (entry["port"] != port):
    #                             entry["port"] = port
    #                             n_updates += 1
    #                     else:
    #                         suffix_table = entry["suffix_table"]
    #                         for suffix_row in suffix_table:
    #                             suffix_address = Address(suffix_row["suffix"])

    #                             if (Address(dest_node_id).matches(suffix_address, mode="right-handed")):
    #                                 if (entry["port"] != port):
    #                                     entry["port"] = port
    #                                     # n_updates += 1

            # print("NUMBER OF TABLE UPDATES = ", n_updates)

    def _find_correct_port(self, src, dst):
        dst = Address(dst)

        # Prefix: find links where src matches given src
        for link in self.links:
            src_node_id = self.id_mapping.get_node_id_from_dpid(link[0])
            dest_node_id = self.id_mapping.get_node_id_from_dpid(link[1])
            port = link[2]["port"]

            if (src_node_id == src):
                # If destination matches given destination, return the port
                if (Address(dest_node_id).matches(dst)): # Prefix matching
                    # print(f"Match: ({src} - {dst}) on ({src_node_id} - {dest_node_id}) port {port}")
                    return port

        # Suffix: find links where src matches given src
        for link in self.links:
            src_node_id = self.id_mapping.get_node_id_from_dpid(link[0])
            dest_node_id = self.id_mapping.get_node_id_from_dpid(link[1])
            port = link[2]["port"]

            if (src_node_id == src):
                # If destination matches given destination, return the port
                if (Address(dest_node_id).matches(dst, "right-handed")):  # Suffix matching
                    print(f"Match: ({src} - {dst}) on ({src_node_id} - {dest_node_id}) port {port}")
                    return port
    
    def _generate_core_switch_routing_tables(self):
        k = self.k
        for j in range(1, int(k/2) + 1):
            for i in range(1, int(k/2) + 1):
                # for dest_pod_num in range(0, int(k/2)):
                for dest_pod_num in range(0, k):
                    x = dest_pod_num
                    src = f"10.{k}.{j}.{i}"
                    dst = f"10.{x}.0.0/16"
                    # port = self._find_correct_port(src, dst)
                    self._addPrefix(src, dst, x + 1)

    def _generate_aggr_switch_routing_tables(self):
        k = self.k
        for pod in range(0, int(k)): # 0 1 2 3
            x = pod
            for switch in range(int(k/2), int(k)): # 2 switches 10.x.(2 or 3).1
                z = switch

                for subnet in range(0, int(k/2)): # 0, 1 subnets
                    i = subnet
                    # Destination subnet switch / edge switch (in pod)
                    src = f"10.{x}.{z}.1"
                    dst = f"10.{x}.{i}.0/24"
                    # port = self._find_correct_port(src, dst)
                    self._addPrefix(src, dst, i + 1)

                self._addPrefix(f"10.{x}.{z}.1", f"0.0.0.0/0", 0)
            
                for host_id in range(2, int(k/2)+2):
                    i = host_id
                    # Link going upwards from pod node 
                    src = f"10.{x}.{z}.1"
                    dst = f"0.0.0.{i}/8"
                    # port = self._find_correct_port(src, dst)
                    self._addSuffix(src, dst, 1 + int( ((i - 2 + z) % (k/2)) + (k/2)) )
                        # int((i - 2 + z) % (k/2) + (k/2)))

    def _generate_edge_switch_routing_tables(self):
        k = self.k
        for pod in range(0, int(k)): # 0 1 2 3
            x = pod
            for switch in range(0, int(k/2)): # 2 switches 10.x.(0 or 1).1
                z = switch

                self._addPrefix(f"10.{x}.{z}.1", f"0.0.0.0/0", 0)
    
                for host_id in range(2, int(k/2)+2):
                    i = host_id
                    src = f"10.{x}.{z}.1"
                    dst = f"0.0.0.{i}/8"
                    # port = self._find_correct_port(src, dst)
                    self._addSuffix(src, dst, 1 + int( ((i - 2 + z) % (k/2)) + (k/2)) )
                        # int((i - 2 + z) % (k/2) + (k/2)) - 2)

    def _addPrefix(self, switch, prefix, port):
        prefix_addr = Address(prefix)
        self.prefix_tables.setdefault(switch, [])

        self.prefix_tables[switch].append({
            "prefix": prefix_addr,
            "port": port,
            "suffix_table": [] # only used for the last entry of the table for each switch
        })
        

    def _addSuffix(self, switch, suffix, port):
        last_index = len(self.prefix_tables[switch]) - 1
        self.prefix_tables[switch][last_index]["suffix_table"].append({
            "suffix": suffix,
            "port": port
        })

    def __str__(self) -> str:
        result = ""
        result += ("prefix tables:") + "\n"
        for switch, table in self.prefix_tables.items():
            result += (f"\n***switch: {switch}") + "\n"
            for entry in table:
                result += str(entry["prefix"].raw) + " -> " + str(entry["port"]) + "\n"
                result += str(entry["suffix_table"]) + "\n"
        return result 
    