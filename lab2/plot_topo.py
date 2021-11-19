import topo
import networkx as nx
import matplotlib.pyplot as plt

num_servers = 16
num_switches = 20
num_ports = 4

ft_topo = topo.Fattree(num_ports)
jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

G = nx.Graph()

total = jf_topo.switches + jf_topo.servers
color_map=[]
for node in jf_topo.switches:
    color_map.append('skyblue')
for node in jf_topo.servers:
    color_map.append('salmon')

G.add_nodes_from(jf_topo.switches)
G.add_nodes_from(jf_topo.servers)
for node in total:
    for edge in node.edges:
        G.add_edge(edge.lnode,edge.rnode)

plt.title("Jellyfish Topology")
nx.draw(G, node_color=color_map)

plt.show()


G = nx.Graph()
print(len(ft_topo.switches))
print(len(ft_topo.servers))

total = ft_topo.switches + ft_topo.servers
color_map=[]
for node in ft_topo.switches:
    color_map.append('skyblue')
for node in ft_topo.servers:
    color_map.append('salmon')

G.add_nodes_from(ft_topo.switches)
G.add_nodes_from(ft_topo.servers)
for node in total:
    for edge in node.edges:
        G.add_edge(edge.lnode,edge.rnode)

plt.title("Fat-tree Topology")
nx.draw(G, node_color=color_map)
plt.show()
