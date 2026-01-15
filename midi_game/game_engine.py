# midi_game/game_engine.py
import time

from midi_game.midi_loader import build_note_spans, load_midi_file


class GameEngine:
    def __init__(self, midi_filename):
        self.events = load_midi_file(midi_filename)
        self.note_spans = build_note_spans(self.events)
        self.current_index = 0
        self.start_time = None
        self.score = 0
        self.total_notes = 0
        self.hits = []
        self.misses = []

    def start(self, start_time: float | None = None):
        """
        Se start_time for None: começa agora.
        Se start_time for um float: começa nesse timestamp absoluto (time.time()).
        """
        self.start_time = start_time if start_time is not None else time.time()
        self.total_notes = sum(1 for e in self.events if e["type"] == "note_on")

    def get_current_time(self):
        return time.time() - self.start_time

    def get_next_events(self):
        now = self.get_current_time()
        events = []
        while (
            self.current_index < len(self.events)
            and self.events[self.current_index]["time"] <= now
        ):
            events.append(self.events[self.current_index])
            self.current_index += 1
        return events

    def check_note_input(self, note):
        for e in self.events:
            if (
                e["type"] == "note_on"
                and abs(self.get_current_time() - e["time"]) < 0.2
                and e["note"] == note
            ):
                if e not in self.hits:
                    self.hits.append(e)
                    self.score += 1
                    return True
        self.misses.append({"note": note, "time": self.get_current_time()})
        return False

    def is_finished(self):
        return self.current_index >= len(self.events)

    def get_visible_spans(self, current_time, window_ahead=8.0, window_behind=1.0):
        start_min = current_time - window_behind
        start_max = current_time + window_ahead
        visible = []
        for s in self.note_spans:
            if s["end"] >= start_min and s["start"] <= start_max:
                visible.append(s)
        return visible
