import random

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
        self.keys = [False] * 16

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


    def set_inputs(self, keys_pressed):
        self.keys = keys_pressed


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

        #4XNN - Skip next instruction if register != value nn
        elif instruction == 4:
            if self.registers[x] != nn:
                self.pc += 2

        #5XYN - Skip next instruction if Vx == Vy
        elif instruction == 5:
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
        elif instruction == 8 and n == 7:
            if self.registers[y] >= self.registers[x]:
                self.registers[0xF] = 1
            else:
                self.registers[0xF] = 0

            self.registers[x] = (self.registers[y] - self.registers[x]) & 0xFF

        #8XYE
        elif instruction == 8 and n == 0xE:
            if (self.registers[x] >> 7) & 0b1 == 1:
                self.registers[0xF] = 1
            else:
                self.registers[0xF] = 0

            self.registers[x] = (self.registers[x] << 1) & 0xFF

        #9XY0
        elif instruction == 9:
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

        #FX15 - Set delay_timer to a value from register
        elif instruction == 0xF and nn == 0x15:
            self.delay_timer = self.registers[x]

        else:
            print(hex(opcode))

        #FX18

        #FX1E


        #FX29

        #FX33

        #FX55

        #FX65


    def load_rom(self, rom_path):
        with open(rom_path, 'rb') as data:
            for i, b in enumerate(data.read()):
                self.memory[i + PROGRAM_START] = b


    def run_cycles(self, count):
        for _ in range(count):
            self.cycle()