class Pilot:
    def __init__(self, name, lap=0, holeshot=None, finished=False):
        self.name = name
        self.lap = lap
        self.laps = []
        self.holeshot = holeshot
        self.finished = finished

    def add_lap(self, lap_time):
        self.laps.append(lap_time)
        self.lap += 1