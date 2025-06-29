import threading
import time

from midi_game.config import set_midi_port
from midi_game.game_engine import GameEngine
from midi_game.midi_input import list_midi_ports, open_midi_port
from midi_game.midi_loader import list_midi_files

# === Escolher porta MIDI ===
ports = list_midi_ports()
print("Portas disponíveis:")
for i, p in enumerate(ports):
    print(f"{i}: {p}")
choice = int(input("Escolha a porta MIDI: "))
set_midi_port(ports[choice])
port = open_midi_port()

# === Escolher música ===
midis = list_midi_files()
print("Músicas disponíveis:")
for i, m in enumerate(midis):
    print(f"{i}: {m}")
music_choice = int(input("Escolha a música: "))
engine = GameEngine(midis[music_choice])
engine.start()


# === Thread para escutar teclado ===
def midi_listener():
    for msg in port:
        if msg.type == "note_on" and msg.velocity > 0:
            result = engine.check_note_input(msg.note)
            print(f"{'✅ Acertou' if result else '❌ Errou'} nota {msg.note}")


listener_thread = threading.Thread(target=midi_listener, daemon=True)
listener_thread.start()

# === Loop do jogo ===
print("🎮 Jogo iniciado!")
while not engine.is_finished():
    events = engine.get_next_events()
    for e in events:
        if e["type"] == "note_on":
            print(f"▶️ Exibir nota {e['note']} em {round(e['time'], 2)}s")
    time.sleep(0.05)

print("\n🏁 Fim da música!")
print(f"🎯 Pontuação final: {engine.score}/{engine.total_notes}")
