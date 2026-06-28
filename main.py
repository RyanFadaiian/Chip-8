import pygame

class CHIP8():
    def __init__(self, rom):
        self.memory = [0] * 4096
        self.reg = [0] * 16
        self.pc = 0x200
        self.i = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [0] * (64 * 32)
        self.stack = []

        self.rom_installer(rom)

    def cycle(self):
        opcode = (self.memory[self.pc] * 2**8 + self.memory[self.pc+1]) # Same as doing (memory[pc] << 8) | memory[pc+1]
        self.pc += 2

        #6XNN - Setting
        if (opcode & 0xF000) >> 12 == 6:
            self.reg[(opcode & 0x0F00) >> 8] = opcode & 0x00FF

        #7XNN - Adding
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
                
        # Call a subroutine
        elif (opcode & 0xF000) >> 12 == 2:
            self.stack.append(self.pc)
            self.pc = opcode & 0x0FFF

        # Exit a subroutine
        elif opcode == 0x00EE:
            self.pc = self.stack.pop()

        elif (opcode & 0xF000) >> 12 == 3:
            if self.reg[(opcode & 0x0F00) >> 8] == (opcode & 0x00FF):
                self.pc += 2

        elif (opcode & 0xF000) >> 12 == 0xF and (opcode & 0x00FF) == 0x07:
            self.reg[(opcode & 0x0F00) >> 8] = self.delay_timer

        elif (opcode & 0xF000) >> 12 == 0xF and (opcode & 0x00FF) == 0x15:
            self.delay_timer = self.reg[(opcode & 0x0F00) >> 8]

        else:
            print(hex(opcode))


    def rom_installer(self, rom):
        with open(rom, 'rb') as data:
            for i, b in enumerate(data.read()):
                self.memory[i + 0x200] = b


    def run_cycles(self, count):
        i = 0
        while i < count:
            self.cycle()
            i += 1
            

if __name__ == "__main__":
    emu = CHIP8('octojam1title.ch8')

    pygame.init()
    screen = pygame.display.set_mode((640, 320))
    clock = pygame.time.Clock()
    running = True

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("purple")

        # RENDER YOUR GAME HERE
        emu.run_cycles(100)

        for x in range(64):
            for y in range(32):
                if emu.display[y * 64 + x] == 1:
                    pygame.draw.rect(screen, (255, 255, 255), (x*10, y*10, 10, 10), 0)

        # flip() the display to put your work on screen
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    pygame.quit()