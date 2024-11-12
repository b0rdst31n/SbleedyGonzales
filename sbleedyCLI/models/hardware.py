
class Hardware():
    def __init__(self, details):
        self.name = details["name"]
        self.description = details["description"]
        self.needs_setup_verification = details["needs_setup_verification"]
        self.port = ""
        self.firmware = details["firmware"]




