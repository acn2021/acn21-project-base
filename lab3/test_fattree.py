import unittest
from fat_tree import FattreeNet
import topo

class TestFattree(unittest.TestCase):
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
    def test_determine_link(self):
        ft_topo = topo.Fattree(4)
        net_topo = FattreeNet(ft_topo)

        # TODO check 4 or 3 for concrete value, which is it?
        # Edge switch bottom left
        assert net_topo._determine_ports(
            '10.0.0.1',
            '10.0.2.1'
        ) == ((3 or 4), 1)
        assert net_topo._determine_ports(
            '10.0.0.1',
            '10.0.3.1'
        ) == ((3 or 4), 1)
        # Check reverse
        assert net_topo._determine_ports(
            '10.0.3.1',
            '10.0.0.1'
        ) == (1, (3 or 4))
        # TODO check 4 or 3 for concrete value, which is it?
        # Edge switch bottom right
        assert net_topo._determine_ports(
            '10.0.1.1',
            '10.0.2.1'
        ) == ((3 or 4), 2)
        assert net_topo._determine_ports(
            '10.0.1.1',
            '10.0.3.1'
        ) == ((3 or 4), 2)
        # TODO check 4 or 3 for concrete value, which is it?
        # First core switch to left aggr switch of each pod
        assert net_topo._determine_ports(
            '10.4.1.1',
            '10.0.2.1'
        ) == (1, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.1.1',
            '10.1.2.1'
        ) == (2, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.1.1',
            '10.2.2.1'
        ) == (3, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.1.1',
            '10.3.2.1'
        ) == (4, (4 or 3))
        # Second core switch to left aggr switch of each pod
        assert net_topo._determine_ports(
            '10.4.1.2',
            '10.0.2.1'
        ) == (1, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.1.2',
            '10.1.2.1'
        ) == (2, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.1.2',
            '10.2.2.1'
        ) == (3, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.1.2',
            '10.3.2.1'
        ) == (4, (4 or 3))
        # Third core switch to right aggr switch of each pod
        assert net_topo._determine_ports(
            '10.4.2.1',
            '10.0.3.1'
        ) == (1, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.2.1',
            '10.1.3.1'
        ) == (2, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.2.1',
            '10.2.3.1'
        ) == (3, (4 or 3))
        assert net_topo._determine_ports(
            '10.4.2.1',
            '10.3.3.1'
        ) == (4, (4 or 3))




if __name__ == '__main__':
    unittest.main()