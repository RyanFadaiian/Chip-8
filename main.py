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

    def read_bytes(self):
        opcode = (self.memory[self.pc] * 2**8 + self.memory[self.pc+1]) # Same as doing (memory[pc] << 8) | memory[pc+1]

        if (opcode & 0xF000) >> 12 == 6:
            self.reg[(opcode & 0x0F00) >> 8] = opcode & 0x00FF

        elif (opcode & 0xF000) >> 12 == 7:
            x = (opcode >> 8) & 0x0F
            self.reg[x] = (self.reg[x] + (opcode & 0xFF)) & 0xFF

        self.pc += 2

    def run(self):
        while self.memory[self.pc] != 0:
            self.read_bytes()
            print(self.reg)
            

if __name__ == "__main__":
    emu = CHIP8()
    emu.memory[0x200] = 0x61
    emu.memory[0x201] = 0x05
    emu.memory[0x202] = 0x71
    emu.memory[0x203] = 0x03

    emu.run()


