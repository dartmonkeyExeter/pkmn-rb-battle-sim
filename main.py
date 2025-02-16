import pygame, sqlite3, math
from moves import *

screen = pygame.display.set_mode((320, 288))
pygame.display.set_caption("Pokémon Red / Blue Battle System")
clock = pygame.time.Clock()
fps = 59.7275 # keep this mf accurate

class Pokemon():
    def __init__(self, species, nickname, level, xp, type1, type2, hp, atk, defense, spec, speed, hp_iv, atk_iv, def_iv, speed_iv, spec_iv, moves):
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
        
        self.hp_iv = hp_iv
        self.atk_iv = atk_iv
        self.def_iv = def_iv
        self.speed_iv = speed_iv
        self.spec_iv = spec_iv

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
        self.bide_dmg = 0
        self.turn_count = 0 # used for moves like bide and rollout n stuff
        self.dot_turns = 0 # used for moves like toxic and leech seed

    def calc_stat(self, base, iv, ev, level, hp=False):
        if hp:
            return math.floor(((2 * base + iv + (ev // 4)) * level) / 100 + level + 10)
        return math.floor((((2 * base + iv + (ev // 4)) * level) / 100) + 5)
        
# ok im gonna test the moves now, i only made absorb so far

# get the pokemon from the database
conn = sqlite3.connect("FirstGenPokemon.db")
c = conn.cursor()
c.execute("SELECT * FROM pokemon WHERE Name = 'Bulbasaur'")
bulbasaur_data = c.fetchone()
c.execute("SELECT * FROM pokemon WHERE Name = 'Squirtle'")
squirtle_data = c.fetchone()
conn.close()

# create the pokemon objects
# hp starts at index 12
squirtle = Pokemon(squirtle_data[1], "Squirty", 5, 0, squirtle_data[2], squirtle_data[3], squirtle_data[12], squirtle_data[13], squirtle_data[14], squirtle_data[15], squirtle_data[16], 0, 0, 0, 0, 0, [])
bulbasaur = Pokemon(bulbasaur_data[1], "Bulby", 5, 0, bulbasaur_data[2], bulbasaur_data[3], bulbasaur_data[12], bulbasaur_data[13], bulbasaur_data[14], bulbasaur_data[15], bulbasaur_data[16], 0, 0, 0, 0, 0, [Absorb()])
print(squirtle.curr_hp)
print(bulbasaur.moves[0].effect(bulbasaur, squirtle, False))
print(squirtle.curr_hp)
quit()

class Trainer():
    def __init__(self, name, party, sprite):
        self.name = name
        self.party = party
        self.sprite = sprite


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