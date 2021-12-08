import unittest
from ft_routing import Address

class TestAddress(unittest.TestCase):

    def test_matches(self):
        assert Address("10.3.1.1").matches(Address("10.3.0.0/16")) # True
        assert not Address("10.2.1.1").matches(Address("10.3.0.0/16")) # False
        assert not Address("10.3.1.1").matches(Address("10.3.0.0/24")) # False
        assert Address("10.3.1.1").matches(Address("10.3.1.0/24")) # True

        # Illustrating the argument "mode":
        assert Address("10.5.6.7").matches(Address("10.1.2.3/8")) # True
        assert not Address("10.5.6.7").matches(Address("10.1.2.3/8"), mode="right-handed") # False
        assert Address("10.5.6.3").matches(Address("10.1.2.3/8"), mode="right-handed") # True



if __name__ == '__main__':
    unittest.main()