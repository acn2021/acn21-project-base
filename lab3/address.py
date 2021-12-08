class Address:
    """Represents an address (e.g. 10.0.1.1/24, or 10.0.1.1) and allows you to 
    conveniently access portions of it.

    Usage:
    addr = Address("10.0.1.1/24")

    addr.raw        = 10.0.1.1/24
    addr.mask       = 24
    addr.octets     = [10, 0, 0, 1]

    # Note mask being an empty string
    addr = Address("10.0.1.1")
    addr.mask       = ""
    """
    def __init__(self, addr_string: str) -> None:
        split = addr_string.split("/")
        # 10.0.1.1/24
        self.raw = addr_string
        # 24
        self.mask = split[1] if len(split) == 2 else ""
        # [10, 0, 1, 1]
        self.octets = split[0].split(".")

    def _get_octets(self, address):
        return 

    def matches(self, other_address, mode: str = "left-handed") -> bool:
        """Check if this address matches with another, based on the mask of the other.
        Ignores mask of self.

        Example:
        ("10.3.1.1").matches("10.3.0.0/16") # True
        ("10.2.1.1").matches("10.3.0.0/16") # False
        ("10.3.1.1").matches("10.3.0.0/24") # False
        ("10.3.1.1").matches("10.3.1.0/24") # True

        Illustrating the argument "mode":
        ("10.5.6.7").matches("10.1.2.3/8") # True
        ("10.5.6.7").matches("10.1.2.3/8", mode="right-handed") # False
        ("10.5.6.3").matches("10.1.2.3/8", mode="right-handed") # True

        Args:
            other_address (Address): the other address to match against
            mode (str): either "left-handed" or "right-handed", meaning
                it will match from left to right or right to left.

        Returns:
            bool: whether there is a match, based on mask of the other
        """
        mask = other_address.mask
        match_oct_1 = other_address.octets[0] == self.octets[0]
        match_oct_2 = other_address.octets[1] == self.octets[1]
        match_oct_3 = other_address.octets[2] == self.octets[2]
        match_oct_4 = other_address.octets[3] == self.octets[3]

        if (mask == "24"):
            if (mode == "left-handed" and match_oct_1 and match_oct_2 and match_oct_3):
                return True
            elif (mode == "right-handed" and match_oct_4 and match_oct_2 and match_oct_3):
                return True
        elif (mask == "16"):
            if (mode == "left-handed" and match_oct_1 and match_oct_2):
                return True
            elif (mode == "right-handed" and match_oct_3 and match_oct_4):
                return True
        elif (mask == "8"):
            if (mode == "left-handed" and match_oct_1):
                return True
            elif (mode == "right-handed" and match_oct_4):
                return True
        else:
            return False

    def __str__(self) -> str:
        return self.raw