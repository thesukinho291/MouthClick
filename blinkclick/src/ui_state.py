class UIState:
    def __init__(self):
        self.diagnostic_enabled = False
        self.button_regions = {}

    def toggle_diagnostic(self):
        self.diagnostic_enabled = not self.diagnostic_enabled

    def set_button_regions(self, button_regions):
        self.button_regions = button_regions

    def button_at(self, x, y):
        for name, (left, top, right, bottom) in self.button_regions.items():
            if left <= x <= right and top <= y <= bottom:
                return name

        return None
