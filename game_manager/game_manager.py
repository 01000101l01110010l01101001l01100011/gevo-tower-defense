# pygame imports
from pygame.sprite import RenderUpdates
from pygame.time import Clock
from pygame import event, QUIT, quit, locals, display, SCALED, font
from pygame.transform import scale

# python imports
import logging


# --- PROJECT IMPORTS ---

# config
from config.settings.enemies import *
from config.settings.towers import *
from config.settings.general_config import Economy, Game, Difficulty, Wave_difficulty, Window, Colors

# objects
from game_objects.enemies.enemy_object import EnemyObject
from game_objects.towers.tower_object import TowerObject
from game_objects.towers.tower_type import TowerType
from game_objects.towers.projectile_tower import ProjectileTower
from game_objects.towers.splash_tower import SplashTower

# other
from graphics_manager.graphics_manager import GraphicsManager
from game_manager import wave_maker, spawn_delay
from level_converter.level_converter import convert_level
from level_generator.level_generator import generate_level

# texture loader
from texture_loader.texture_loader import TextureLoader

# gui
from gui.gui import Gui

class GameManager:
    """ The ultimate class that controls everything everywhere """
    def __init__(self) -> None:
        self.screen = None
        self.textures = {}
        self.gui = None

        self.objects = RenderUpdates()

        self.projectiles = RenderUpdates()
        self.towers = RenderUpdates()
        self.living_enemies = RenderUpdates()
        self.not_spawned_enemies = []
        self.effects = RenderUpdates()


        self.moving_objects = RenderUpdates()
        self.static_objects = RenderUpdates()

        self.ui = RenderUpdates()

        self.coins:int = Economy.STARTING_MONEY
        self.lives:int = Economy.STARTING_LIVES
        self.level:int = Game.START_LEVEL
        self.wave:int = Game.START_WAVE

        self.converted_level = []


        self.clock = Clock()

        self.running = True
        self.pause = False
        self.wave_running = False

#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#-------------------------------------- STARTER THINGS ------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------   

    def create_screen(self) -> None:
        """ Create screen"""
        self.screen = display.set_mode((Window.WIDTH, Window.HEIGHT), SCALED)
        self.screen.fill(Colors.BACKGROUND)

    def init_things(self) -> None:
        """ Initialize some things"""
        font.init()
        self.gui = Gui()

    def initialize(self):
        """ Initialize game"""
        generate_level(self.level)
        self.load_textures()
        self.converted_level = convert_level(self.level)

#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#-------------------------------------- TEXTURES ------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
    def load_textures(self) -> None:
        """ Load all textures from texture_loader"""
        self.textures = TextureLoader().load_all_textures()
        logging.info(f"Loaded {len(self.textures)} textures")

#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#---------------------------------------- GUI ---------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
    def show_gui(self, screen) -> None:
        """ Show gui on screen"""
        self.gui.show_coins(screen, self.coins)
        self.gui.show_lives(screen, self.lives)
        self.gui.show_wave(screen, self.wave)
        self.gui.show_towers(screen, self.textures)


    def test_run(self) -> None:

        self.init_things()
        self.create_screen()
        self.initialize()

        self.show_map()
        self.show_gui(self.screen)


#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#---------------------------------------- SHOW MAP ----------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

    def show_map(self) -> None:
        """ Show map on screen"""
        for tile in self.converted_level:
            for pixel in range(len(self.converted_level[tile])):
                image = self.textures["game_objects"]["tiles"][tile][0]
                image = scale(image, (Tile.PIXEL_SIZE, Tile.PIXEL_SIZE))      
                sprite = self.converted_level[tile][pixel]
                self.screen.blit(image, sprite)  

# #------------------------------------------------------------------------------------------------------------
# #------------------------------------------------------------------------------------------------------------
# #-------------------------------------- HANDLE ENEMIES ------------------------------------------------------
# #------------------------------------------------------------------------------------------------------------
# #------------------------------------------------------------------------------------------------------------


    def get_start(self) -> tuple:
        """ Get start position from level"""
        logging.debug(f"Getting start position from level {self.level}")
        return self.converted_level["start"][0].x, self.converted_level["start"][0].y


    def wave_loader(self, level:Difficulty ,wave: int) -> list[EnemyObject]:
        """ Load wave from config and return a list of EnemyObjects. The wave is randomized"""
        logging.debug(f"Loading wave {wave}")

        wave_function = Wave_difficulty.waves_dict[level]
        number_of_enemies = int(wave_function(wave))    
        enemies = wave_maker.create_wave(number_of_enemies, wave)
        #name of enemies in a list

        enemy_objects = []
        x,y = self.get_start(self.level)

        for enemy_name in enemies:
            try:
                hp = enemy_dict[enemy_name].HEALTH
                size = enemy_dict[enemy_name].SIZE
                image = ... #TODO: image
                speed = enemy_dict[enemy_name].SPEED
                direction = ... #TODO: direction
                animation = ... #TODO: animation
                animation_index = ... #TODO: animation_index
                detectable = enemy_dict[enemy_name].DETECTABLE
                lvl = enemy_dict[enemy_name].START_LEVEL
            except KeyError:
                logging.debug(f"Enemy {enemy_name} is not in enemy_dict" + KeyError)
            
            enemy = EnemyObject(hp, x, y, size, size, image, speed, direction, animation, animation_index, detectable, lvl)
            enemy_objects.append(enemy)

            # Adding the enemy into groups
            self.not_spawned_enemies.append(enemy)

        logging.info(f"Loaded wave {wave} with {number_of_enemies} enemies")

        # EnemyObjects in a list
        return enemy_objects
        
    
    def spawn_enemy(self, frames:int, spawn_delay:int) -> None:
        """ Transfer enemy from not_spawned to living and moving groups in intervals. Called every frame"""
        if len(self.not_spawned_enemies) == 0:
            return 
        
        if frames % spawn_delay == 0:
            enemy = self.not_spawned_enemies.pop(0)

            self.living_enemies.add(enemy)
            self.moving_objects.add(enemy)

            logging.debug(f"Spawned enemy {enemy} with spawn delay {spawn_delay}")
            # Enemy is in living group and moving objects group --> One group will be drawn every frame
           

    def handle_enemy_hp(self) -> None:
        """ Check if enemy is dead and kill it"""

        for enemy in self.living_enemies:
            if enemy.hp <= 0:
                enemy.kill()
        
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------ HANDLE TOWERS ---------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

    def buy_tower(self, tower:TowerType, position:tuple) -> TowerObject:
        """ Buy tower if player has enough coins and create tower object and add it in static objects + towers group"""
        ### TODO zmwnit tohle at to tam neni napsane vicekrat

        if self.coins >= tower_dict[tower].PRICE:
            self.coins -= tower_dict[tower].PRICE
            if tower_dict[tower].TYPE == "projectile":
                x,y = position
                width = Tile.PIXEL_SIZE
                height = Tile.PIXEL_SIZE
                image = ... # TODO: image
                animation = ... # TODO: animation
                animation_index = ... # TODO: animation index
                damage = tower_dict[tower].DAMAGE
                reload_time = tower_dict[tower].RELOAD_TIME
                tower_type = tower
                projectile_animation = ... # TODO: animation
                projectile_animation_index = ... # TODO: animation index

                tower_object = ProjectileTower()#TODO počkat, než Jáchym mi dá pořadí argumentů

                self.static_objects.add(tower_object)
                self.towers.add(tower_object)
            elif tower_dict[tower].TYPE == "splash":
                x,y = position
                width = Tile.PIXEL_SIZE
                height = Tile.PIXEL_SIZE
                image = ... # TODO: image
                animation = ... # TODO: animation
                animation_index = ... # TODO: animation index
                damage = tower_dict[tower].DAMAGE
                reload_time = tower_dict[tower].RELOAD_TIME
                tower_type = tower
                projectile_animation = ... # TODO: animation
                projectile_animation_index = ... # TODO: animation index

                tower_object = SplashTower()#TODO počkat, než Jáchym mi dá pořadí argumentů

                self.static_objects.add(tower_object)
                self.towers.add(tower_object)
            else:
                logging.error(f"Cannot buy tower {tower} because it has unknown type")
            return True
        else:
            return False
        

        

#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------ IMPORTANT ---------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

    def handle_input(self):
        """ Handle input from user"""

        for event in event.get():
            if event.type == QUIT:
                quit()
            elif event.type == locals.K_ESCAPE:
                self.pause = not self.pause


    def update(self, frames) -> None:
        """ Update game state every frame"""

        if not self.wave_running:
            # Load wave
            wave = self.wave_loader(self.wave)
            self.add_enemies_to_group(wave)        
        # Spawn enemies in intervals
        self.spawn_enemy(frames, spawn_delay.spawn_delay(self.not_spawned_enemies[0], self.not_spawned_enemies[1]))


        self.handle_enemy_hp()
    

    def run(self) -> None:
        """ Main game loop"""

        frames = 0
        while self.running:
            self.clock.tick(Game.FPS)

            self.handle_input()

            if self.pause:
                continue

            frames += 1 #bezi kdzy neni pauza

            self.update()
    
    
