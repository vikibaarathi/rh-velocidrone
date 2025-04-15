class Pilot:
    def __init__(self, uid, name, lap=0, finished=False, last_crossing_time=0.0):
        self.uid = uid
        self.name = name
        self.lap = lap
        self.finished = finished
        self.laps = []
        self.last_crossing_time = last_crossing_time

    def add_time_of_gate(self, time):
        self.laps.append(time)
        self.lap = self.lap + 1

    def mark_finished(self):
        self.finished = True
        if self.lap == 1:
            self.lap = 2