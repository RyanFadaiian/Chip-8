class CHIP8():
    def __init__(self):
        self.memory = [0] * 4096
        self.reg = [0] * 16
        self.pc = 0x200
        self.i = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [0] * (64 * 32)
        self.stack = []

    def cycle(self):
        opcode = (self.memory[self.pc] * 2**8 + self.memory[self.pc+1]) # Same as doing (memory[pc] << 8) | memory[pc+1]
        self.pc += 2

        #6NXX - Setting
        if (opcode & 0xF000) >> 12 == 6:
            self.reg[(opcode & 0x0F00) >> 8] = opcode & 0x00FF

        #7NXX - Adding
        elif (opcode & 0xF000) >> 12 == 7:
            x = (opcode >> 8) & 0x0F
            self.reg[x] = (self.reg[x] + (opcode & 0xFF)) & 0xFF

        #1XXX - Switching to different Memory
        elif (opcode & 0xF000) >> 12 == 1:
            self.pc = opcode & 0x0FFF

        #ANNN - Set index to address NNN
        elif (opcode & 0xF000) >> 12 == 0xA:
            self.i = opcode & 0x0FFF

        #00E0 - Clear display
        elif opcode == 0x00E0:
            self.display = [0] * (64 * 32)

        #DXYN - Draw Sprite
        elif (opcode & 0xF000) >> 12 == 0xD:
            n = opcode & 0x000F
            y = (opcode >> 4) & 0x00F
            x = (opcode >> 8) & 0x0F

            start_x, start_y = self.reg[x], self.reg[y]

            self.reg[15] = 0
            for row in range(n):
                for bit in range(8):
                    if (self.memory[self.i + row] >> (7 - bit)) & 1 == 1:
                        screen_x = (start_x + bit) % 64
                        screen_y = (start_y + row) % 32

                        display_index = screen_y * 64 + screen_x
                        if self.display[display_index] == 1:
                            self.display[display_index] = 0
                            self.reg[15] = 1
                        else:
                            self.display[display_index] = 1
                
                    


    def run(self):
        while self.memory[self.pc] != 0:
            self.cycle()
            #print(self.reg)
            

if __name__ == "__main__":
    emu = CHIP8()

    # Set I = 0x300
    emu.memory[0x200] = 0xA3
    emu.memory[0x201] = 0x00

    # Set V1 = 10
    emu.memory[0x202] = 0x61
    emu.memory[0x203] = 0x0A

    # Set V2 = 6
    emu.memory[0x204] = 0x62
    emu.memory[0x205] = 0x06

    # Draw a 3-row sprite at (V1, V2)
    emu.memory[0x206] = 0xD1
    emu.memory[0x207] = 0x23

    # Draw the same sprite again
    emu.memory[0x208] = 0xD1
    emu.memory[0x209] = 0x23

    # Sprite data
    emu.memory[0x300] = 0b11110000
    emu.memory[0x301] = 0b10010000
    emu.memory[0x302] = 0b11110000

    emu.run()
    print(sum(emu.display))
    print(emu.reg[15])

