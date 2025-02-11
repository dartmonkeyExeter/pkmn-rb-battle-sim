import pygame

screen = pygame.display.set_mode((320, 288))
pygame.display.set_caption("Pokémon Red / Blue Battle System")
clock = pygame.time.Clock()
fps = 59.7275 # keep this mf accurate

class Pokemon():
    def __init__(self, name, level, type1, type2=None):
        self.name = name
        self.level = level
        self.type1 = type1
        self.type2 = type2
        
        self.hp_iv = 0
        self.attack_iv = 0
        self.defense_iv = 0
        self.speed_iv = 0
        self.special_iv = 0
        

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((255, 255, 255))
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    
if __name__ == "__main__":
    main()