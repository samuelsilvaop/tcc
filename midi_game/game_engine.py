# midi_game/game_engine.py
import time

from midi_game.midi_loader import load_midi_file, load_midi_note_spans


class GameEngine:
    def __init__(self, midi_filename: str):
        self.midi_filename = midi_filename

        # eventos e spans
        self.events = load_midi_file(midi_filename)
        self.note_spans = load_midi_note_spans(midi_filename)

        self.current_index = 0
        self.start_time = None

    def start(self, start_time: float | None = None):
        """
        Se start_time for None: começa agora.
        Se start_time for um float: começa nesse timestamp absoluto (time.time()).
        """
        self.start_time = start_time if start_time is not None else time.time()

    def get_current_time(self) -> float:
        return time.time() - float(self.start_time)

    def is_finished(self) -> bool:
        return self.current_index >= len(self.events)

    def get_visible_spans(
        self, current_time: float, window_ahead=8.0, window_behind=1.0
    ):
        start_min = current_time - window_behind
        start_max = current_time + window_ahead
        return [
            s
            for s in self.note_spans
            if s["end"] >= start_min and s["start"] <= start_max
        ]

    def get_max_score(self, max_per_note: int = 100) -> int:
        """Pontuação máxima teórica: 100 por span."""
        return max(1, len(self.note_spans) * int(max_per_note))
