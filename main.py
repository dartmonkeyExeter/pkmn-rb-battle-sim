import pygame, sqlite3, math, copy
from moves import *

pygame.init()
pygame.mixer.init()
scale = 4
HEIGHT, WIDTH = 144 * scale, 160 * scale
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pokémon Red / Blue Battle System")
clock = pygame.time.Clock()
fps = 59.7275 # keep this mf accurate
font = pygame.font.Font("assets/fonts/pkmnfl.ttf", 8 * scale)
game_loop_idx = 0

game_state = "battle"
battle_state = "precutscene"
battle_sub_state = "init"
turn_count = 0
battle_index = 0
battle_text_index = 0
battle_mon_index = 0
hp_fps_wait = 0
shownFirst = False
player_mon_cry = None
opponent_mon_cry = None

player_intended_action = None
opponent_intended_action = None
msgs_index = 0
speed_stage_multipliers = {
    -6: 2 / 8,
    -5: 2 / 7,
    -4: 2 / 6,
    -3: 2 / 5,
    -2: 2 / 4,
    -1: 2 / 3,
     0: 2 / 2,
     1: 3 / 2,
     2: 4 / 2,
     3: 5 / 2,
     4: 6 / 2,
     5: 7 / 2,
     6: 8 / 2,
}

who_went_first = None
half_turn_done = False

trainer_music = pygame.mixer.music.load("assets/music/trainer_battle.mp3")
# 9x10 grid


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

        self.pending_hp = 0

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

        self.collected_dmg = 0 # used for moves like counter and bide and mirror coat n stuff
        self.turn_count = 0 # used for moves like bide and rollout n stuff
        self.dot_turns = 0 # used for moves like toxic and leech seed
        self.invincible = False # used for moves like fly and dig

        self.owner_reference = None
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
    def __init__(self, name, party, sprite, player=False, ai_level=1):
        self.name = name
        self.party = party
        self.sprite = sprite
        self.player = player
        if not self.player:
            self.ai_level = ai_level
        
        self.current_pokemon = self.party[0]
        self.battle_pos = (0, 0)
        self.field_move = []
        self.field_move_turns = []

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
                hp_surface = font.render(f"{int(self.pokemon.curr_hp)}/    {self.pokemon.max_hp}", True, (0, 0, 0))
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

class MovesSelect(UIelement):
    def __init__(self, sprite, pos):
        super().__init__(sprite, pos)

    def draw(self):
        global scale, player, current_hover
        moves = player.current_pokemon.moves
        screen.blit(self.sprite, self.pos)
        for i in range(4):
            try:
                move_surface = font.render(moves[i].name.upper(), True, (0, 0, 0))
                screen.blit(move_surface, (self.pos[0] + 48 * scale, self.pos[1] + (i * 8 * scale + (40 * scale))))
            except IndexError:
                move_surface = font.render("-", True, (0, 0, 0))
                screen.blit(move_surface, (self.pos[0] + 48 * scale, self.pos[1] + (i * 8 * scale + (40 * scale))))

        type_surface = font.render(moves[current_hover].type.upper(), True, (0, 0, 0))
        screen.blit(type_surface, (self.pos[0] + 24 * scale, self.pos[1] + 16 * scale))

        pp_surface = font.render(f"{moves[current_hover].curr_pp}/{moves[current_hover].pp}", True, (0, 0, 0))
        screen.blit(pp_surface, (self.pos[0] + 40 * scale, self.pos[1] + 24 * scale))


main_textbox = UIelement(pygame.image.load("assets/ui/battle/textbox.png"), (0, 96 * scale))
continue_tri = UIelement(pygame.image.load("assets/ui/battle/continue.png"), (142 * scale, 130 * scale))
player_healthbar = HealthBar(pygame.image.load("assets/ui/battle/player_healthbar.png"), (75 * scale, 67 * scale), player=True)
opponent_healthbar = HealthBar(pygame.image.load("assets/ui/battle/opponent_healthbar.png"), (8 * scale, 10 * scale))

main_options_ui = UIelement(pygame.image.load("assets/ui/battle/main_options.png"), (64 * scale, 96 * scale))
current_hover = 0
opts_cur_hov_dict = {0: (72 * scale, 112 * scale), 
                1: (120 * scale, 112 * scale), 
                2: (72 * scale, 128 * scale), 
                3: (120 * scale, 128 * scale)}
main_selector = UIelement(pygame.image.load("assets/ui/battle/right_arrow.png"), (72 * scale, 112 * scale))

moves_ui = MovesSelect(pygame.image.load("assets/ui/battle/move_select.png"), (0, 64 * scale))
moves_cur_hov_dict = {0: (41 * scale, 106 * scale),
                    1: (41 * scale, 114 * scale),
                    2: (41 * scale, 122 * scale),
                    3: (41 * scale, 130 * scale)}
moves_selector = UIelement(pygame.image.load("assets/ui/battle/right_arrow.png"), (8 * scale, 112 * scale))

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

charmander = Pokemon(charmander_data[0], charmander_data[1], "CHARMANDER", 5, 0, charmander_data[2], charmander_data[3], charmander_data[12], charmander_data[13], charmander_data[14], charmander_data[15], charmander_data[16], random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), [Scratch(), Growl(), Quickattack()], True)
mewtwo = Pokemon(150, "MEWTWO", "MEWTWO", 70, 0, "PSYCHIC", None, 106, 110, 90, 154, 130, 15, 15, 15, 15, [Tackle(), Growl(), Quickattack()], True)

squirtle = Pokemon(squirtle_data[0], squirtle_data[1], "SQUIRTLE", 5, 0, squirtle_data[2], squirtle_data[3], squirtle_data[12], squirtle_data[13], squirtle_data[14], squirtle_data[15], squirtle_data[16], random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), [Tailwhip(), Tackle()])
bulbasaur = Pokemon(bulbasaur_data[0], bulbasaur_data[1], "BULBASAUR", 5, 0,bulbasaur_data[2], bulbasaur_data[3], bulbasaur_data[12], bulbasaur_data[13], bulbasaur_data[14], bulbasaur_data[15], 140, random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), random.randint(0, 15), [Growl(), Tackle()])

player = Trainer("RED", [mewtwo], pygame.image.load(f"assets/trainers/red.png"), True)
blue = Trainer("BLUE", [bulbasaur, squirtle], pygame.image.load(f"assets/trainers/blue.png"), ai_level=0)

player.party[0].owner_reference = player
blue.party[0].owner_reference = blue

PLAYER_INIT_BATTLEPOS = [160 * scale, 40 * scale]
OPPONENT_INIT_BATTLEPOS = [-50 * scale, 0 * scale]

PLAYER_FINAL_BATTLEPOS = [10 * scale, 40 * scale]
PLAYERMON_FINAL_BATTLEPOS = [10 * scale, 40 * scale]
OPPONENT_FINAL_BATTLEPOS = [95 * scale, 0 * scale]
OPPONENTMON_FINAL_BATTLEPOS = [110 * scale, 15 * scale]

def display_text(text, pos, index):
    global screen, clock, font

    lines = text.split("\n")
    characters_to_display = index * 3  # Controls text reveal speed
    # Handle single-line messages
    if len(lines) == 1:
        text_to_display = lines[0][:characters_to_display]  # Display only up to the limit
        text_surface = font.render(text_to_display, True, (0, 0, 0))
        screen.blit(text_surface, pos)

    # Handle two-line messages
    elif len(lines) == 2:
        if characters_to_display <= len(lines[0]):  
            # If we haven't reached the second line yet
            text_to_display = lines[0][:characters_to_display]
            text_surface = font.render(text_to_display, True, (0, 0, 0))
            screen.blit(text_surface, pos)
        else:
            # Display first line fully
            text_surface_one = font.render(lines[0], True, (0, 0, 0))
            screen.blit(text_surface_one, pos)

            # Calculate characters remaining for second line
            remaining_chars = characters_to_display - len(lines[0])
            remaining_chars = min(remaining_chars, len(lines[1]))  # Prevents cutting off last chars

            text_to_display = lines[1][:remaining_chars]
            text_surface_two = font.render(text_to_display, True, (0, 0, 0))
            screen.blit(text_surface_two, (pos[0], pos[1] + 15 * scale))  # Second line position

    # Check if the full message has been displayed (ignoring newline characters)
    if characters_to_display >= len(text.replace("\n", "")):
        return "done"

def generate_spiral(width, height, cell_size):
    grid = [[False] * (width // cell_size) for _ in range(height // cell_size)]
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Down, Right, Up, Left
    x, y = 0, 0
    dir_idx = 0
    order = []
    
    for _ in range((width // cell_size) * (height // cell_size)):
        order.append((x, y))
        grid[y][x] = True
        
        nx, ny = x + directions[dir_idx][0], y + directions[dir_idx][1]
        if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid) and not grid[ny][nx]:
            x, y = nx, ny
        else:
            dir_idx = (dir_idx + 1) % 4
            x, y = x + directions[dir_idx][0], y + directions[dir_idx][1]
    
    return order

order = generate_spiral(WIDTH, HEIGHT, 16 * scale)
filled_squares = []

def pre_battle_cutscene(idx):
    # fill screen with black squares that follow each other like snake, to the center
    # starting from the top left corner and going down

    global screen, scale, trainer_music, filled_squares, battle_state

    if idx == 1:
        pygame.mixer.music.play(loops=-1)

    try:
        filled_squares.append(order.pop(0))
    except IndexError:
        pygame.time.delay(250)
        battle_state = "init"
        return "done"
    
    for square in filled_squares:
        x, y = square
        pygame.draw.rect(screen, (0, 0, 0), (x * 16 * scale, y * 16 * scale, 16 * scale, 16 * scale))

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
    elif index >= 4 * wait_factor:
        return "done"
    elif shownFirst:
        return "showing"
    
def trainer_pkmn_disappear(pokemon, index, shownFirst=False):
    wait_factor = 8  # Number of frames to wait before next scaling

    # Centering the scale transformation from the top
    def scale_pokemon(factor):
        original_width, original_height = pokemon.init_scale
        new_width = original_width // factor
        new_height = original_height // factor

        # Get the current top center before scaling
        center_x = pokemon.battle_pos[0] + pokemon.sprite.get_width() // 2
        bottom_y = pokemon.battle_pos[1] + pokemon.sprite.get_height()  # bottom of the sprite

        # Scale the sprite
        pokemon.sprite = pygame.transform.scale(pokemon.original_sprite, (new_width, new_height))

        # Reposition to keep it anchored at the center top
        pokemon.battle_pos[0] = center_x - new_width // 2
        pokemon.battle_pos[1] = bottom_y - new_height  # Keep the top edge aligned

    if index == 1 * wait_factor:
        scale_pokemon(1)
        return "showing"
    elif index == 2 * wait_factor:
        scale_pokemon(2)
        return "showing"
    elif index == 3 * wait_factor:
        scale_pokemon(4)
        return "showing"
    elif index >= 4 * wait_factor:
        return "done"

def temp_init(opponent):
    global battle_sub_state, player, PLAYER_INIT_BATTLEPOS, OPPONENT_INIT_BATTLEPOS, turn_count, battle_index, battle_text_index, battle_mon_index, shownFirst, player_mon_cry, opponent_mon_cry
    player_mon_cry = pygame.mixer.Sound(f"assets/sfx/cries/{player.party[0].dex_num:03}.wav")
    opponent_mon_cry = pygame.mixer.Sound(f"assets/sfx/cries/{opponent.party[0].dex_num:03}.wav")

    player.battle_pos = PLAYER_INIT_BATTLEPOS
    opponent.battle_pos = OPPONENT_INIT_BATTLEPOS

    for pokemon in player.party:
        pokemon.battle_pos = PLAYERMON_FINAL_BATTLEPOS
    for pokemon in opponent.party:
        pokemon.battle_pos = OPPONENTMON_FINAL_BATTLEPOS

    player_healthbar.pokemon = player.party[0]
    opponent_healthbar.pokemon = opponent.party[0]

def death_check(pokemon):
    if pokemon.curr_hp <= 0:
        return True
    return False

def trainer_battle_init(opponent, key_pressed=None):
    # to be called in main loop while battling
    global battle_state, battle_sub_state, player, PLAYER_INIT_BATTLEPOS, OPPONENT_INIT_BATTLEPOS, battle_index, battle_text_index, battle_mon_index, shownFirst, player_mon_cry, opponent_mon_cry
    
    if battle_index == 0:
        player_mon_cry = pygame.mixer.Sound(f"assets/sfx/cries/{player.party[0].dex_num:03}.wav")
        opponent_mon_cry = pygame.mixer.Sound(f"assets/sfx/cries/{opponent.party[0].dex_num:03}.wav")

        player.battle_pos = PLAYER_INIT_BATTLEPOS
        opponent.battle_pos = OPPONENT_INIT_BATTLEPOS

        for pokemon in player.party:
            pokemon.battle_pos = PLAYERMON_FINAL_BATTLEPOS
        for pokemon in opponent.party:
            pokemon.battle_pos = OPPONENTMON_FINAL_BATTLEPOS

        player_healthbar.pokemon = player.party[0]
        opponent_healthbar.pokemon = opponent.party[0]

    if battle_sub_state == "init":
        if player.battle_pos[0] > PLAYER_FINAL_BATTLEPOS[0]:
            player.battle_pos = (player.battle_pos[0] - (2 * scale), player.battle_pos[1])
        if opponent.battle_pos[0] < OPPONENT_FINAL_BATTLEPOS[0]:
            opponent.battle_pos = (opponent.battle_pos[0] + (2 * scale), opponent.battle_pos[1])

        if player.battle_pos[0] <= PLAYER_FINAL_BATTLEPOS[0] and opponent.battle_pos[0] >= OPPONENT_FINAL_BATTLEPOS[0]:
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

            display_text(f"{opponent.name} sent\nout {opponent.party[0].species}!", (8 * scale, 110 * scale), battle_text_index // 2)
            scaling = trainer_pkmn_appear(opponent.party[0], battle_mon_index, shownFirst)
            opponent_healthbar.draw()

            if scaling == "done":
                opponent.party[0].battlesprite_draw()
                opponent_mon_cry.play()
                while pygame.mixer.get_busy():
                    pygame.time.delay(100)
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
                player_mon_cry.play()
                while pygame.mixer.get_busy():
                    pygame.time.delay(100)
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

def trainer_battle_main(opponent, key_pressed=None):
    
    global player, battle_sub_state, current_hover, moves_selector, opponent_intended_action, player_intended_action, battle_text_index, battle_state, battle_index, msgs_index, msgs, hp_fps_wait, who_went_first, half_turn_done, battle_mon_index, shownFirst, opponent_mon_cry, opponent_healthbar
    
    if battle_sub_state == "player_select":
        half_turn_done = False
        main_selector.pos = opts_cur_hov_dict[current_hover]

        opponent.current_pokemon.battlesprite_draw()
        player.current_pokemon.battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()
        main_options_ui.draw()
        main_selector.draw()

        if key_pressed == "up":
            current_hover = (current_hover - 2) % 4
        elif key_pressed == "down":
            current_hover = (current_hover + 2) % 4
        elif key_pressed == "left":
            current_hover = (current_hover - 1) % 4
        elif key_pressed == "right":
            current_hover = (current_hover + 1) % 4
        
        if key_pressed == "enter":
            if current_hover == 0:
                battle_sub_state = "player_select_move"
                current_hover = 0
            elif current_hover == 1:
                pass
            elif current_hover == 2:
                pass
            elif current_hover == 3:
                battle_sub_state = "player_run"
            
    elif battle_sub_state == "player_select_move":
        moves_selector.pos = moves_cur_hov_dict[current_hover]
        opponent.current_pokemon.battlesprite_draw()
        player.current_pokemon.battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()
        moves_ui.draw()
        moves_selector.draw()

        if key_pressed == "up":
            current_hover = (current_hover - 1) % len(player.current_pokemon.moves)
        elif key_pressed == "down":
            current_hover = (current_hover + 1) % len(player.current_pokemon.moves)

        if key_pressed == "backspace":
            battle_sub_state = "player_select"
            current_hover = 0

        if key_pressed == "enter":
            player_intended_action = player.current_pokemon.moves[current_hover]
            battle_sub_state = "opponent_select_move"
            current_hover = 0

    elif battle_sub_state == "opponent_select_move":
        # ai, only needs to be called once
        if opponent.ai_level == 0:
            opponent_intended_action = opponent.current_pokemon.moves[random.randint(0, len(opponent.current_pokemon.moves) - 1)]

        player_mon_speed = player.current_pokemon.speed * speed_stage_multipliers[player.current_pokemon.speed_stage]
        opponent_mon_speed = opponent.current_pokemon.speed * speed_stage_multipliers[opponent.current_pokemon.speed_stage]

        player_mon_speed = player_mon_speed // 4 if player.current_pokemon.status == "paralyzed" else player_mon_speed
        opponent_mon_speed = opponent_mon_speed // 4 if opponent.current_pokemon.status == "paralyzed" else opponent_mon_speed

        if "priority" in player_intended_action.tags and "priority" in opponent_intended_action.tags:
            if player_mon_speed > opponent_mon_speed:
                who_went_first = "player"
                battle_sub_state = "perform_player_actions"
            elif player_mon_speed < opponent_mon_speed:
                who_went_first = "opponent"
                battle_sub_state = "perform_opponent_actions"
            elif player_mon_speed == opponent_mon_speed:
                who_went_first = "player"
                battle_sub_state = "perform_player_actions"
        elif "priority" in player_intended_action.tags:
            who_went_first = "player"
            battle_sub_state = "perform_player_actions"
        elif "priority" in opponent_intended_action.tags:
            who_went_first = "opponent"
            battle_sub_state = "perform_opponent_actions"
        elif player_mon_speed > opponent_mon_speed:
            who_went_first = "player"
            battle_sub_state = "perform_player_actions"
        elif player_mon_speed < opponent_mon_speed:
            who_went_first = "opponent"
            battle_sub_state = "perform_opponent_actions"
        elif player_mon_speed == opponent_mon_speed:
            who_went_first = "player"
            battle_sub_state = "perform_player_actions"
        
    elif battle_sub_state == "perform_player_actions":
        opponent.current_pokemon.battlesprite_draw()
        player.current_pokemon.battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()

        if player_intended_action:
            msgs = player_intended_action.effect(player.current_pokemon, opponent.current_pokemon, False)
            print(opponent.current_pokemon.pending_hp, player.current_pokemon.pending_hp)
            player_intended_action = None
            msgs_index = 0
            battle_sub_state = "display_msgs"
            msgs = [msg for msg in msgs if msg != "" and msg != None]
    
    elif battle_sub_state == "perform_opponent_actions":
        opponent.current_pokemon.battlesprite_draw()
        player.current_pokemon.battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()

        if opponent_intended_action:
            msgs = opponent_intended_action.effect(opponent.current_pokemon, player.current_pokemon, True)
            print(opponent.current_pokemon.pending_hp, player.current_pokemon.pending_hp)
            opponent_intended_action = None
            msgs_index = 0
            battle_sub_state = "display_msgs"
            msgs = [msg for msg in msgs if msg != "" and msg != None]

    elif battle_sub_state == "display_msgs":
        opponent.current_pokemon.battlesprite_draw()
        player.current_pokemon.battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()

        battle_text_index += 1

        if display_text(msgs[msgs_index], (8 * scale, 110 * scale), battle_text_index // 2) == "done":
            if msgs_index < len(msgs) - 1 and opponent.current_pokemon.pending_hp == 0 and player.current_pokemon.pending_hp == 0 and battle_text_index > 100:
                battle_text_index = 0
                msgs_index += 1
                pygame.time.delay(500)
            
            if msgs_index + 1 == len(msgs) and opponent.current_pokemon.pending_hp == 0 and player.current_pokemon.pending_hp == 0:
                continue_tri.draw()
                if key_pressed == "enter" and half_turn_done:
                    battle_sub_state = "player_select"
                    msgs_index = 0
                    battle_text_index = 0
                elif key_pressed == "enter":
                    half_turn_done = True
                    if who_went_first == "player":
                        if death_check(opponent.current_pokemon):
                            battle_sub_state = "opponent_withdraw_mon"
                            shownFirst = False
                            battle_mon_index = 0
                        else:
                            battle_sub_state = "perform_opponent_actions"
                    elif who_went_first == "opponent":
                        if death_check(player.current_pokemon):
                            battle_sub_state = "player_withdraw_mon"
                            shownFirst = False
                            battle_mon_index = 0
                        else:
                            battle_sub_state = "perform_player_actions"
                    msgs_index = 0
                    battle_text_index = 0

    elif battle_sub_state == "opponent_withdraw_mon":
        opponent.current_pokemon.battlesprite_draw()
        player.current_pokemon.battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()
        battle_text_index += 1
        battle_mon_index += 1

        display_text(f"{opponent.current_pokemon.species} fainted!", (8 * scale, 110 * scale), battle_text_index // 2)
        scaling = trainer_pkmn_disappear(opponent.current_pokemon, battle_mon_index, shownFirst)
        opponent_healthbar.draw()

        if scaling == "done":
            opponent_mon_cry.play()
            while pygame.mixer.get_busy():
                pygame.time.delay(100)
            battle_sub_state = "opponent_choose_mon"
            battle_mon_index = 0
            battle_text_index = 0
            shownFirst = False
        elif scaling == "shownFirst":
            opponent.party[0].battlesprite_draw()
            shownFirst = True
        elif scaling == "showing":
            opponent.party[0].battlesprite_draw()

    elif battle_sub_state == "opponent_choose_mon":
        player.current_pokemon.battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()
        for pokemon in opponent.party:
            if not death_check(pokemon):
                opponent.current_pokemon = pokemon
                opponent_mon_cry = pygame.mixer.Sound(f"assets/sfx/cries/{opponent.current_pokemon.dex_num:03}.wav")
                opponent_healthbar.pokemon = opponent.current_pokemon
                battle_sub_state = "opponent_send_out_mon"
                pygame.time.delay(500)
                break
        
        if battle_sub_state != "opponent_send_out_mon":
            battle_sub_state = "player_wins"
            battle_text_index = 0
        
    elif battle_sub_state == "opponent_send_out_mon":
        player.current_pokemon.battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()
        battle_text_index += 1
        battle_mon_index += 1
        display_text(f"{opponent.name} sent\nout {opponent.current_pokemon.species}!", (8 * scale, 110 * scale), battle_text_index // 2)
        opponent.current_pokemon.battle_pos = [110 * scale, 15 * scale]
        scaling = trainer_pkmn_appear(opponent.current_pokemon, battle_mon_index, shownFirst)

        if scaling == "done":
            opponent_mon_cry.play()
            while pygame.mixer.get_busy():
                pygame.time.delay(100)
            battle_sub_state = "player_select"
            battle_mon_index = 0
            battle_text_index = 0
            shownFirst = False
        elif scaling == "shownFirst":
            opponent.current_pokemon.battlesprite_draw()
            shownFirst = True
        elif scaling == "showing":
            opponent.current_pokemon.battlesprite_draw()


    elif battle_sub_state == "player_run":
        opponent.party[0].battlesprite_draw()
        player.party[0].battlesprite_draw()
        main_textbox.draw()
        player_healthbar.draw()
        opponent_healthbar.draw()

        battle_text_index += 1

        if display_text(f"There's no running\nfrom a trainer battle!", (8 * scale, 110 * scale), battle_text_index // 2) == "done":
            continue_tri.draw()
            if key_pressed == "enter":
               battle_sub_state = "player_select"
               battle_text_index = 0

    if opponent.current_pokemon.pending_hp < 0:
        opponent.current_pokemon.curr_hp -= 0.25
        opponent.current_pokemon.pending_hp += 0.25
        if opponent.current_pokemon.curr_hp == 0:
            opponent.current_pokemon.pending_hp = 0

    elif opponent.current_pokemon.pending_hp > 0:
        opponent.current_pokemon.curr_hp += 0.25
        opponent.current_pokemon.pending_hp -= 0.25
        if opponent.current_pokemon.curr_hp == opponent.current_pokemon.max_hp:
            opponent.current_pokemon.pending_hp = 0

    if player.current_pokemon.pending_hp < 0:
        player.current_pokemon.curr_hp -= 0.25
        player.current_pokemon.pending_hp += 0.25
        if player.current_pokemon.curr_hp == 0:
            player.current_pokemon.pending_hp = 0

    elif player.current_pokemon.pending_hp > 0:
        player.current_pokemon.curr_hp += 0.25
        player.current_pokemon.pending_hp -= 0.25
        if player.current_pokemon.curr_hp == player.current_pokemon.max_hp:
            player.current_pokemon.pending_hp = 0      

temp_init(blue) # TEMP DELETE LATER !!!

def main():
    global screen, clock, fps, battle_state, battle_sub_state, turn_count, battle_index
    running = True
    game_loop_idx = 0
    while running:
        key = ""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    key = "enter"
                elif event.key == pygame.K_UP:
                    key = "up"
                elif event.key == pygame.K_DOWN:
                    key = "down"
                elif event.key == pygame.K_LEFT:
                    key = "left"
                elif event.key == pygame.K_RIGHT:
                    key = "right"
                elif event.key == pygame.K_BACKSPACE:
                    key = "backspace"

        screen.fill((248, 232, 248))
        
        if game_state == "battle":
            game_loop_idx += 1
            if battle_state == "precutscene":
                if pre_battle_cutscene(game_loop_idx) == "done":
                    game_loop_idx = 0
            elif battle_state == "init":
                if game_loop_idx == 1: pygame.time.delay(100)
                trainer_battle_init(opponent=blue, key_pressed=key)
            elif battle_state == "main":
                trainer_battle_main(opponent=blue, key_pressed=key)

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    
if __name__ == "__main__":
    main()