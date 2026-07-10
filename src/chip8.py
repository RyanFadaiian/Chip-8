from dataclasses import dataclass
import random

MEMORY_SIZE = 4096
PROGRAM_START = 0x200
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
REGISTER_COUNT = 16

CHIP8_FONT = [
    0b11110000, 0b10010000, 0b10010000, 0b10010000, 0b11110000,
    0b00100000, 0b01100000, 0b00100000, 0b00100000, 0b01110000,
    0b11110000, 0b00010000, 0b11110000, 0b10000000, 0b11110000,
    0b11110000, 0b00010000, 0b11110000, 0b00010000, 0b11110000,
    0b10010000, 0b10010000, 0b11110000, 0b00010000, 0b00010000,
    0b11110000, 0b10000000, 0b11110000, 0b00010000, 0b11110000,
    0b11110000, 0b10000000, 0b11110000, 0b10010000, 0b11110000,
    0b11110000, 0b00010000, 0b00100000, 0b01000000, 0b01000000,
    0b11110000, 0b10010000, 0b11110000, 0b10010000, 0b11110000,
    0b11110000, 0b10010000, 0b11110000, 0b00010000, 0b11110000,
    0b11110000, 0b10010000, 0b11110000, 0b10010000, 0b10010000,
    0b11100000, 0b10010000, 0b11100000, 0b10010000, 0b11100000,
    0b11110000, 0b10000000, 0b10000000, 0b10000000, 0b11110000,
    0b11100000, 0b10010000, 0b10010000, 0b10010000, 0b11100000,
    0b11110000, 0b10000000, 0b11110000, 0b10000000, 0b11110000,
    0b11110000, 0b10000000, 0b11110000, 0b10000000, 0b10000000,
]


@dataclass
class DecodedInstruction:
    opcode: int
    instruction: int
    x: int
    y: int
    n: int
    nn: int
    nnn: int
    text: str


def hex4(value):
    return f"{value & 0xFFFF:04X}"


def hex2(value):
    return f"{value & 0xFF:02X}"


def instruction_text(opcode, instruction, x, y, n, nn, nnn):
    if opcode == 0x00E0:
        return "CLS"
    if opcode == 0x00EE:
        return "RET"
    if instruction == 0x1:
        return f"JP {hex4(nnn)}"
    if instruction == 0x2:
        return f"CALL {hex4(nnn)}"
    if instruction == 0x3:
        return f"SE V{x:X}, {hex2(nn)}"
    if instruction == 0x4:
        return f"SNE V{x:X}, {hex2(nn)}"
    if instruction == 0x5 and n == 0:
        return f"SE V{x:X}, V{y:X}"
    if instruction == 0x6:
        return f"LD V{x:X}, {hex2(nn)}"
    if instruction == 0x7:
        return f"ADD V{x:X}, {hex2(nn)}"
    if instruction == 0x8:
        names = {
            0x0: "LD",
            0x1: "OR",
            0x2: "AND",
            0x3: "XOR",
            0x4: "ADD",
            0x5: "SUB",
            0x6: "SHR",
            0x7: "SUBN",
            0xE: "SHL",
        }
        return f"{names.get(n, '8XY?')} V{x:X}, V{y:X}"
    if instruction == 0x9 and n == 0:
        return f"SNE V{x:X}, V{y:X}"
    if instruction == 0xA:
        return f"LD I, {hex4(nnn)}"
    if instruction == 0xB:
        return f"JP V0, {hex4(nnn)}"
    if instruction == 0xC:
        return f"RND V{x:X}, {hex2(nn)}"
    if instruction == 0xD:
        return f"DRW V{x:X}, V{y:X}, {n:X}"
    if instruction == 0xE and nn == 0x9E:
        return f"SKP V{x:X}"
    if instruction == 0xE and nn == 0xA1:
        return f"SKNP V{x:X}"
    if instruction == 0xF:
        names = {
            0x07: "LD Vx, DT",
            0x0A: "LD Vx, K",
            0x15: "LD DT, Vx",
            0x18: "LD ST, Vx",
            0x1E: "ADD I, Vx",
            0x29: "LD F, Vx",
            0x33: "LD B, Vx",
            0x55: "LD [I], Vx",
            0x65: "LD Vx, [I]",
        }
        return names.get(nn, "FX??").replace("Vx", f"V{x:X}")
    return f"Unknown {hex4(opcode)}"


def decode_instruction(opcode):
    instruction = opcode >> 12
    x = (opcode >> 8) & 0xF
    y = (opcode >> 4) & 0xF
    n = opcode & 0xF
    nn = opcode & 0xFF
    nnn = opcode & 0xFFF

    return DecodedInstruction(
        opcode=opcode,
        instruction=instruction,
        x=x,
        y=y,
        n=n,
        nn=nn,
        nnn=nnn,
        text=instruction_text(opcode, instruction, x, y, n, nn, nnn),
    )


def decode_opcode(opcode):
    return decode_instruction(opcode).text


class Chip8:
    def __init__(self, rom_path=None, rom_bytes=None):
        self.rom_path = rom_path
        self.rom_bytes = list(rom_bytes) if rom_bytes is not None else None
        self.reset()

    def reset(self):
        self.memory = [0] * MEMORY_SIZE
        self.registers = [0] * REGISTER_COUNT
        self.pc = PROGRAM_START
        self.index_register = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT)
        self.stack = []
        self.keys = [False] * 16
        self.last_opcode = 0
        self.last_pc = PROGRAM_START
        self.last_decoded = "Ready"
        self.trace = []

        self.initiate_font()
        if self.rom_bytes is not None:
            self.load_rom_bytes(self.rom_bytes)
        elif self.rom_path is not None:
            self.load_rom(self.rom_path)

    def initiate_font(self):
        for i, font_byte in enumerate(CHIP8_FONT):
            self.memory[0x50 + i] = font_byte

    def cycle(self):
        decoded = self.fetch_opcode()
        self.last_opcode = decoded.opcode
        self.last_decoded = decoded.text
        self.execute_instruction(decoded)
        self.trace.append({
            "pc": hex4(self.last_pc),
            "opcode": hex4(decoded.opcode),
            "decoded": decoded.text,
        })
        self.trace = self.trace[-32:]
        return decoded.opcode

    def fetch_opcode(self):
        self.last_pc = self.pc
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1] # Same as doing self.memory[self.pc] * 2**8 + self.memory[self.pc+1]
        self.pc += 2
        return decode_instruction(opcode)


    def set_inputs(self, keys_pressed):
        self.keys = [bool(key) for key in keys_pressed]


    def tick_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1

        if self.sound_timer > 0:
            self.sound_timer -= 1


    def execute_instruction(self, decoded):
        opcode = decoded.opcode
        instruction = decoded.instruction
        x = decoded.x
        y = decoded.y
        n = decoded.n
        nn = decoded.nn
        nnn = decoded.nnn

        #00E0 - Clear display
        if opcode == 0x00E0:
            self.display = [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT)

        #00EE - Exit a subroutine
        elif opcode == 0x00EE:
            self.pc = self.stack.pop()

        #1NNN - Switching to different Memory
        elif instruction == 0x1:
            self.pc = nnn

        #2NNN - Call a subroutine
        elif instruction == 2:
            self.stack.append(self.pc)
            self.pc = nnn

        #3XNN - Skip next instruction if register has value nn
        elif instruction == 3:
            if self.registers[x] == nn:
                self.pc += 2

        #4XNN - Skip next instruction if register != value nn
        elif instruction == 4:
            if self.registers[x] != nn:
                self.pc += 2

        #5XY0 - Skip next instruction if Vx == Vy
        elif instruction == 5 and n == 0:
            if self.registers[x] == self.registers[y]:
                self.pc += 2

        #6XNN - Setting register to a value
        elif instruction == 0x6:
            self.registers[x] = nn

        #7XNN - Adding
        elif instruction == 7:
            self.registers[x] = (self.registers[x] + nn) & 0xFF #0xFF is to make sure value is never over 255 aka wrap-around

        #8XY0 - Set Vx = Vy
        elif instruction == 8 and n == 0:
            self.registers[x] = self.registers[y]

        #8XY1 - Set Vx = Vx (bitwise OR) Vy
        elif instruction == 8 and n == 1:
            self.registers[x] = self.registers[x] | self.registers[y]

        #8XY2 - Set Vx = Vx (bitwise AND) Vy
        elif instruction == 8 and n == 2:
            self.registers[x] = self.registers[x] & self.registers[y]

        #8XY3 - Set Vx = Vx (bitwise XOR) Vy
        elif instruction == 8 and n == 3:
            self.registers[x] = self.registers[x] ^ self.registers[y]

        #8XY4 -
        elif instruction == 8 and n == 4:
            self.registers[x] += self.registers[y]

            if self.registers[x] > 255:
                self.registers[0xF] = 1
                self.registers[x] = self.registers[x] & 0xFF
            else:
                self.registers[0xF] = 0


        #8XY5
        elif instruction == 8 and n == 5:
            if self.registers[y] <= self.registers[x]:
                self.registers[0xF] = 1
            else:
                self.registers[0xF] = 0

            self.registers[x] = (self.registers[x] - self.registers[y]) & 0xFF

        #8XY6 - Divide Vx by 2
        elif instruction == 8 and n == 6:
            if self.registers[x] & 0b1 == 1:
                self.registers[0xF] = 1
            else:
                self.registers[0xF] = 0

            self.registers[x] = self.registers[x] >> 1


        #8XY7 - 
        elif instruction == 0x8 and n == 0x7:
            vx = self.registers[x]
            vy = self.registers[y]

            result = (vy - vx) & 0xFF
            no_borrow = 1 if vy >= vx else 0

            self.registers[x] = result
            self.registers[0xF] = no_borrow

        #8XYE
        elif instruction == 8 and n == 0xE:
            if (self.registers[x] >> 7) & 0b1 == 1:
                self.registers[0xF] = 1
            else:
                self.registers[0xF] = 0

            self.registers[x] = (self.registers[x] << 1) & 0xFF

        #9XY0
        elif instruction == 9 and n == 0:
            if self.registers[x] != self.registers[y]:
                self.pc += 2

        #ANNN - Set index to address NNN
        elif instruction == 0xA:
            self.index_register = nnn

        #BNNN
        elif instruction == 0xB:
            self.pc = (self.registers[0] + nnn)

        #CXKK
        elif instruction == 0xC:
            self.registers[x] = random.randint(0, 255) & nn

        #DXYN - Draw Sprite
        elif instruction == 0xD:
            start_x, start_y = self.registers[x], self.registers[y]

            self.registers[-1] = 0
            for row in range(n):
                for bit in range(8):
                    if (self.memory[self.index_register + row] >> (7 - bit)) & 1 == 1:  # Confusing Line
                        screen_x = (start_x + bit) % DISPLAY_WIDTH
                        screen_y = (start_y + row) % DISPLAY_HEIGHT

                        display_index = screen_y * DISPLAY_WIDTH + screen_x
                        if self.display[display_index] == 1:
                            self.display[display_index] = 0
                            self.registers[15] = 1
                        else:
                            self.display[display_index] = 1
            
        #EX9E
        elif instruction == 0xE and nn == 0x9E:
            if self.keys[self.registers[x]] == True:
                self.pc += 2

        #EXA1
        elif instruction == 0xE and nn == 0xA1:
            if self.keys[self.registers[x]] == False:
                self.pc += 2
            
        #FX07 - Save delay_timer to a register
        elif instruction == 0xF and nn == 0x07:
            self.registers[x] = self.delay_timer

        #FX0A
        elif instruction == 0xF and nn == 0x0A:
            key_found = False

            for i in range(len(self.keys)):
                if self.keys[i]:
                    self.registers[x] = i
                    key_found = True
                    break

            if not key_found:
                self.pc -= 2

        #FX15 - Set delay_timer to a value from register
        elif instruction == 0xF and nn == 0x15:
            self.delay_timer = self.registers[x]

        #FX18
        elif instruction == 0xF and nn == 0x18:
            self.sound_timer = self.registers[x]

        #FX1E
        elif instruction == 0xF and nn == 0x1E:
            self.index_register += self.registers[x]

        #FX29
        elif instruction == 0xF and nn == 0x29:
            self.index_register = 0x50 + (self.registers[x] * 5)

        #FX33
        elif instruction == 0xF and nn == 0x33:
            value = self.registers[x]

            self.memory[self.index_register] = value // 100
            self.memory[self.index_register + 1] = (value // 10) % 10
            self.memory[self.index_register + 2] = value % 10


        #FX55
        elif instruction == 0xF and nn == 0x55:
            for val, reg in enumerate(self.registers[0:x+1]):
                self.memory[self.index_register + val] = reg

        #FX65
        elif instruction == 0xF and nn == 0x65:
            for i in range(x + 1):
                self.registers[i] = self.memory[self.index_register + i]

        else:
            print(hex(opcode))

    def load_rom(self, rom_path):
        with open(rom_path, 'rb') as data:
            self.load_rom_bytes(data.read())


    def load_rom_bytes(self, rom_bytes):
        for i, b in enumerate(rom_bytes):
            target = i + PROGRAM_START
            if target < MEMORY_SIZE:
                self.memory[target] = int(b) & 0xFF


    def run_cycles(self, count):
        for _ in range(count):
            self.cycle()


    def run_until_draw(self, max_cycles=2000):
        cycles = 0
        while cycles < max_cycles:
            opcode = self.cycle()
            cycles += 1
            if opcode >> 12 == 0xD:
                break

        return cycles


    def snapshot(self):
        start = max(PROGRAM_START, self.pc - 8)
        memory_window = []
        for address in range(start, min(start + 16, MEMORY_SIZE - 1), 2):
            opcode = (self.memory[address] << 8) | self.memory[address + 1]
            memory_window.append({
                "address": hex4(address),
                "opcode": hex4(opcode),
                "decoded": decode_opcode(opcode),
                "current": address == self.pc,
            })

        return {
            "pc": hex4(self.pc),
            "lastPc": hex4(self.last_pc),
            "index": hex4(self.index_register),
            "lastOpcode": hex4(self.last_opcode),
            "lastDecoded": self.last_decoded,
            "registers": [hex2(value) for value in self.registers],
            "delayTimer": self.delay_timer,
            "soundTimer": self.sound_timer,
            "stack": [hex4(value) for value in self.stack],
            "display": self.display,
            "memoryWindow": memory_window,
            "trace": self.trace,
        }
