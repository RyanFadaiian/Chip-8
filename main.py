import pygame
from chip8 import Chip8, DISPLAY_WIDTH, DISPLAY_HEIGHT

SCALE = 10
FPS = 60
CYCLES_PER_FRAME = 10

def main():
    emu = Chip8('1-chip8-logo.ch8')

    pygame.init()
    screen = pygame.display.set_mode((DISPLAY_WIDTH * SCALE, DISPLAY_HEIGHT * SCALE))
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # RENDER YOUR GAME HERE
        emu.run_cycles(CYCLES_PER_FRAME)

        screen.fill("purple")

        for y in range(DISPLAY_HEIGHT):
            for x in range(DISPLAY_WIDTH):
                if emu.display[y * DISPLAY_WIDTH + x]:
                    pygame.draw.rect(
                        screen,
                        "white",
                        (x * SCALE, y * SCALE, SCALE, SCALE),
                    )

        pygame.display.flip() # Displays own work on screen
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()