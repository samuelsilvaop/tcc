from midi_game.config import set_midi_port
from midi_game.midi_input import list_midi_ports, open_midi_port

ports = list_midi_ports()
print("Portas MIDI disponíveis:")
for i, p in enumerate(ports):
    print(f"{i}: {p}")

selected = int(input("Selecione o número da porta: "))
set_midi_port(ports[selected])

with open_midi_port() as port:
    print("Aguardando notas...")
    for msg in port:
        print(msg)
