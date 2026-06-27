memory = [0] * 4096
reg = [0] * 16
pc = 0x200
i = 0
delay_timer = 0
sound_timer = 0
display = [0] * (64 * 32)
stack = []

memory[0x200] = 0x61
memory[0x201] = 0x05

if __name__ == "__main__":
    opcode = (memory[pc] * 2**8 + memory[pc+1]) # Same as doing (memory[pc] << 8) | memory[pc+1]
    pc += 2

    if (opcode & 0xF000) >> 12 == 6:
        reg[(opcode & 0x0F00) >> 8] = opcode & 0x00FF