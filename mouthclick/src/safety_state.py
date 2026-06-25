class SafetyState:
    def __init__(self):
        self.armed = False

    def toggle_armed(self):
        self.armed = not self.armed

    def arm(self):
        self.armed = True

    def disarm(self):
        self.armed = False

    @property
    def status_text(self):
        return "armado" if self.armed else "desarmado"
