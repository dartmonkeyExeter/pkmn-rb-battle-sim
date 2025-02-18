import pygame, sqlite3, math, copy
from moves import *

pygame.init()
scale = 1
screen = pygame.display.set_mode((160 * scale, 144 * scale))
pygame.display.set_caption("Pokémon Red / Blue Battle System")
clock = pygame.time.Clock()
fps = 59.7275 # keep this mf accurate
font = pygame.font.Font("assets/fonts/pkmnfl.ttf", 8 * scale)

game_state = "battle"
battle_state = "init"
battle_sub_state = "init"
turn_count = 0
battle_index = 0
battle_text_index = 0
battle_mon_index = 0
shownFirst = False

class Pokemon():
    def __init__(self, dex_num, species, nickname, level, xp, type1, type2, hp, atk, defense, spec, speed, atk_iv, def_iv, speed_iv, spec_iv, moves, player_owned=False):
        self.dex_num = dex_num
        self.species = species.upper()
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
        self.battle_pos = [0, 0]
        if self.player_owned:
            self.sprite = pygame.image.load(f"assets/pokemon/back/{self.dex_num}.png")
            self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * 2, self.sprite.get_height() * 2))
        else:
            self.sprite = pygame.image.load(f"assets/pokemon/front/{self.dex_num}.png")

        self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * scale, self.sprite.get_height() * scale))
        self.original_sprite = copy.copy(self.sprite)
        self.init_scale = (self.sprite.get_width(), self.sprite.get_height())

    def calc_stat(self, base, iv, ev, level, hp=False):
        if hp:
            return math.floor(((2 * base + iv + (ev // 4)) * level) / 100 + level + 10)
        return math.floor((((2 * base + iv + (ev // 4)) * level) / 100) + 5)
        
    def battlesprite_draw(self):
        global scale
        screen.blit(self.sprite, self.battle_pos) # should start off screen on right side

    def update(self):
        self.battlesprite_draw()
                
class Trainer():
    def __init__(self, name, party, sprite, player=False):
        self.name = name
        self.party = party
        self.sprite = sprite
        self.player = player
        self.current_pokemon = self.party[0]
        self.battle_pos = (0, 0)
        global scale
        # scale current size of sprite by scale factor
        self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * scale, self.sprite.get_height() * scale))
        if self.player:
            self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * 2, self.sprite.get_height() * 2))


    def battlesprite_draw(self):
        screen.blit(self.sprite, self.battle_pos)

    def update(self):
        for pokemon in self.party:
            pokemon.update()

    def draw(self):
        pass

class UIelement():
    def __init__(self, sprite, pos):
        self.sprite = sprite
        self.sprite = pygame.transform.scale(self.sprite, (self.sprite.get_width() * scale, self.sprite.get_height() * scale))
        self.pos = pos

    def draw(self):
        screen.blit(self.sprite, self.pos)

class HealthBar(UIelement):
    def __init__(self, sprite, pos, pokemon=None, player=False):
        super().__init__(sprite, pos)
        self.pokemon = pokemon
        self.player = player

    def draw(self):
        global scale
        if self.pokemon:
            # draw the health bar
            if self.player:
                health_percentage = self.pokemon.curr_hp / self.pokemon.max_hp
                health_bar = pygame.Surface((health_percentage * 48 * scale, 2 * scale))
                health_bar.fill((72, 160, 88))
                screen.blit(health_bar, (self.pos[0] + 24 * scale, self.pos[1] + 11 * scale))

                # draw the pokemon name
                name_surface = font.render(self.pokemon.nickname, True, (0, 0, 0))
                screen.blit(name_surface, (self.pos[0] + 4 * scale, self.pos[1] - 9 * scale))

                # draw the level
                level_surface = font.render(f"{self.pokemon.level}", True, (0, 0, 0))
                screen.blit(level_surface, (self.pos[0] + 48 * scale, self.pos[1] - 1 * scale))

                # draw the hp / max hp
                hp_surface = font.render(f"{self.pokemon.curr_hp}/    {self.pokemon.max_hp}", True, (0, 0, 0))
                screen.blit(hp_surface, (self.pos[0] + 24 * scale, self.pos[1] + 16 * scale))

                screen.blit(self.sprite, self.pos)

            else:
                health_percentage = self.pokemon.curr_hp / self.pokemon.max_hp
                health_bar = pygame.Surface((health_percentage * 48 * scale, 2 * scale))
                health_bar.fill((72, 160, 88))
                screen.blit(health_bar, (self.pos[0] + 21 * scale, self.pos[1] + 10 * scale))

                # draw the pokemon name
                name_surface = font.render(self.pokemon.nickname, True, (0, 0, 0))
                screen.blit(name_surface, (self.pos[0] - 2 * scale, self.pos[1] - 10 * scale))

                # draw the level
                level_surface = font.render(f"{self.pokemon.level}", True, (0, 0, 0))
                screen.blit(level_surface, (self.pos[0] + 29 * scale, self.pos[1] - 2 * scale))

                screen.blit(self.sprite, self.pos)

main_textbox = UIelement(pygame.image.load("assets/ui/battle/textbox.png"), (0, 97 * scale))
continue_tri = UIelement(pygame.image.load("assets/ui/battle/continue.png"), (142 * scale, 130 * scale))
player_healthbar = HealthBar(pygame.image.load("assets/ui/battle/player_healthbar.png"), (75 * scale, 67 * scale), player=True)
opponent_healthbar = HealthBar(pygame.image.load("assets/ui/battle/opponent_healthbar.png"), (8 * scale, 10 * scale))

# get the pokemon from the database
conn = sqlite3.connect("FirstGenPokemon.db")
c = conn.cursor()
c.execute("SELECT * FROM pokemon WHERE Name = 'Charmander'")
charmander_data = c.fetchone()
c.execute("SELECT * FROM pokemon WHERE Name = 'Squirtle'")
squirtle_data = c.fetchone()
c.execute("SELECT * FROM pokemon WHERE Name = 'Bulbasaur'")
bulbasaur_data = c.fetchone()
conn.close()

# create the pokemon objects
# hp starts at index 12

charmander = Pokemon(charmander_data[0], charmander_data[1], "CHARMANDER", 5, 0, charmander_data[2], charmander_data[3], charmander_data[12], charmander_data[13], charmander_data[14], charmander_data[15], charmander_data[16], random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), [Growl(), Scratch()], True)
squirtle = Pokemon(squirtle_data[0], squirtle_data[1], "SQUIRTLE", 5, 0, squirtle_data[2], squirtle_data[3], squirtle_data[12], squirtle_data[13], squirtle_data[14], squirtle_data[15], squirtle_data[16], random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), [Tailwhip(), Tackle()])
bulbasaur = Pokemon(bulbasaur_data[0], bulbasaur_data[1], "BULBASAUR", 5, 0, bulbasaur_data[2], bulbasaur_data[3], bulbasaur_data[12], bulbasaur_data[13], bulbasaur_data[14], bulbasaur_data[15], bulbasaur_data[16], random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), [Growl(), Tackle()])

player = Trainer("RED", [charmander], pygame.image.load(f"assets/trainers/red.png"), True)
opponent = Trainer("BLUE", [squirtle], pygame.image.load(f"assets/trainers/blue.png"))

player_init_battlepos = [160 * scale, 40 * scale]
opponent_init_battlepos = [-50 * scale, 0 * scale]

player_final_battlepos = [10 * scale, 40 * scale]
playermon_final_battlepos = [10 * scale, 40 * scale]
opponent_final_battlepos = [95 * scale, 0 * scale]
opponentmon_final_battlepos = [110 * scale, 15 * scale]

# ok battle should work in states
# the init state is the trainers sliding to their positions from off screen, and text "TRAINER wants to fight!"
# off screen positions:
# player: (160 * scale, 40 * scale)
# opponent: (-50 * scale, 0 * scale)
# then opponent slides off, sends out mon "TRAINER sent out POKEMON!"
# then player slides off, sends out mon "GO! POKEMON!"
# then battle starts

# function to display text, 3 chars at a time
def display_text(text, pos, index):
    global screen, clock, font

    lines = text.split("\n")
    characters_to_display = index * 3

    if len(lines) == 1:
        text_to_display = text[:characters_to_display]
        text_surface = font.render(text_to_display, True, (0, 0, 0))
        screen.blit(text_surface, pos)
    
    elif len(lines) == 2:
        if characters_to_display <= len(lines[0]):
            text_to_display = lines[0][:characters_to_display]
            text_surface = font.render(text_to_display, True, (0, 0, 0))
            screen.blit(text_surface, pos)

        else:
            text_surface_one = font.render(lines[0], True, (0, 0, 0))
            text_to_display = lines[1][:characters_to_display - len(lines[0])]
            text_surface_two = font.render(text_to_display, True, (0, 0, 0))
            screen.blit(text_surface_one, pos)
            screen.blit(text_surface_two, (pos[0], pos[1] + 15 * scale))

    if characters_to_display >= len(text):
        return "done"
    
def trainer_pkmn_appear(pokemon, index, shownFirst=False):
    # Start Pokémon small and grow to full size from the center bottom
    wait_factor = 8  # Number of frames to wait before next scaling

    # Centering the scale transformation from the bottom
    def scale_pokemon(factor):
        original_width, original_height = pokemon.init_scale  # Always scale from the original size
        new_width = original_width // factor
        new_height = original_height // factor

        # Get the current bottom center before scaling
        center_x = pokemon.battle_pos[0] + pokemon.sprite.get_width() // 2
        bottom_y = pokemon.battle_pos[1] + pokemon.sprite.get_height()  # bottom of the sprite

        # Scale the sprite
        pokemon.sprite = pygame.transform.scale(pokemon.original_sprite, (new_width, new_height))

        # Reposition to keep it anchored at the center bottom
        pokemon.battle_pos[0] = center_x - new_width // 2
        pokemon.battle_pos[1] = bottom_y - new_height  # Keep the bottom edge aligned

    if index == 1 * wait_factor:
        scale_pokemon(4)
        return "shownFirst"
    elif index == 2 * wait_factor:
        scale_pokemon(2)
        return "showing"
    elif index == 3 * wait_factor:
        scale_pokemon(1)
        return "showing"
    elif index == 4 * wait_factor:
        return "done"
    elif shownFirst:
        return "showing"

def trainer_battle_init(key_pressed=None):
    # to be called in main loop while battling
    global battle_sub_state, player, opponent, player_init_battlepos, opponent_init_battlepos, turn_count, battle_index, battle_text_index, battle_mon_index, shownFirst 
    
    if battle_index == 0:
        player.battle_pos = player_init_battlepos
        opponent.battle_pos = opponent_init_battlepos

        for pokemon in player.party:
            pokemon.battle_pos = playermon_final_battlepos
        for pokemon in opponent.party:
            pokemon.battle_pos = opponentmon_final_battlepos

        player_healthbar.pokemon = player.party[0]
        opponent_healthbar.pokemon = opponent.party[0]

    if battle_sub_state == "init":
        if player.battle_pos[0] > player_final_battlepos[0]:
            player.battle_pos = (player.battle_pos[0] - (2 * scale), player.battle_pos[1])
        if opponent.battle_pos[0] < opponent_final_battlepos[0]:
            opponent.battle_pos = (opponent.battle_pos[0] + (2 * scale), opponent.battle_pos[1])

        if player.battle_pos[0] <= player_final_battlepos[0] and opponent.battle_pos[0] >= opponent_final_battlepos[0]:
            battle_sub_state = "opponent_wants_to_fight"
            
        opponent.battlesprite_draw() # only draw the trainers for now
        player.battlesprite_draw()
        main_textbox.draw() # draw above the sprites

    elif battle_sub_state == "opponent_wants_to_fight":

        opponent.battlesprite_draw() # only draw the trainers for now
        player.battlesprite_draw()

        main_textbox.draw() # draw above the sprites
        battle_text_index += 1
        
        if display_text(f"{opponent.name} wants\nto fight!", (8 * scale, 110 * scale), battle_text_index // 2) == "done":
            continue_tri.draw()
            if key_pressed == "enter":
                battle_sub_state = "opponent_send_out_mon"
                battle_text_index = 0

    elif battle_sub_state == "opponent_send_out_mon":
        # slide opponent off screen, 

        if opponent.battle_pos[0] < 160 * scale:
            opponent.battle_pos = (opponent.battle_pos[0] + (4 * scale), opponent.battle_pos[1])
            opponent.battlesprite_draw()
            player.battlesprite_draw()
            main_textbox.draw()

        elif opponent.battle_pos[0] >= 160 * scale:
            player.battlesprite_draw()
            main_textbox.draw()
            battle_text_index += 1
            battle_mon_index += 1

            display_text(f"{opponent.name}\nsent out {opponent.party[0].species}!", (8 * scale, 110 * scale), battle_text_index // 2)
            scaling = trainer_pkmn_appear(opponent.party[0], battle_mon_index, shownFirst)
            opponent_healthbar.draw()

            if scaling == "done":
                opponent.party[0].battlesprite_draw()
                pygame.time.wait(500)
                battle_sub_state = "player_send_out_mon"
                battle_mon_index = 0
                battle_text_index = 0
                shownFirst = False
            elif scaling == "shownFirst":
                opponent.party[0].battlesprite_draw()
                shownFirst = True
            elif scaling == "showing":
                opponent.party[0].battlesprite_draw()

    elif battle_sub_state == "player_send_out_mon":
        # slide player off screen, 
        if player.battle_pos[0] > -80 * scale:
            player.battle_pos = (player.battle_pos[0] - (4 * scale), player.battle_pos[1])
            player.battlesprite_draw()
            opponent.party[0].battlesprite_draw()
            main_textbox.draw()
            opponent_healthbar.draw()

        elif player.battle_pos[0] <= -80 * scale:
            
            battle_text_index += 1
            battle_mon_index += 1

            scaling = trainer_pkmn_appear(player.party[0], battle_mon_index, shownFirst)
            opponent_healthbar.draw()
            player_healthbar.draw()

            if scaling == "done":
                player.party[0].battlesprite_draw()
                pygame.time.wait(500)
                battle_state = "main"
                battle_sub_state = "player_select"
                battle_text_index = 0
                battle_mon_index = 0
            elif scaling == "shownFirst":
                player.party[0].battlesprite_draw()
                shownFirst = True
            elif scaling == "showing":
                player.party[0].battlesprite_draw()

            opponent.party[0].battlesprite_draw()
            main_textbox.draw()
            display_text(f"Go! {player.party[0].species}!", (8 * scale, 110 * scale), battle_text_index // 2)

    battle_index += 1

def trainer_battle_main(key_pressed=None):
    pass


def main():
    global screen, clock, fps, battle_state, battle_sub_state, turn_count, battle_index
    running = True
    while running:
        key = ""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    key = "enter"

        screen.fill((248, 248, 248))
        
        if battle_state == "init":
            trainer_battle_init(key)

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    
if __name__ == "__main__":
    main()