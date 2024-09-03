import os
class i40NCAssistant:
    def __init__(self, i40nc, i40ncconfig):
        self.config = i40ncconfig
        self.db = i40nc