import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.chip8 import (
    CHIP8_FONT,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    MEMORY_SIZE,
    PROGRAM_START,
    Chip8,
    decode_instruction,
    decode_opcode,
)


def run_opcode(chip8, opcode):
    chip8.execute_instruction(decode_instruction(opcode))


def test_initial_state_loads_font_and_rom_bytes():
    chip8 = Chip8(rom_bytes=[0x60, 0x2A, 0x61, 0x03])

    assert chip8.pc == PROGRAM_START
    assert chip8.memory[:0x50] == [0] * 0x50
    assert chip8.memory[0x50:0x50 + len(CHIP8_FONT)] == CHIP8_FONT
    assert chip8.memory[PROGRAM_START:PROGRAM_START + 4] == [0x60, 0x2A, 0x61, 0x03]
    assert chip8.registers == [0] * 16
    assert chip8.display == [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT)


@pytest.mark.parametrize(
    ("opcode", "expected"),
    [
        # 00E0
        (0x00E0, "CLS"),
        # 00EE
        (0x00EE, "RET"),
        # 1NNN
        (0x1234, "JP 0234"),
        # 6XNN
        (0x6A7F, "LD VA, 7F"),
        # 8XY4
        (0x8AB4, "ADD VA, VB"),
        # DXYN
        (0xD125, "DRW V1, V2, 5"),
        # FX33
        (0xF133, "LD B, V1"),
    ],
)
def test_decode_opcode_text(opcode, expected):
    assert decode_opcode(opcode) == expected


def test_cycle_fetches_executes_and_records_trace():
    chip8 = Chip8(rom_bytes=[0x60, 0x2A, 0x70, 0x01])

    # 6XNN
    first_opcode = chip8.cycle()
    # 7XNN
    second_opcode = chip8.cycle()

    assert first_opcode == 0x602A
    assert second_opcode == 0x7001
    assert chip8.registers[0] == 0x2B
    assert chip8.pc == PROGRAM_START + 4
    assert chip8.trace == [
        {"pc": "0200", "opcode": "602A", "decoded": "LD V0, 2A"},
        {"pc": "0202", "opcode": "7001", "decoded": "ADD V0, 01"},
    ]


def test_jump_call_and_return_update_pc_and_stack():
    chip8 = Chip8()
    chip8.pc = PROGRAM_START + 2

    # 2NNN
    run_opcode(chip8, 0x2300)
    assert chip8.pc == 0x300
    assert chip8.stack == [PROGRAM_START + 2]

    # 00EE
    run_opcode(chip8, 0x00EE)
    assert chip8.pc == PROGRAM_START + 2
    assert chip8.stack == []

    # 1NNN
    run_opcode(chip8, 0x1456)
    assert chip8.pc == 0x456


def test_skip_instructions_advance_pc_when_conditions_match():
    chip8 = Chip8()
    chip8.pc = PROGRAM_START
    chip8.registers[1] = 0x12
    chip8.registers[2] = 0x34
    chip8.registers[3] = 0x12

    # 3XNN
    run_opcode(chip8, 0x3112)
    assert chip8.pc == PROGRAM_START + 2

    # 4XNN
    run_opcode(chip8, 0x4212)
    assert chip8.pc == PROGRAM_START + 4

    # 5XY0
    run_opcode(chip8, 0x5130)
    assert chip8.pc == PROGRAM_START + 6

    # 9XY0
    run_opcode(chip8, 0x9120)
    assert chip8.pc == PROGRAM_START + 8


def test_arithmetic_and_bitwise_operations_set_registers_and_flags():
    chip8 = Chip8()

    # 6XNN
    run_opcode(chip8, 0x61FE)
    # 7XNN
    run_opcode(chip8, 0x7105)
    assert chip8.registers[1] == 0x03

    chip8.registers[1] = 200
    chip8.registers[2] = 100
    # 8XY4
    run_opcode(chip8, 0x8124)
    assert chip8.registers[1] == 44
    assert chip8.registers[0xF] == 1

    chip8.registers[1] = 50
    chip8.registers[2] = 100
    # 8XY5
    run_opcode(chip8, 0x8125)
    assert chip8.registers[1] == 206
    assert chip8.registers[0xF] == 0

    chip8.registers[1] = 0b1010
    chip8.registers[2] = 0b1100
    # 8XY1
    run_opcode(chip8, 0x8121)
    assert chip8.registers[1] == 0b1110

    # 8XY2
    run_opcode(chip8, 0x8122)
    assert chip8.registers[1] == 0b1100

    # 8XY3
    run_opcode(chip8, 0x8123)
    assert chip8.registers[1] == 0


def test_shift_operations_store_shifted_bit_in_vf():
    chip8 = Chip8()

    chip8.registers[1] = 0b0000_0011
    # 8XY6
    run_opcode(chip8, 0x8106)
    assert chip8.registers[1] == 0b0000_0001
    assert chip8.registers[0xF] == 1

    chip8.registers[1] = 0b1000_0001
    # 8XYE
    run_opcode(chip8, 0x810E)
    assert chip8.registers[1] == 0b0000_0010
    assert chip8.registers[0xF] == 1


def test_memory_index_bcd_store_and_load_registers():
    chip8 = Chip8()
    # ANNN
    run_opcode(chip8, 0xA300)
    assert chip8.index_register == 0x300

    chip8.registers[2] = 197
    # FX33
    run_opcode(chip8, 0xF233)
    assert chip8.memory[0x300:0x303] == [1, 9, 7]

    chip8.registers[0:4] = [1, 2, 3, 4]
    # FX55
    run_opcode(chip8, 0xF355)
    assert chip8.memory[0x300:0x304] == [1, 2, 3, 4]

    chip8.registers[0:4] = [0, 0, 0, 0]
    # FX65
    run_opcode(chip8, 0xF365)
    assert chip8.registers[0:4] == [1, 2, 3, 4]


def test_draw_sprite_toggles_pixels_wraps_and_sets_collision_flag():
    chip8 = Chip8()
    chip8.index_register = 0x300
    chip8.memory[0x300] = 0b1100_0000
    chip8.registers[0] = DISPLAY_WIDTH - 1
    chip8.registers[1] = DISPLAY_HEIGHT - 1

    # DXYN
    run_opcode(chip8, 0xD011)
    bottom_right = (DISPLAY_HEIGHT - 1) * DISPLAY_WIDTH + (DISPLAY_WIDTH - 1)
    bottom_left = (DISPLAY_HEIGHT - 1) * DISPLAY_WIDTH
    assert chip8.display[bottom_right] == 1
    assert chip8.display[bottom_left] == 1
    assert chip8.registers[0xF] == 0

    # DXYN
    run_opcode(chip8, 0xD011)
    assert chip8.display[bottom_right] == 0
    assert chip8.display[bottom_left] == 0
    assert chip8.registers[0xF] == 1


def test_key_skip_and_wait_for_key_behavior():
    chip8 = Chip8()
    chip8.pc = PROGRAM_START + 2
    chip8.registers[1] = 0xA
    chip8.keys[0xA] = True

    # EX9E
    run_opcode(chip8, 0xE19E)
    assert chip8.pc == PROGRAM_START + 4

    chip8.keys[0xA] = False
    # EXA1
    run_opcode(chip8, 0xE1A1)
    assert chip8.pc == PROGRAM_START + 6

    # FX0A
    run_opcode(chip8, 0xF20A)
    assert chip8.pc == PROGRAM_START + 4

    chip8.keys[0x5] = True
    # FX0A
    run_opcode(chip8, 0xF20A)
    assert chip8.registers[2] == 0x5
    assert chip8.pc == PROGRAM_START + 4


def test_timers_and_snapshot_format_values():
    chip8 = Chip8(rom_bytes=[0xA3, 0x00])
    chip8.registers[1] = 7
    # FX15
    run_opcode(chip8, 0xF115)
    # FX18
    run_opcode(chip8, 0xF118)

    chip8.tick_timers()
    assert chip8.delay_timer == 6
    assert chip8.sound_timer == 6

    # ANNN
    chip8.cycle()
    snapshot = chip8.snapshot()
    assert snapshot["pc"] == "0202"
    assert snapshot["index"] == "0300"
    assert snapshot["registers"][1] == "07"
    assert snapshot["memoryWindow"][0]["opcode"] == "A300"


def test_rom_bytes_do_not_write_past_memory_end():
    chip8 = Chip8()

    chip8.load_rom_bytes([0xAB] * MEMORY_SIZE)

    assert chip8.memory[PROGRAM_START] == 0xAB
    assert chip8.memory[-1] == 0xAB
    assert len(chip8.memory) == MEMORY_SIZE
