# CHIP-8 Emulator

A simple CHIP-8 emulator and visualizer built to learn how emulators work at a low level, and to help others see what is happening inside one. I made this project because I loved emulation as a kid, and wanted to better understand systems programming, CPU instructions, memory, registers, timers, graphics, and input. It started with pygame and expanded into a Pyodide-powered site that exposes the emulator's inner state while it runs.

Live site: https://ryanfadaiian.github.io/chip8-visualizer

## Features

- Python CHIP-8 CPU core
- Browser visualizer powered by Pyodide
- 64x32 monochrome display
- 4 KB memory model
- 16 general-purpose registers
- Index register, program counter, stack, delay timer, and sound timer
- Built-in CHIP-8 font data
- ROM loading and custom ROM upload
- Live instruction display showing the opcode currently being executed
- Debug views for registers, memory near the program counter, stack, timers, and instruction trace
- Step controls so users can slow the emulator down and see what is happening under the hood

## Supported Instructions

The emulator implements the main CHIP-8 instruction set, including:

- `00E0` - clear the screen
- `00EE` - return from a subroutine
- `1NNN` - jump to address `NNN`
- `2NNN` - call a subroutine at address `NNN`
- `3XNN`, `4XNN`, `5XY0`, `9XY0` - skip the next instruction based on register comparisons
- `6XNN`, `7XNN` - set or add a value to register `VX`
- `8XY0` to `8XYE` - register math, bitwise operations, and shifts
- `ANNN`, `BNNN` - set the index register or jump with an offset
- `CXNN` - generate a random number and mask it
- `DXYN` - draw a sprite to the display
- `EX9E`, `EXA1` - skip based on keypad input
- `FX07`, `FX15`, `FX18` - read and write delay/sound timers
- `FX0A` - wait for a key press
- `FX1E`, `FX29`, `FX33`, `FX55`, `FX65` - index, font, BCD, memory store, and memory load helpers

## Project Structure

- `src/chip8.py` - emulator core
- `index.html`, `app.js`, `styles.css` - web visualizer
- `roms/` - sample CHIP-8 ROMs
- `tests/` - emulator tests
- `cli/` - pygame-based runner

## Running Tests

```bash
python -m pytest
```
