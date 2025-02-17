import pygame, sqlite3, math
from moves import *

scale = 4
screen = pygame.display.set_mode((160 * scale, 144 * scale))
pygame.display.set_caption("Pokémon Red / Blue Battle System")
clock = pygame.time.Clock()
fps = 59.7275 # keep this mf accurate

class Pokemon():
    def __init__(self, dex_num, species, nickname, level, xp, type1, type2, hp, atk, defense, spec, speed, atk_iv, def_iv, speed_iv, spec_iv, moves, player_owned=False):
        self.dex_num = dex_num
        self.species = species
        self.nickname = nickname
        self.level = level
        self.xp = xp
        self.types = (type1, type2)
        self.moves = moves
        
        self.base_hp = hp
        self.base_atk = atk
        self.base_defense = defense
        self.base_spatk = spec
        self.base_spdef = spec
        self.base_speed = speed
        
        self.atk_iv = atk_iv
        self.def_iv = def_iv
        self.speed_iv = speed_iv
        self.spec_iv = spec_iv
        self.hp_iv = ((self.atk_iv % 2) * 8) + ((self.def_iv % 2) * 4) + ((speed_iv % 2) * 2) + ((self.spec_iv % 2) * 1)

        self.hp_ev = 0
        self.atk_ev = 0
        self.def_ev = 0
        self.speed_ev = 0
        self.spec_ev = 0

        self.max_hp = self.calc_stat(self.base_hp, self.hp_iv, self.hp_ev, self.level, True)
        self.curr_hp = self.max_hp

        self.atk = self.calc_stat(self.base_atk, self.atk_iv, self.atk_ev, self.level)
        self.defense = self.calc_stat(self.base_defense, self.def_iv, self.def_ev, self.level)
        self.spatk = self.calc_stat(self.base_spatk, self.spec_iv, self.spec_ev, self.level)
        self.spdef = self.calc_stat(self.base_spdef, self.spec_iv, self.spec_ev, self.level)
        self.speed = self.calc_stat(self.base_speed, self.speed_iv, self.speed_ev, self.level)
        
        self.atk_stage = 0
        self.defense_stage = 0
        self.spatk_stage = 0
        self.spdef_stage = 0
        self.speed_stage = 0
        self.accuracy_stage = 0
        self.evasion_stage = 0

        self.status = None
        self.vol_status = [] # volatile status effects
        
        self.crit_boost = False

        self.reflect = False
        self.light_screen = False
        self.collected_dmg = 0 # used for moves like counter and bide and mirror coat n stuff
        self.turn_count = 0 # used for moves like bide and rollout n stuff
        self.dot_turns = 0 # used for moves like toxic and leech seed
        self.invincible = False # used for moves like fly and dig

        self.player_owned = player_owned
        self.battle_pos = (0, 0)
        if self.player_owned:
            self.sprite = pygame.image.load(f"assets/pokemon/back/{self.dex_num}.png")
            self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * 2, self.sprite.get_height() * 2))
        else:
            self.sprite = pygame.image.load(f"assets/pokemon/front/{self.dex_num}.png")
        self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * scale, self.sprite.get_height() * scale))

    def calc_stat(self, base, iv, ev, level, hp=False):
        if hp:
            return math.floor(((2 * base + iv + (ev // 4)) * level) / 100 + level + 10)
        return math.floor((((2 * base + iv + (ev // 4)) * level) / 100) + 5)
        
    def battlesprite_draw(self):
        global scale
        if self.player_owned:
            screen.blit(self.sprite, self.battle_pos) # should start off screen on right side
        else:
            screen.blit(self.sprite, self.battle_pos) # should start off screen on left side

    def update(self):
        self.battlesprite_draw()
        
# ok im gonna test the moves now, i only made absorb so far

# get the pokemon from the database
conn = sqlite3.connect("FirstGenPokemon.db")
c = conn.cursor()
c.execute("SELECT * FROM pokemon WHERE Name = 'Charmander'")
charmander_data = c.fetchone()
c.execute("SELECT * FROM pokemon WHERE Name = 'Squirtle'")
squirtle_data = c.fetchone()
conn.close()

# create the pokemon objects
# hp starts at index 12

charmander = Pokemon(charmander_data[0], charmander_data[1], "Charmander", 5, 0, charmander_data[2], charmander_data[3], charmander_data[12], charmander_data[13], charmander_data[14], charmander_data[15], charmander_data[16], random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), [Growl(), Scratch()], True)
squirtle = Pokemon(squirtle_data[0], squirtle_data[1], "Squirtle", 5, 0, squirtle_data[2], squirtle_data[3], squirtle_data[12], squirtle_data[13], squirtle_data[14], squirtle_data[15], squirtle_data[16], random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), [Tailwhip(), Tackle()])

class Trainer():
    def __init__(self, name, party, sprite, player=False):
        self.name = name
        self.party = party
        self.sprite = sprite
        self.player = player
        global scale
        # scale current size of sprite by scale factor
        self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * scale, self.sprite.get_height() * scale))
        if self.player:
            self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * 2, self.sprite.get_height() * 2))


    def battlesprite_draw(self):
        screen.blit(self.sprite, (0, 0))

    def update(self):
        self.battlesprite_draw()
        for pokemon in self.party:
            pokemon.update()

player = Trainer("Red", [charmander], pygame.image.load(f"assets/trainers/red.png"), True)
opponent = Trainer("Blue", [squirtle], pygame.image.load(f"assets/trainers/blue.png"))

player.party[0].battle_pos = (10 * scale, 40 * scale)
opponent.party[0].battle_pos = (130 * scale - 64, 10 * scale)

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((255, 255, 255))
        player.update()
        opponent.update()
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    
if __name__ == "__main__":
    main()