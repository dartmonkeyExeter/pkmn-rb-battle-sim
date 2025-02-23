import random, pygame

class Move:
    def __init__(self, name, type, category, power, accuracy, pp):
        self.name = name
        self.type = type
        self.category = category
        self.power = power
        self.accuracy = accuracy
        self.pp = pp
        self.curr_pp = pp
        self.return_messages = []
        self.disabled = False
        self.crit_buff = False
        self.tags = []
        self.sound = pygame.mixer.Sound(f"assets/sfx/moves/{self.name.lower()}.wav")

    def __repr__(self):
        return f"{self.__class__.__name__}(Type: {self.type}, Power: {self.power}, Accuracy: {self.accuracy}, PP: {self.pp})"

CHART = {
        "normal": {"rock": 0.5, "ghost": 0},
        "fire": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 2, "bug": 2, "rock": 0.5, "dragon": 0.5},
        "water": {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
        "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
        "grass": {"fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5},
        "ice": {"water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2},
        "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0},
        "poison": {"grass": 2, "poison": 0.5, "ground": 0.5, "bug": 2, "rock": 0.5, "ghost": 0.5},
        "ground": {"fire": 2, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2},
        "flying": {"electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5},
        "psychic": {"fighting": 2, "poison": 2, "psychic": 0.5},
        "bug": {"fire": 0.5, "grass": 2, "fighting": 0.5, "poison": 2, "flying": 0.5, "psychic": 2, "ghost": 0.5},
        "rock": {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2},
        "ghost": {"normal": 0, "psychic": 2, "ghost": 2}, # fixed from the original games
        "dragon": {"dragon": 2},
    }

def calculate_damage(user_level, attack_type, attack_cat, defender_types, attack, attack_stage, defense, defense_stage, power, stab, critical, reflect, light_screen):
    # this formula so fucking complicated man

    if critical:
        a = attack
        d = defense
    else:
        if attack_stage > 0:
            a = attack * (2 + attack_stage) / 2
        elif attack_stage < 0:
            a = attack * 2 / (2 - attack_stage)
        else:
            a = attack

        if defense_stage > 0:
            d = defense * 2 / (2 + defense_stage)
        elif defense_stage < 0:
            d = defense * (2 - defense_stage) / 2
        else:
            d = defense

        if reflect and attack_cat == "physical" or light_screen and attack_cat == "special":
            d *= 2

    if a >= 256 or d >= 256:
        a = (a // 4) % 256
        d = (d // 4) % 256
        if a == 0:
            a = 1
        if d == 0:
            d = 1

    base_dmg = user_level
    base_dmg *= 2
    base_dmg //= 5
    base_dmg += 2
    base_dmg *= power
    base_dmg *= a
    base_dmg //= d
    base_dmg //= 50
    if base_dmg > 997:
        base_dmg = 997
    base_dmg += 2

    modified_dmg = base_dmg
    
    if stab:
        modified_dmg += base_dmg // 2
    
    for type in defender_types:
        if type in CHART[attack_type]:
            if CHART[attack_type][type] == 0:
                return 0
            elif CHART[attack_type][type] == 0.5:
                modified_dmg *= 5
                modified_dmg //= 10
            elif CHART[attack_type][type] == 2:
                modified_dmg *= 20
                modified_dmg //= 10
            else:
                modified_dmg *= 10
                modified_dmg //= 10

    if modified_dmg <= 1:
        return 1
    
    random_factor = random.randint(217, 255)
    modified_dmg *= random_factor
    modified_dmg //= 255
    
    if critical:
        modified_dmg *= 2
    return modified_dmg

def calculate_critical_hit(user_speed, direhitFocusEnergy, critHitRatio): # direhitFocusEnergy is a boolean, and im fixing it from the original where it reduces instead of increases
    if direhitFocusEnergy:
        crit_roll = user_speed / 2 * 2 * critHitRatio
    else:
        crit_roll = user_speed / 2 * 0.5 * critHitRatio

    if crit_roll > 255:
        crit_roll = 255

    return random.randint(0, 255) < crit_roll

def calculate_accuracy(accuracy, user_accuracy_stage, target_evasion_stage, target_invincible=False):
    if not target_invincible:
        stage_multipliers = [3/9, 3/8, 3/7, 3/6, 3/5, 3/4, 3/3, 4/3, 5/3, 6/3, 7/3, 8/3, 9/3]
        
        user_accuracy_stage = max(-6, min(6, user_accuracy_stage))
        target_evasion_stage = max(-6, min(6, target_evasion_stage))
        
        accuracy_multiplier = stage_multipliers[user_accuracy_stage + 6]
        evasion_multiplier = stage_multipliers[target_evasion_stage + 6]
        
        final_accuracy = accuracy * (accuracy_multiplier / evasion_multiplier)
        
        return max(0, min(100, final_accuracy))
    return 0

def stab_check(move_type, user_types):
    return move_type in user_types

def check_effectiveness(move_type, target):
    final_effectiveness = 1
    for type in target.types:
        if type is None:
            continue
        try:
            if CHART[move_type.lower()][type.lower()] == 0:
                final_effectiveness *= 0
            elif CHART[move_type.lower()][type.lower()] == 0.5:
                final_effectiveness *= 0.5
            elif CHART[move_type.lower()][type.lower()] == 2:
                final_effectiveness *= 2
        except KeyError:
            # If the type isn't in the chart, it's neutral
            pass

    if final_effectiveness == 0:
        return "It had no effect..."
    elif final_effectiveness == 0.5:
        return "It's not very effective..."
    elif final_effectiveness == 2:
        return "It's super effective!"

def apply_stat_change(target, stat, change, enemy=False):
    """Apply changes to stats. Stat stages range from -6 to 6."""
    stat_map = {
        "attack": "atk_stage",
        "defense": "defense_stage",
        "spatk": "spatk_stage",
        "spdef": "spdef_stage",
        "speed": "speed_stage",
        "accuracy": "accuracy_stage",
        "evasion": "evasion_stage"
    }
    
    stat_stage = stat_map.get(stat)
    if stat_stage and "mist" not in target.owner_reference.field_move:
        current_stage = getattr(target, stat_stage)
        
        # Check if the change would exceed the limit
        if (change > 0 and current_stage >= 6) or (change < 0 and current_stage <= -6):
            return "But it failed!"
        
        new_stage = current_stage + change
        new_stage = max(-6, min(new_stage, 6))  # Clamps between -6 and 6
        setattr(target, stat_stage, new_stage)

        return f"{'Enemy ' if enemy else ''}{target.nickname}'s\n{stat} {'rose' if change > 0 else 'fell'}!"
    
    return None

def apply_move_effect(move, user, target, enemy, stat_changes=None, stat_target=None, 
                      status_change=None, vol_status_change=None, status_target=None, 
                      vol_status_target=None, dot_turns=None, damage_override=None, 
                      self_damage=None, target_invincible=None, additional_multiplier=1):

    return_messages = []

    # Reduce PP
    move.curr_pp -= 1
    
    # Ensure invincibility logic is handled
    if target_invincible is None:
        target_invincible = target.invincible

    # **Full Paralysis Check (25% Chance)**
    if user.status == "paralyzed" and random.randint(1, 100) <= 25:
        return_messages.append(f"{'Enemy ' if enemy else ''}{user.nickname} is\nfully paralyzed!")
        return return_messages, None  # Move fails due to full paralysis

    # Check if the move deals damage
    damage = None  # Initialize damage variable
    if move.power != 0 or damage_override is not None:
        # Accuracy check
        if random.randint(0, 100) < calculate_accuracy(move.accuracy, user.accuracy_stage, target.evasion_stage, target_invincible):
            
            # Determine critical hit
            crit = calculate_critical_hit(user.speed, user.crit_boost, 4 if move.crit_buff else 0.5)
            
            # Calculate damage
            if damage_override is not None:
                damage = damage_override
            else:
                damage = calculate_damage(user.level, move.type, move.category, target.types, 
                                          user.spatk, user.spatk_stage, target.spdef, target.spdef_stage, 
                                          move.power, stab_check(move.type, user.types), crit, 
                                          "reflect" in user.owner_reference.field_move, 
                                          "lightscreen" in user.owner_reference.field_move) * additional_multiplier
            
            # Apply damage
            target.pending_hp -= damage  # Ensure this modifies the correct target object
            return_messages.append(f"{'Enemy ' if enemy else ''}{user.nickname}\nused {move.name.upper()}!")

            if crit:
                return_messages.append("Critical hit!")

            # Apply recoil damage (if any)
            if self_damage:
                user.pending_hp -= self_damage
                return_messages.append(f"{'Enemy ' if enemy else ''}{user.nickname} took recoil damage!")

            # Apply damage over time (DoT) effect
            if dot_turns:
                target.dot_turns = dot_turns

        else:
            return_messages.append(f"{'Enemy ' if enemy else ''}{user.nickname}'s attack missed!")

    else:
        return_messages.append(f"{'Enemy ' if enemy else ''}{user.nickname}\nused {move.name.upper()}!")

    # Apply stat changes (if any)
    if stat_changes:
        for stat, change in stat_changes.items():
            stat_message = apply_stat_change(stat_target, stat, change, stat_target == target)
            if stat_message:
                return_messages.append(stat_message)

    # Apply status effect (if any)
    if status_change and status_target:
        status_name = next(iter(status_change))
        if getattr(status_target, status_name, None) is None:
            setattr(status_target, status_name, True)
            return_messages.append(f"{'Enemy ' if enemy else ''}{status_target.nickname} is now {status_name.upper()}!")

    # Apply volatile status (if any)
    if vol_status_change and vol_status_target:
        vol_status_name = next(iter(vol_status_change))
        if vol_status_name not in vol_status_target.vol_status:
            vol_status_target.vol_status.append(vol_status_name)
            return_messages.append(f"{'Enemy ' if enemy else ''}{vol_status_target.nickname} is now affected by {vol_status_name}!")

    # Check effectiveness
    effectiveness_message = check_effectiveness(move.type, target)
    return_messages.append(effectiveness_message)

    return return_messages, damage  # Damage is now always returned properly


class Acid(Move):
    def __init__(self):
        super().__init__(name="Acid", type="poison", category="special", power=40, accuracy=100, pp=30)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 77:
            return apply_move_effect(self, user, target, enemy, stat_changes={'defense': -1}, stat_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Acidarmor(Move):
    def __init__(self):
        super().__init__(name="Acid Armor", type="poison", category="status", power=0, accuracy=0, pp=20)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, stat_changes={'defense': 2}, stat_target=user)[0]

class Agility(Move):
    def __init__(self):
        super().__init__(name="Agility", type="psychic", category="status", power=0, accuracy=0, pp=30)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, stat_changes={'speed': 2}, stat_target=user)[0]

class Amnesia(Move):
    def __init__(self):
        super().__init__(name="Amnesia", type="psychic", category="status", power=0, accuracy=0, pp=20)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, stat_changes={'spdef': 2}, stat_target=user)[0]

class Aurorabeam(Move):
    def __init__(self):
        super().__init__(name="Aurora Beam", type="ice", category="special", power=65, accuracy=100, pp=20)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 77:
            return apply_move_effect(self, user, target, enemy, stat_changes={'attack': -1}, stat_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Barrage(Move):
    def __init__(self):
        super().__init__(name="Barrage", type="normal", category="physical", power=15, accuracy=85, pp=20)

    def effect(self, user, target, enemy):
        hits = random.randint(2, 5)
        final = []
        for i in range(hits):
            final.append(apply_move_effect(self, user, target, enemy)[0])
        return final

class Barrier(Move):
    def __init__(self):
        super().__init__(name="Barrier", type="psychic", category="status", power=0, accuracy=0, pp=20)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, stat_changes={'defense': 2}, stat_target=user)[0]

class Bide(Move):
    def __init__(self):
        super().__init__(name="Bide", type="normal", category="physical", power=0, accuracy=0, pp=10)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, vol_status_change={'bide': random.randint(2,3)}, vol_status_target=user)[0]
    
    def effect_end(self, user, target, enemy):
        msgs, dmg = apply_move_effect(self, user, target, enemy, damage_override=user.collected_dmg * 2)
        if dmg == 0:
            return [f"{"Enemy " if enemy is True else ""}{user.nickname} unleashed energy!", "But it failed!"]
        else:
            return msgs

class Bind(Move):
    def __init__(self):
        super().__init__(name="Bind", type="normal", category="physical", power=15, accuracy=85, pp=20)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, vol_status_change={'bind': random.randint(4, 5)}, vol_status_target=target)[0]

class Bite(Move):
    def __init__(self):
        super().__init__(name="Bite", type="dark", category="physical", power=60, accuracy=100, pp=25)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 77:
            return apply_move_effect(self, user, target, enemy, status_change={'flinch': True}, status_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Blizzard(Move):
    def __init__(self):
        super().__init__(name="Blizzard", type="ice", category="special", power=110, accuracy=70, pp=5)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 77:
            return apply_move_effect(self, user, target, enemy, status_change={'frozen': True}, status_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Bodyslam(Move):
    def __init__(self):
        super().__init__(name="Body Slam", type="normal", category="physical", power=85, accuracy=100, pp=15)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 77:
            return apply_move_effect(self, user, target, enemy, status_change={'paralyzed': True}, status_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Boneclub(Move):
    def __init__(self):
        super().__init__(name="Bone Club", type="ground", category="physical", power=65, accuracy=85, pp=20)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 33:
            return apply_move_effect(self, user, target, enemy, status_change={'flinch': True}, status_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Bonemerang(Move):
    def __init__(self):
        super().__init__(name="Bonemerang", type="ground", category="physical", power=50, accuracy=90, pp=10)

    def effect(self, user, target, enemy):
        hits = 2
        final = []
        for i in range(hits):
            final.append(apply_move_effect(self, user, target, enemy)[0])
        return final

class Bubble(Move):
    def __init__(self):
        super().__init__(name="Bubble", type="water", category="special", power=40, accuracy=100, pp=30)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 33:
            return apply_move_effect(self, user, target, enemy, stat_changes={'speed': -1}, stat_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Bubblebeam(Move):
    def __init__(self):
        super().__init__(name="Bubble Beam", type="water", category="special", power=65, accuracy=100, pp=20)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 33:
            return apply_move_effect(self, user, target, enemy, stat_changes={'speed': -1}, stat_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Clamp(Move):
    def __init__(self):
        super().__init__(name="Clamp", type="water", category="physical", power=35, accuracy=85, pp=15)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, vol_status_change={'clamp': random.choice([2, 2, 2, 3, 3, 3, 4, 5])}, vol_status_target=target, dot_turns=rand)[0]

class Cometpunch(Move):
    def __init__(self):
        super().__init__(name="Comet Punch", type="normal", category="physical", power=18, accuracy=85, pp=15)

    def effect(self, user, target, enemy):
        hits = random.randint(2, 5)
        final = []
        for i in range(hits):
            final.append(apply_move_effect(self, user, target, enemy)[0])
        return final

class Confuseray(Move):
    def __init__(self):
        super().__init__(name="Confuse Ray", type="ghost", category="status", power=0, accuracy=100, pp=10)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, vol_status_change={'confusion': random.randint(1, 4)}, vol_status_target=target)[0]

class Confusion(Move):
    def __init__(self):
        super().__init__(name="Confusion", type="psychic", category="special", power=50, accuracy=100, pp=25)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 33:
            return apply_move_effect(self, user, target, enemy, vol_status_change={'confusion': random.randint(1, 4)}, vol_status_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Constrict(Move):
    def __init__(self):
        super().__init__(name="Constrict", type="normal", category="physical", power=10, accuracy=100, pp=35)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 77:
            return apply_move_effect(self, user, target, enemy, stat_changes={'speed': -1}, stat_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Conversion(Move):
    def __init__(self):
        super().__init__(name="Conversion", type="normal", category="status", power=0, accuracy=0, pp=30)

    def effect(self, user, target, enemy):
        user.types = target.types
        # weird edgecase move, just gonna return the correct message
        if enemy:
            return [f"Enemy {user.nickname} transformed into the {target.types[0]} type!"]
        return [f"{user.nickname} transformed into the {target.types[0]} type!"]

class Counter(Move):
    def __init__(self):
        super().__init__(name="Counter", type="fighting", category="physical", power=0, accuracy=100, pp=20)

    def effect(self, user, target, enemy):
        if user.collected_dmg > 0:
            return apply_move_effect(self, user, target, enemy, damage_override=user.collected_dmg * 2)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Crabhammer(Move):
    def __init__(self):
        super().__init__(name="Crabhammer", type="water", category="physical", power=100, accuracy=90, pp=10)
        self.crit_buff = True

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 33:
            return apply_move_effect(self, user, target, enemy, stat_changes={'defense': -1}, stat_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Cut(Move):
    def __init__(self):
        super().__init__(name="Cut", type="normal", category="physical", power=50, accuracy=95, pp=30)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy)[0]

class Defensecurl(Move):
    def __init__(self):
        super().__init__(name="Defense Curl", type="normal", category="status", power=0, accuracy=0, pp=40)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, stat_changes={'defense': 1}, stat_target=user)[0]

class Dig(Move):
    def __init__(self):
        super().__init__(name="Dig", type="ground", category="physical", power=80, accuracy=100, pp=10)

    def effect(self, user, target, enemy):
        user.vol_status.append('dig')
        user.invincible = True
        return [f"{"Enemy " if enemy is True else ""}{user.nickname} burrowed underground!"]
    
    def effect_end(self, user, target, enemy):
        user.vol_status.remove('dig')
        user.invincible = False
        return apply_move_effect(self, user, target, enemy, target_invincible=False)[0]

class Disable(Move):
    def __init__(self):
        super().__init__(name="Disable", type="normal", category="status", power=0, accuracy=100, pp=20)

    def effect(self, user, target, enemy):
        pass # once the actual battle system is implemented, this will be done

class Dizzypunch(Move):
    def __init__(self):
        super().__init__(name="Dizzy Punch", type="normal", category="physical", power=70, accuracy=100, pp=10)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 33:
            return apply_move_effect(self, user, target, enemy, status_change={'confusion': True}, status_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Doublekick(Move):
    def __init__(self):
        super().__init__(name="Double Kick", type="fighting", category="physical", power=30, accuracy=100, pp=30)

    def effect(self, user, target, enemy):
        hits = 2
        final = []
        for i in range(hits):
            final.append(apply_move_effect(self, user, target, enemy)[0])
        return final

class Doubleslap(Move):
    def __init__(self):
        super().__init__(name="Double Slap", type="normal", category="physical", power=15, accuracy=85, pp=10)

    def effect(self, user, target, enemy):
        hits = random.randint(2, 5)
        final = []
        for i in range(hits):
            final.append(apply_move_effect(self, user, target, enemy)[0])
        return final

class Doubleteam(Move):
    def __init__(self):
        super().__init__(name="Double Team", type="normal", category="status", power=0, accuracy=0, pp=15)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, stat_changes={'evasion': 1}, stat_target=user)[0]

class Doubleedge(Move):
    def __init__(self):
        super().__init__(name="Double-Edge", type="normal", category="physical", power=120, accuracy=100, pp=15)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, self_damage=user.curr_hp // 3)[0]

class Dragonrage(Move):
    def __init__(self):
        super().__init__(name="Dragon Rage", type="dragon", category="special", power=0, accuracy=100, pp=10)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, damage_override=40)[0]

class Dreameater(Move):
    def __init__(self):
        super().__init__(name="Dream Eater", type="psychic", category="special", power=100, accuracy=100, pp=15)

    def effect(self, user, target, enemy):
        if 'sleep' in target.vol_status:
            msgs, dmg = apply_move_effect(self, user, target, enemy)
            user.pending_hp += dmg // 2
            return msgs
        else:
            return [f"{"Enemy" if enemy is True else ""}{target.nickname}\nused {self.name}!", "But it failed!"]

class Drillpeck(Move):
    def __init__(self):
        super().__init__(name="Drill Peck", type="flying", category="physical", power=80, accuracy=100, pp=20)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy)[0]

class Earthquake(Move):
    def __init__(self):
        super().__init__(name="Earthquake", type="ground", category="physical", power=100, accuracy=100, pp=10)

    def effect(self, user, target, enemy):
        if target.vol_status == 'dig':
            return apply_move_effect(self, user, target, enemy, target_invincible=False, additional_multiplier=2)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]

class Eggbomb(Move):
    def __init__(self):
        super().__init__(name="Egg Bomb", type="normal", category="physical", power=100, accuracy=75, pp=10)

class Ember(Move):
    def __init__(self):
        super().__init__(name="Ember", type="fire", category="special", power=40, accuracy=100, pp=25)

    def effect(self, user, target, enemy):
        if random.randint(0, 255) < 77:
            return apply_move_effect(self, user, target, enemy, status_change={'burned': True}, status_target=target)[0]
        else:
            return apply_move_effect(self, user, target, enemy)[0]
        

class Explosion(Move):
    def __init__(self):
        super().__init__(name="Explosion", type="normal", category="physical", power=250, accuracy=100, pp=5)

class Fireblast(Move):
    def __init__(self):
        super().__init__(name="Fire Blast", type="fire", category="special", power=110, accuracy=85, pp=5)

class Firepunch(Move):
    def __init__(self):
        super().__init__(name="Fire Punch", type="fire", category="physical", power=75, accuracy=100, pp=15)

class Firespin(Move):
    def __init__(self):
        super().__init__(name="Fire Spin", type="fire", category="special", power=35, accuracy=85, pp=15)

class Fissure(Move):
    def __init__(self):
        super().__init__(name="Fissure", type="ground", category="physical", power=0, accuracy=30, pp=5)

class Flamethrower(Move):
    def __init__(self):
        super().__init__(name="Flamethrower", type="fire", category="special", power=90, accuracy=100, pp=15)

class Flash(Move):
    def __init__(self):
        super().__init__(name="Flash", type="normal", category="status", power=0, accuracy=100, 
pp=20)

class Fly(Move):
    def __init__(self):
        super().__init__(name="Fly", type="flying", category="physical", power=90, accuracy=95, pp=15)

    def effect(self, user, target, enemy):
        user.vol_status.append('fly')
        user.invincible = True
        return [f"{"Enemy " if enemy is True else ""}{user.nickname} flew up high!"]
    
    def effect_end(self, user, target, enemy):
        user.vol_status.remove('fly')
        user.invincible = False
        return apply_move_effect(self, user, target, enemy, target_invincible=False)[0]

class Focusenergy(Move):
    def __init__(self):
        super().__init__(name="Focus Energy", type="normal", category="status", power=0, accuracy=0, pp=30)

class Furyattack(Move):
    def __init__(self):
        super().__init__(name="Fury Attack", type="normal", category="physical", power=15, accuracy=85, pp=20)

class Furyswipes(Move):
    def __init__(self):
        super().__init__(name="Fury Swipes", type="normal", category="physical", power=18, accuracy=80, pp=15)

class Glare(Move):
    def __init__(self):
        super().__init__(name="Glare", type="normal", category="status", power=0, accuracy=100, 
pp=30)

class Growl(Move):
    def __init__(self):
        super().__init__(name="Growl", type="normal", category="status", power=0, accuracy=100, pp=40)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, stat_changes={'attack': -1}, stat_target=target)[0]

class Growth(Move):
    def __init__(self):
        super().__init__(name="Growth", type="normal", category="status", power=0, accuracy=0, pp=20)

class Guillotine(Move):
    def __init__(self):
        super().__init__(name="Guillotine", type="normal", category="physical", power=0, accuracy=30, pp=5)

class Gust(Move):
    def __init__(self):
        super().__init__(name="Gust", type="flying", category="special", power=40, accuracy=100, pp=35)

class Harden(Move):
    def __init__(self):
        super().__init__(name="Harden", type="normal", category="status", power=0, accuracy=0, pp=30)

class Haze(Move):
    def __init__(self):
        super().__init__(name="Haze", type="ice", category="status", power=0, accuracy=0, pp=30)
class Headbutt(Move):
    def __init__(self):
        super().__init__(name="Headbutt", type="normal", category="physical", power=70, accuracy=100, pp=15)

class Hijumpkick(Move):
    def __init__(self):
        super().__init__(name="Hi Jump Kick", type="fighting", category="physical", power=130, accuracy=90, pp=10)

class Hornattack(Move):
    def __init__(self):
        super().__init__(name="Horn Attack", type="normal", category="physical", power=65, accuracy=100, pp=25)

class Horndrill(Move):
    def __init__(self):
        super().__init__(name="Horn Drill", type="normal", category="physical", power=0, accuracy=30, pp=5)

class Hydropump(Move):
    def __init__(self):
        super().__init__(name="Hydro Pump", type="water", category="special", power=110, accuracy=80, pp=5)

class Hyperbeam(Move):
    def __init__(self):
        super().__init__(name="Hyper Beam", type="normal", category="special", power=150, accuracy=90, pp=5)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, vol_status_change={'recharge': 1}, vol_status_target=user)[0]

class Hyperfang(Move):
    def __init__(self):
        super().__init__(name="Hyper Fang", type="normal", category="physical", power=80, accuracy=90, pp=15)

class Hypnosis(Move):
    def __init__(self):
        super().__init__(name="Hypnosis", type="psychic", category="status", power=0, accuracy=60, pp=20)

class Icebeam(Move):
    def __init__(self):
        super().__init__(name="Ice Beam", type="ice", category="special", power=90, accuracy=100, pp=10)

class Icepunch(Move):
    def __init__(self):
        super().__init__(name="Ice Punch", type="ice", category="physical", power=75, accuracy=100, pp=15)

class Jumpkick(Move):
    def __init__(self):
        super().__init__(name="Jump Kick", type="fighting", category="physical", power=100, accuracy=95, pp=10)

class Karatechop(Move):
    def __init__(self):
        super().__init__(name="Karate Chop", type="fighting", category="physical", power=50, accuracy=100, pp=25)

class Kinesis(Move):
    def __init__(self):
        super().__init__(name="Kinesis", type="psychic", category="status", power=0, accuracy=80, pp=15)

class Leechlife(Move):
    def __init__(self):
        super().__init__(name="Leech Life", type="bug", category="physical", power=80, accuracy=100, pp=10)

class Leechseed(Move):
    def __init__(self):
        super().__init__(name="Leech Seed", type="grass", category="status", power=0, accuracy=90, pp=10)

class Leer(Move):
    def __init__(self):
        super().__init__(name="Leer", type="normal", category="status", power=0, accuracy=100, pp=30)

class Lick(Move):
    def __init__(self):
        super().__init__(name="Lick", type="ghost", category="physical", power=30, accuracy=100, pp=30)

class Lightscreen(Move):
    def __init__(self):
        super().__init__(name="Light Screen", type="psychic", category="status", power=0, accuracy=0, pp=30)

    def effect(self, user, target, enemy):
        user.owner_reference.field_move.append('lightscreen')
        user.owner_reference.field_move_turns.append(5)
        return apply_move_effect(self, user, target, enemy)[0]

class Lovelykiss(Move):
    def __init__(self):
        super().__init__(name="Lovely Kiss", type="normal", category="status", power=0, accuracy=75, pp=10)

class Lowkick(Move):
    def __init__(self):
        super().__init__(name="Low Kick", type="fighting", category="physical", power=0, accuracy=100, pp=20)

class Meditate(Move):
    def __init__(self):
        super().__init__(name="Meditate", type="psychic", category="status", power=0, accuracy=0, pp=40)

class Megadrain(Move):
    def __init__(self):
        super().__init__(name="Mega Drain", type="grass", category="special", power=40, accuracy=100, pp=15)

class Megakick(Move):
    def __init__(self):
        super().__init__(name="Mega Kick", type="normal", category="physical", power=120, accuracy=75, pp=5)

class Megapunch(Move):
    def __init__(self):
        super().__init__(name="Mega Punch", type="normal", category="physical", power=80, accuracy=85, pp=20)

class Metronome(Move):
    def __init__(self):
        super().__init__(name="Metronome", type="normal", category="status", power=0, accuracy=0, pp=10)

class Mimic(Move):
    def __init__(self):
        super().__init__(name="Mimic", type="normal", category="status", power=0, accuracy=0, pp=10)

class Minimize(Move):
    def __init__(self):
        super().__init__(name="Minimize", type="normal", category="status", power=0, accuracy=0, pp=10)

class Mirrormove(Move):
    def __init__(self):
        super().__init__(name="Mirror Move", type="flying", category="status", power=0, accuracy=0, pp=20)

class Mist(Move):
    def __init__(self):
        super().__init__(name="Mist", type="ice", category="status", power=0, accuracy=0, pp=30)

    def effect(self, user, target, enemy):
        user.owner_reference.field_move.append('mist')
        user.owner_reference.field_move_turns.append(5)
        return apply_move_effect(self, user, target, enemy)[0]
    
class Nightshade(Move):
    def __init__(self):
        super().__init__(name="Night Shade", type="ghost", category="special", power=0, accuracy=100, pp=15)

class Payday(Move):
    def __init__(self):
        super().__init__(name="Pay Day", type="normal", category="physical", power=40, accuracy=100, pp=20)

class Peck(Move):
    def __init__(self):
        super().__init__(name="Peck", type="flying", category="physical", power=35, accuracy=100, pp=35)

class Petaldance(Move):
    def __init__(self):
        super().__init__(name="Petal Dance", type="grass", category="special", power=120, accuracy=100, pp=10)

class Pinmissile(Move):
    def __init__(self):
        super().__init__(name="Pin Missile", type="bug", category="physical", power=25, accuracy=95, pp=20)

class Poisongas(Move):
    def __init__(self):
        super().__init__(name="Poison Gas", type="poison", category="status", power=0, accuracy=90, pp=40)

class Poisonpowder(Move):
    def __init__(self):
        super().__init__(name="Poison Powder", type="poison", category="status", power=0, accuracy=75, pp=35)

class Poisonsting(Move):
    def __init__(self):
        super().__init__(name="Poison Sting", type="poison", category="physical", power=15, accuracy=100, pp=35)

class Pound(Move):
    def __init__(self):
        super().__init__(name="Pound", type="normal", category="physical", power=40, accuracy=100, pp=35)

class Psybeam(Move):
    def __init__(self):
        super().__init__(name="Psybeam", type="psychic", category="special", power=65, accuracy=100, pp=20)

class Psychic(Move):
    def __init__(self):
        super().__init__(name="Psychic", type="psychic", category="special", power=90, accuracy=100, pp=10)

class Psywave(Move):
    def __init__(self):
        super().__init__(name="Psywave", type="psychic", category="special", power=0, accuracy=100, pp=15)

class Quickattack(Move):
    def __init__(self):
        super().__init__(name="Quick Attack", type="normal", category="physical", power=40, accuracy=100, pp=30)
        self.tags.append('priority')

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy)[0]

class Rage(Move):
    def __init__(self):
        super().__init__(name="Rage", type="normal", category="physical", power=20, accuracy=100, pp=20)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, vol_status_change={'rage': 1}, vol_status_target=user, stat_changes={'attack': 1}, stat_target=user)[0]

class Razorleaf(Move):
    def __init__(self):
        super().__init__(name="Razor Leaf", type="grass", category="physical", power=55, accuracy=95, pp=25)

class Razorwind(Move):
    def __init__(self):
        super().__init__(name="Razor Wind", type="normal", category="special", power=80, accuracy=100, pp=10)

class Recover(Move):
    def __init__(self):
        super().__init__(name="Recover", type="normal", category="status", power=0, accuracy=0, 
pp=5)

class Reflect(Move):
    def __init__(self):
        super().__init__(name="Reflect", type="psychic", category="status", power=0, accuracy=0, pp=20)

    def effect(self, user, target, enemy):
        user.owner_reference.field_move.append('reflect')
        user.owner_reference.field_move_turns.append(5)
        return apply_move_effect(self, user, target, enemy)[0]

class Rest(Move):
    def __init__(self):
        super().__init__(name="Rest", type="psychic", category="status", power=0, accuracy=0, pp=5)

    def effect(self, user, target, enemy):
        user.pending_hp = user.max_hp
        user.status = None
        user.turn_count = 2
        return apply_move_effect(self, user, target, enemy, vol_status_change={'rest': 2}, vol_status_target=user)[0]

class Roar(Move):
    def __init__(self):
        super().__init__(name="Roar", type="normal", category="status", power=0, accuracy=0, pp=20)

class Rockslide(Move):
    def __init__(self):
        super().__init__(name="Rock Slide", type="rock", category="physical", power=75, accuracy=90, pp=10)

class Rockthrow(Move):
    def __init__(self):
        super().__init__(name="Rock Throw", type="rock", category="physical", power=50, accuracy=90, pp=15)

class Rollingkick(Move):
    def __init__(self):
        super().__init__(name="Rolling Kick", type="fighting", category="physical", power=60, accuracy=85, pp=15)

class Sandattack(Move):
    def __init__(self):
        super().__init__(name="Sand Attack", type="ground", category="status", power=0, accuracy=100, pp=15)

class Scratch(Move):
    def __init__(self):
        super().__init__(name="Scratch", type="normal", category="physical", power=40, accuracy=100, pp=35)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy)[0]

class Screech(Move):
    def __init__(self):
        super().__init__(name="Screech", type="normal", category="status", power=0, accuracy=85, pp=40)

class Seismictoss(Move):
    def __init__(self):
        super().__init__(name="Seismic Toss", type="fighting", category="physical", power=0, accuracy=100, pp=20)

class Selfdestruct(Move):
    def __init__(self):
        super().__init__(name="Self-Destruct", type="normal", category="physical", power=200, accuracy=100, pp=5)

class Sharpen(Move):
    def __init__(self):
        super().__init__(name="Sharpen", type="normal", category="status", power=0, accuracy=0, 
pp=30)

class Sing(Move):
    def __init__(self):
        super().__init__(name="Sing", type="normal", category="status", power=0, accuracy=55, pp=15)

class Skullbash(Move):
    def __init__(self):
        super().__init__(name="Skull Bash", type="normal", category="physical", power=130, accuracy=100, pp=10)

class Skyattack(Move):
    def __init__(self):
        super().__init__(name="Sky Attack", type="flying", category="physical", power=140, accuracy=90, pp=5)

class Slam(Move):
    def __init__(self):
        super().__init__(name="Slam", type="normal", category="physical", power=80, accuracy=75, pp=20)

class Slash(Move):
    def __init__(self):
        super().__init__(name="Slash", type="normal", category="physical", power=70, accuracy=100, pp=20)

class Sleeppowder(Move):
    def __init__(self):
        super().__init__(name="Sleep Powder", type="grass", category="status", power=0, accuracy=75, pp=15)

class Sludge(Move):
    def __init__(self):
        super().__init__(name="Sludge", type="poison", category="special", power=65, accuracy=100, pp=20)

class Smog(Move):
    def __init__(self):
        super().__init__(name="Smog", type="poison", category="special", power=30, accuracy=70, 
pp=20)

class Smokescreen(Move):
    def __init__(self):
        super().__init__(name="Smokescreen", type="normal", category="status", power=0, accuracy=100, pp=20)

class Softboiled(Move):
    def __init__(self):
        super().__init__(name="Soft-Boiled", type="normal", category="status", power=0, accuracy=0, pp=5)

class Solarbeam(Move):
    def __init__(self):
        super().__init__(name="Solar Beam", type="grass", category="special", power=120, accuracy=100, pp=10)

class Sonicboom(Move):
    def __init__(self):
        super().__init__(name="Sonic Boom", type="normal", category="special", power=0, accuracy=90, pp=20)

class Spikecannon(Move):
    def __init__(self):
        super().__init__(name="Spike Cannon", type="normal", category="physical", power=20, accuracy=100, pp=15)

class Splash(Move):
    def __init__(self):
        super().__init__(name="Splash", type="normal", category="status", power=0, accuracy=0, pp=40)

class Spore(Move):
    def __init__(self):
        super().__init__(name="Spore", type="grass", category="status", power=0, accuracy=100, pp=15)

class Stomp(Move):
    def __init__(self):
        super().__init__(name="Stomp", type="normal", category="physical", power=65, accuracy=100, pp=20)

class Strength(Move):
    def __init__(self):
        super().__init__(name="Strength", type="normal", category="physical", power=80, accuracy=100, pp=15)

class Stringshot(Move):
    def __init__(self):
        super().__init__(name="String Shot", type="bug", category="status", power=0, accuracy=95, pp=40)

class Struggle(Move):
    def __init__(self):
        super().__init__(name="Struggle", type="normal", category="physical", power=50, accuracy=0, pp=0)

class Stunspore(Move):
    def __init__(self):
        super().__init__(name="Stun Spore", type="grass", category="status", power=0, accuracy=75, pp=30)

class Submission(Move):
    def __init__(self):
        super().__init__(name="Submission", type="fighting", category="physical", power=80, accuracy=80, pp=20)

class Substitute(Move):
    def __init__(self):
        super().__init__(name="Substitute", type="normal", category="status", power=0, accuracy=0, pp=10)

class Superfang(Move):
    def __init__(self):
        super().__init__(name="Super Fang", type="normal", category="physical", power=0, accuracy=90, pp=10)

class Supersonic(Move):
    def __init__(self):
        super().__init__(name="Supersonic", type="normal", category="status", power=0, accuracy=55, pp=20)

class Surf(Move):
    def __init__(self):
        super().__init__(name="Surf", type="water", category="special", power=90, accuracy=100, 
pp=15)

class Swift(Move):
    def __init__(self):
        super().__init__(name="Swift", type="normal", category="special", power=60, accuracy=0, 
pp=20)

class Swordsdance(Move):
    def __init__(self):
        super().__init__(name="Swords Dance", type="normal", category="status", power=0, accuracy=0, pp=20)

class Tackle(Move):
    def __init__(self):
        super().__init__(name="Tackle", type="normal", category="physical", power=40, accuracy=100, pp=35)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy)[0]

class Tailwhip(Move):
    def __init__(self):
        super().__init__(name="Tail Whip", type="normal", category="status", power=0, accuracy=100, pp=30)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy, stat_changes={'defense': -1}, stat_target=target)[0]

class Takedown(Move):
    def __init__(self):
        super().__init__(name="Take Down", type="normal", category="physical", power=90, accuracy=85, pp=20)

class Teleport(Move):
    def __init__(self):
        super().__init__(name="Teleport", type="psychic", category="status", power=0, accuracy=0, pp=20)

class Thrash(Move):
    def __init__(self):
        super().__init__(name="Thrash", type="normal", category="physical", power=120, accuracy=100, pp=10)

class Thunder(Move):
    def __init__(self):
        super().__init__(name="Thunder", type="electric", category="special", power=110, accuracy=70, pp=10)

class Thunderpunch(Move):
    def __init__(self):
        super().__init__(name="Thunder Punch", type="electric", category="physical", power=75, accuracy=100, pp=15)

class Thundershock(Move):
    def __init__(self):
        super().__init__(name="Thunder Shock", type="electric", category="special", power=40, accuracy=100, pp=30)

class Thunderwave(Move):
    def __init__(self):
        super().__init__(name="Thunder Wave", type="electric", category="status", power=0, accuracy=90, pp=20)

class Thunderbolt(Move):
    def __init__(self):
        super().__init__(name="Thunderbolt", type="electric", category="special", power=90, accuracy=100, pp=15)

class Toxic(Move):
    def __init__(self):
        super().__init__(name="Toxic", type="poison", category="status", power=0, accuracy=90, pp=10)

class Transform(Move):
    def __init__(self):
        super().__init__(name="Transform", type="normal", category="status", power=0, accuracy=0, pp=10)

class Triattack(Move):
    def __init__(self):
        super().__init__(name="Tri Attack", type="normal", category="special", power=80, accuracy=100, pp=10)

class Twineedle(Move):
    def __init__(self):
        super().__init__(name="Twineedle", type="bug", category="physical", power=25, accuracy=100, pp=20)

class Vinewhip(Move):
    def __init__(self):
        super().__init__(name="Vine Whip", type="grass", category="physical", power=45, accuracy=100, pp=25)

class Vicegrip(Move):
    def __init__(self):
        super().__init__(name="ViceGrip", type="normal", category="physical", power=55, accuracy=100, pp=30)

class Watergun(Move):
    def __init__(self):
        super().__init__(name="Water Gun", type="water", category="special", power=40, accuracy=100, pp=25)

    def effect(self, user, target, enemy):
        return apply_move_effect(self, user, target, enemy)[0]

class Waterfall(Move):
    def __init__(self):
        super().__init__(name="Waterfall", type="water", category="physical", power=80, accuracy=100, pp=15)

class Whirlwind(Move):
    def __init__(self):
        super().__init__(name="Whirlwind", type="normal", category="status", power=0, accuracy=0, pp=20)

class Wingattack(Move):
    def __init__(self):
        super().__init__(name="Wing Attack", type="flying", category="physical", power=60, accuracy=100, pp=35)

class Withdraw(Move):
    def __init__(self):
        super().__init__(name="Withdraw", type="water", category="status", power=0, accuracy=0, 
pp=40)

class Wrap(Move):
    def __init__(self):
        super().__init__(name="Wrap", type="normal", category="physical", power=15, accuracy=90, pp=20)
