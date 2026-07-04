from chip8 import Chip8


def create_emulator(rom_bytes):
    return Chip8(rom_bytes=rom_bytes)
