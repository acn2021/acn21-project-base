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

import topo
import random
import matplotlib.pyplot as plt

# Setup for Jellyfish
num_servers = 686
num_switches = 245
num_ports = 14

jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

# TODO: code for reproducing Figure 9 in the jellyfish paper
# Set ITERATIONS to 10 for an average
ITERATIONS = 1

tp = topo.Paths(jf_topo)

# creating a dict of all switch - switch connections that are connected with an edge.
switch_dict = dict()
for switch in jf_topo.switches:
    for edge in switch.edges:
        other_switch = edge.lnode if edge.lnode != switch else edge.rnode
        # omitting all of the switch-server connections. Only inter-switch connections are counted in figure 9
        if other_switch.type == "server":
            continue
        switch_dict[(switch, other_switch)] = 0
        switch_dict[(other_switch, switch)] = 0

ecmp8_switch_dict = switch_dict.copy()
ecmp64_switch_dict = switch_dict.copy()


def extract_switch_pairs(path):
    switchpairs = []
    for i in range(1, len(path)-2): # omitting the servers at the start and the end
        switchpairs.append((path[i], path[i+1]))
    return switchpairs

def create_fig(ksp_switch_dict, ecmp8_switch_dict, ecmp64_switch_dict):
    other = ksp_switch_dict.keys()
    ksp = sorted(ksp_switch_dict.values())
    ecmp8 = sorted([ecmp8_switch_dict[one] for one in other])
    ecmp64 = sorted([ecmp64_switch_dict[one] for one in other])
    x = list(range(0, len(other)))

    plt.figure()
    plt.plot(x, ksp, label='8 Shortest Paths')
    plt.plot(x, ecmp8, label='8-Way ECMP')
    plt.plot(x, ecmp64, label='64-Way ECMP')

    plt.title('Figure 9')
    plt.xlabel("Rank of Link")
    plt.ylabel("# Distinct Paths Link is on")
    plt.grid(linestyle='dotted')
    plt.legend(loc='upper left')
    plt.show()



SOURCE = 0
DESTINATION = 1

# Create the pairs for multiple operations
for _ in range(ITERATIONS):
    # make random permutation of server pairs
    server_pairs = []
    all_servers = jf_topo.servers.copy()

    random.shuffle(all_servers)
    for i in range(0, len(all_servers) - 1, 2):
        server_pairs.append([all_servers[i], all_servers[i + 1]])

    # Create paths between source and destination of the server pairs
    # And count all the links that are used by the paths.
    for server_pair in server_pairs:
        ksp = tp.k_shortest_paths(server_pair[SOURCE], server_pair[DESTINATION], 8)
        ecmp64 = tp.n_way_ecmp(server_pair[SOURCE], server_pair[DESTINATION], 64)
        ecmp8 = ecmp64[:8]

        for path in ksp:
            pairs = extract_switch_pairs(path)
            for pair in pairs:
                switch_dict[pair] += 1

        for path in ecmp8:
            pairs = extract_switch_pairs(path)
            for pair in pairs:
                ecmp8_switch_dict[pair] += 1

        for path in ecmp64:
            pairs = extract_switch_pairs(path)
            for pair in pairs:
                ecmp64_switch_dict[pair] += 1

# Dividing all values by the ITERATIONS to create the average.
switch_dict = {k: v / ITERATIONS for k, v in switch_dict.items()}
ecmp8_switch_dict = {k: v / ITERATIONS for k, v in ecmp8_switch_dict.items()}
ecmp64_switch_dict = {k: v / ITERATIONS for k, v in ecmp64_switch_dict.items()}

# Plotting the graph
create_fig(switch_dict, ecmp8_switch_dict, ecmp64_switch_dict)

