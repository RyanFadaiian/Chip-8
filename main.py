import pygame
from chip8 import Chip8, DISPLAY_WIDTH, DISPLAY_HEIGHT

SCALE = 10
FPS = 60
CYCLES_PER_FRAME = 10

def main():
    emu = Chip8('br8kout.ch8')

    pygame.init()
    screen = pygame.display.set_mode((DISPLAY_WIDTH * SCALE, DISPLAY_HEIGHT * SCALE))
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # CHIP8 INPUTS: 1-4, Q-R, A-F, Z-V
        inputs = pygame.key.get_pressed()
        emu.set_inputs([inputs[pygame.K_x], inputs[pygame.K_1], inputs[pygame.K_2], inputs[pygame.K_3],
                        inputs[pygame.K_q], inputs[pygame.K_w], inputs[pygame.K_e], inputs[pygame.K_a],
                        inputs[pygame.K_s], inputs[pygame.K_d], inputs[pygame.K_z], inputs[pygame.K_c],
                        inputs[pygame.K_4], inputs[pygame.K_r], inputs[pygame.K_f], inputs[pygame.K_v]])


        # GAME RENDER
        emu.run_cycles(CYCLES_PER_FRAME)

        if emu.delay_timer > 0:
            emu.delay_timer -= 1

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