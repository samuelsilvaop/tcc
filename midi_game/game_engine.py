import time

from midi_game.midi_loader import load_midi_file


class GameEngine:
    def __init__(self, midi_filename):
        self.events = load_midi_file(midi_filename)
        self.current_index = 0
        self.start_time = None
        self.score = 0
        self.total_notes = 0
        self.hits = []
        self.misses = []

    def start(self):
        self.start_time = time.time()
        self.total_notes = sum(1 for e in self.events if e["type"] == "note_on")

    def get_current_time(self):
        return time.time() - self.start_time

    def get_next_events(self):
        """Retorna os eventos que devem ser processados até agora."""
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
        """Chamada quando o jogador toca uma nota."""
        # Procura se a nota atual esperada bate com a tocada
        for e in self.events:
            if (
                e["type"] == "note_on"
                and abs(self.get_current_time() - e["time"]) < 0.2
                and e["note"] == note
            ):
                if e not in self.hits:
                    self.hits.append(e)
                    self.score += 1
                    return True  # Acertou
        self.misses.append({"note": note, "time": self.get_current_time()})
        return False  # Errou

    def is_finished(self):
        return self.current_index >= len(self.events)
