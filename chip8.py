MEMORY_SIZE = 4096
PROGRAM_START = 0x200
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
REGISTER_COUNT = 16


class Chip8():
    def __init__(self, rom_path):
        self.memory = [0] * MEMORY_SIZE
        self.registers = [0] * REGISTER_COUNT
        self.pc = PROGRAM_START
        self.index_register = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT)
        self.stack = []

        self.load_rom(rom_path)

    def cycle(self):
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1] # Same as doing self.memory[self.pc] * 2**8 + self.memory[self.pc+1]
        self.pc += 2

        instruction = opcode >> 12
        x = (opcode >> 8) & 0xF
        y = (opcode >> 4) & 0xF
        n = opcode & 0xF
        nn = opcode & 0xFF
        nnn = opcode & 0xFFF

        #6XNN - Setting register to a value
        if instruction == 0x6:
            self.registers[x] = nn

        #7XNN - Adding
        elif instruction == 7:
            self.registers[x] = (self.registers[x] + nn) & 0xFF #0xFF is to make sure value is never over 255 aka wrap-around

        
        elif instruction == 0x7:
            self.registers[x] = (self.registers[x] + nn) & 0xFF

        #1XXX - Switching to different Memory
        elif instruction == 0x1:
            self.pc = nnn

        #ANNN - Set index to address NNN
        elif instruction == 0xA:
            self.index_register = nnn

        #00E0 - Clear display
        elif opcode == 0x00E0:
            self.display = [0] * (64 * 32)

        #DXYN - Draw Sprite
        elif instruction == 0xD:
            start_x, start_y = self.registers[x], self.registers[y]

            self.registers[15] = 0
            for row in range(n):
                for bit in range(8):
                    if (self.memory[self.index_register + row] >> (7 - bit)) & 1 == 1:
                        screen_x = (start_x + bit) % 64
                        screen_y = (start_y + row) % 32

                        display_index = screen_y * 64 + screen_x
                        if self.display[display_index] == 1:
                            self.display[display_index] = 0
                            self.registers[15] = 1
                        else:
                            self.display[display_index] = 1
                
        # Call a subroutine
        elif instruction == 2:
            self.stack.append(self.pc)
            self.pc = nnn

        # Exit a subroutine
        elif opcode == 0x00EE:
            self.pc = self.stack.pop()

        elif instruction == 3:
            if self.registers[(opcode & 0x0F00) >> 8] == (opcode & 0x00FF):
                self.pc += 2

        elif instruction == 0xF and nn == 0x07:
            self.registers[x] = self.delay_timer

        elif instruction == 0xF and nn == 0x15:
            self.delay_timer = self.registers[x]

        else:
            print(hex(opcode))


    def load_rom(self, rom_path):
        with open(rom_path, 'rb') as data:
            for i, b in enumerate(data.read()):
                self.memory[i + 0x200] = b


    def run_cycles(self, count):
        for _ in range(count):
            self.cycle()