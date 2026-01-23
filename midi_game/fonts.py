import pygame.freetype

# Lista de fontes “boas” e comuns no Linux/Windows
# A primeira que existir no sistema será usada.
FONT_CANDIDATES = [
    "DejaVu Sans",
    "Noto Sans",
    "Liberation Sans",
    "Arial",
]


def get_font(size: int, bold: bool = False):
    """
    Retorna uma fonte robusta (com acentos e símbolos comuns).
    Se nenhuma das fontes candidatas existir, cai no default do sistema.
    """
    size = max(8, int(size))
    for name in FONT_CANDIDATES:
        f = pygame.freetype.SysFont(name, size, bold=bold)
        if f is not None:
            return f
    return pygame.freetype.SysFont(None, size, bold=bold)


def safe_text(text: str) -> str:
    """
    Remove caracteres problemáticos (ex: emoji) e troca por fallback simples.
    Também troca alguns símbolos por ASCII se der ruim no PC de alguém.
    """
    replacements = {
        "🎹": "",  # remove emoji
        "➡️": "->",
        "→": "->",
        "•": "-",
        "♪": "*",  # se não renderizar, vira '*'
        "♫": "*",
        "★": "*",
        "▶": ">",
        "⏎": "ENTER",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)

    # remove qualquer caractere fora do “básico” que pode quebrar fontes
    # (mantém acentos comuns)
    allowed = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        " áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ"
        " .,:;!?()[]{}<>+-_=/'\"\\|@#$%&*"
    )
    return "".join(ch if ch in allowed else "" for ch in text)
