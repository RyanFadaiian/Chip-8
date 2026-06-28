MEMORY_SIZE = 4096
PROGRAM_START = 0x200
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
REGISTER_COUNT = 16


class Chip8:
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

    def draw_sprite(self, x_register, y_register, height):
        pass

    def cycle(self):
        opcode, instruction, x, y, n, nn, nnn = self.fetch_opcode()
        self.execute_opcode(opcode, instruction, x, y, n, nn, nnn)

    def fetch_opcode(self):
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1] # Same as doing self.memory[self.pc] * 2**8 + self.memory[self.pc+1]
        self.pc += 2

        instruction = opcode >> 12
        x = (opcode >> 8) & 0xF
        y = (opcode >> 4) & 0xF
        n = opcode & 0xF
        nn = opcode & 0xFF
        nnn = opcode & 0xFFF

        return opcode, instruction, x, y, n, nn, nnn


    def execute_opcode(self, opcode, instruction, x, y, n, nn, nnn):

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

        #6XNN - Setting register to a value
        elif instruction == 0x6:
            self.registers[x] = nn

        #7XNN - Adding
        elif instruction == 7:
            self.registers[x] = (self.registers[x] + nn) & 0xFF #0xFF is to make sure value is never over 255 aka wrap-around

        #ANNN - Set index to address NNN
        elif instruction == 0xA:
            self.index_register = nnn

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
            
        #FX07 - Save delay_timer to a register
        elif instruction == 0xF and nn == 0x07:
            self.registers[x] = self.delay_timer

        #FX15 - Set delay_timer to a value from register
        elif instruction == 0xF and nn == 0x15:
            self.delay_timer = self.registers[x]

        else:
            print(hex(opcode))


    def load_rom(self, rom_path):
        with open(rom_path, 'rb') as data:
            for i, b in enumerate(data.read()):
                self.memory[i + PROGRAM_START] = b


    def run_cycles(self, count):
        for _ in range(count):
            self.cycle()