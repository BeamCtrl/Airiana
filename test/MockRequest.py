class MockRequest():
    """Mock the request class for unit testing"""
    def __init__(self):
        self.response = ""
        self.data = {}

    def write_register(self, address, value):
        print("Writing to", address, "the value", value)
        self.data[address] = value
        self.response = value
        return True

    def modbusregister(self, address, decimals):
        self.response =  1 * (decimals+1)
        try:
            self.response = self.data[address]
            print("Reading the address", address, "which has", self.response, "and decimals at", decimals)
            return self.data[address]
        except:
            print("No data found using:", self.response)
            return self.response

    def modbusregisters(self, start_address, count, signed):
        return True

    def setup(self, device, mode):
        pass
