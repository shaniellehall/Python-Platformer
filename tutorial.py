import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Advanced Platformer Adventure")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

# Initialize mixer for better audio support
pygame.mixer.init()

# Sound effects (optional - will handle missing files gracefully)
try:
    jump_sound = pygame.mixer.Sound("assets/sounds/jump.wav")
    hit_sound = pygame.mixer.Sound("assets/sounds/hit.wav")
    collect_sound = pygame.mixer.Sound("assets/sounds/collect.wav")
    shoot_sound = pygame.mixer.Sound("assets/sounds/shoot.wav")
    checkpoint_sound = pygame.mixer.Sound("assets/sounds/checkpoint.wav")
    level_complete_sound = pygame.mixer.Sound("assets/sounds/level_complete.wav")
    
    # Background music
    pygame.mixer.music.load("assets/sounds/background_music.wav")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
except:
    jump_sound = hit_sound = collect_sound = shoot_sound = None
    checkpoint_sound = level_complete_sound = None

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    if not os.path.exists(path):
        # Return empty dict if path doesn't exist
        return {}
    
    images = [f for f in listdir(path) if isfile(join(path, f))]
    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size):
    try:
        path = join("assets", "Terrain", "Terrain.png")
        image = pygame.image.load(path).convert_alpha()
        surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
        rect = pygame.Rect(96, 0, size, size)
        surface.blit(image, (0, 0), rect)
        return pygame.transform.scale2x(surface)
    except:
        # Fallback if terrain image doesn't exist
        surface = pygame.Surface((size * 2, size * 2))
        surface.fill((100, 100, 100))
        return surface

def get_background(name):
    try:
        image = pygame.image.load(join("assets", "Background", name))
        _, _, width, height = image.get_rect()
        tiles = []

        for i in range(WIDTH // width + 1):
            for j in range(HEIGHT // height + 1):
                pos = (i * width, j * height)
                tiles.append(pos)

        return tiles, image
    except:
        # Fallback background
        image = pygame.Surface((WIDTH, HEIGHT))
        image.fill((135, 206, 250))  # Sky blue
        return [(0, 0)], image

class GameState:
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    PAUSED = "paused"
    LEVEL_COMPLETE = "level_complete"
    
    def __init__(self):
        self.state = self.MENU
        self.score = 0
        self.health = 100
        self.max_health = 100
        self.lives = 3
        self.current_level = 1
        self.max_level = 3
        self.fruits_collected = 0
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 72)
        self.checkpoint_reached = False
        self.checkpoint_pos = (100, 100)
        
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.lives -= 1
            if self.lives <= 0:
                self.state = self.GAME_OVER
            else:
                self.health = self.max_health  # Restore health on life loss
        
    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
    
    def draw_ui(self, window):
        if self.state == self.PLAYING or self.state == self.PAUSED:
            # Draw score
            score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
            window.blit(score_text, (10, 10))
            
            # Draw lives
            lives_text = self.font.render(f"Lives: {self.lives}", True, (255, 255, 255))
            window.blit(lives_text, (10, 50))
            
            # Draw fruits
            fruits_text = self.font.render(f"Fruits: {self.fruits_collected}", True, (255, 255, 255))
            window.blit(fruits_text, (10, 90))
            
            # Draw level
            level_text = self.font.render(f"Level: {self.current_level}", True, (255, 255, 255))
            window.blit(level_text, (10, 130))
            
            # Draw health bar
            health_bar_width = 200
            health_bar_height = 20
            health_percentage = self.health / self.max_health
            
            # Background (red)
            pygame.draw.rect(window, (100, 0, 0), (WIDTH - 220, 10, health_bar_width, health_bar_height))
            # Health (green to red gradient based on health)
            if health_percentage > 0.5:
                color = (255 * (1 - health_percentage) * 2, 255, 0)
            else:
                color = (255, 255 * health_percentage * 2, 0)
            pygame.draw.rect(window, color, (WIDTH - 220, 10, health_bar_width * health_percentage, health_bar_height))
            # Border
            pygame.draw.rect(window, (255, 255, 255), (WIDTH - 220, 10, health_bar_width, health_bar_height), 2)
            
            # Health text
            health_text = self.small_font.render(f"Health: {int(self.health)}/{self.max_health}", True, (255, 255, 255))
            window.blit(health_text, (WIDTH - 220, 35))
            
            # Pause indicator
            if self.state == self.PAUSED:
                pause_text = self.title_font.render("PAUSED", True, (255, 255, 255))
                text_rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//2))
                window.blit(pause_text, text_rect)
                resume_text = self.font.render("Press P to Resume", True, (255, 255, 255))
                resume_rect = resume_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80))
                window.blit(resume_text, resume_rect)
        
        elif self.state == self.MENU:
            self.draw_menu(window)
        elif self.state == self.GAME_OVER:
            self.draw_game_over(window)
        elif self.state == self.LEVEL_COMPLETE:
            self.draw_level_complete(window)
    
    def draw_menu(self, window):
        # Title
        title_text = self.title_font.render("PLATFORMER ADVENTURE", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
        window.blit(title_text, title_rect)
        
        # Instructions
        instructions = [
            "Arrow Keys - Move",
            "Space - Jump (Wall Jump Available!)",
            "X - Dash",
            "P - Pause",
            "Collect fruits and reach the flag!",
            "",
            "Press ENTER to Start",
            "Press Q to Quit"
        ]
        
        y_offset = HEIGHT//2 - 20
        for instruction in instructions:
            text = self.font.render(instruction, True, (255, 255, 255))
            text_rect = text.get_rect(center=(WIDTH//2, y_offset))
            window.blit(text, text_rect)
            y_offset += 35
    
    def draw_game_over(self, window):
        game_over_text = self.title_font.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        window.blit(game_over_text, text_rect)
        
        score_text = self.font.render(f"Final Score: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
        window.blit(score_text, score_rect)
        
        restart_text = self.font.render("Press R to Restart or M for Menu", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
        window.blit(restart_text, restart_rect)
    
    def draw_level_complete(self, window):
        complete_text = self.title_font.render("LEVEL COMPLETE!", True, (0, 255, 0))
        text_rect = complete_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        window.blit(complete_text, text_rect)
        
        if self.current_level < self.max_level:
            next_text = self.font.render("Press N for Next Level or M for Menu", True, (255, 255, 255))
        else:
            next_text = self.font.render("Congratulations! You beat all levels!", True, (255, 255, 255))
        
        next_rect = next_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
        window.blit(next_text, next_rect)

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        # Load sprites after initialization
        self.SPRITES = load_sprite_sheets("MainCharacters", "PinkMan", 32, 32, True)
        
        # Create fallback sprites if loading fails
        if not self.SPRITES:
            self.create_fallback_sprites()
        
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.dash_cooldown = 0
        self.dash_power = 15
        self.max_speed = PLAYER_VEL
        self.wall_slide = False
        self.wall_jump_cooldown = 0

    def create_fallback_sprites(self):
        """Create simple fallback sprites if asset loading fails"""
        self.SPRITES = {}
        colors = {"idle": (255, 0, 0), "run": (255, 100, 100), "jump": (255, 200, 200), 
                 "fall": (200, 0, 0), "hit": (100, 0, 0), "double_jump": (255, 150, 150)}
        
        for state in colors:
            for direction in ["left", "right"]:
                sprites = []
                for i in range(4):  # Create 4 frame animation
                    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
                    pygame.draw.rect(surface, colors[state], (16, 16, 32, 48))
                    if direction == "left":
                        surface = pygame.transform.flip(surface, True, False)
                    sprites.append(surface)
                self.SPRITES[f"{state}_{direction}"] = sprites
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.dash_cooldown = 0
        self.dash_power = 15
        self.max_speed = PLAYER_VEL
        self.wall_slide = False
        self.wall_jump_cooldown = 0

    def jump(self):
        if self.jump_count < 2 or self.wall_slide:
            self.y_vel = -self.GRAVITY * 8
            self.animation_count = 0
            if not self.wall_slide:
                self.jump_count += 1
            else:
                # Wall jump - add horizontal velocity away from wall
                self.x_vel = 8 if self.direction == "left" else -8
                self.wall_jump_cooldown = 10
                self.jump_count = 1
            
            if self.jump_count == 1:
                self.fall_count = 0
            if jump_sound:
                jump_sound.play()

    def dash(self):
        if self.dash_cooldown <= 0:
            if self.direction == "right":
                self.x_vel = self.dash_power
            else:
                self.x_vel = -self.dash_power
            self.dash_cooldown = 60

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        if not self.hit:
            self.hit = True
            if hit_sound:
                hit_sound.play()

    def move_left(self, vel):
        if self.wall_jump_cooldown <= 0:
            self.x_vel = max(-self.max_speed, self.x_vel - vel * 0.3)
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        if self.wall_jump_cooldown <= 0:
            self.x_vel = min(self.max_speed, self.x_vel + vel * 0.3)
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def apply_friction(self):
        if abs(self.x_vel) > 0.1:
            self.x_vel *= 0.8
        else:
            self.x_vel = 0

    def loop(self, fps):
        # Wall slide logic
        if self.wall_slide and self.y_vel > 0:
            self.y_vel = min(self.y_vel, 2)  # Slower fall when wall sliding
        else:
            self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 0.5:  # Shorter hit time
            self.hit = False
            self.hit_count = 0

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        if self.wall_jump_cooldown > 0:
            self.wall_jump_cooldown -= 1

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
        self.wall_slide = False

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.wall_slide:
            sprite_sheet = "wall_slide" if "wall_slide" in self.SPRITES else "idle"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif abs(self.x_vel) > 0.1:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        if sprite_sheet_name in self.SPRITES:
            sprites = self.SPRITES[sprite_sheet_name]
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.sprite = sprites[sprite_index]
        else:
            # Fallback to idle if sprite doesn't exist
            sprite_sheet_name = "idle_" + self.direction
            sprites = self.SPRITES[sprite_sheet_name]
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.sprite = sprites[sprite_index]
        
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))
        
        # Wall slide indicator
        if self.wall_slide:
            pygame.draw.circle(win, (255, 255, 0), 
                             (self.rect.centerx - offset_x, self.rect.centery), 30, 3)
        
        # Dash cooldown indicator
        if self.dash_cooldown > 0:
            dash_bar_width = 50
            dash_bar_height = 5
            dash_progress = (60 - self.dash_cooldown) / 60
            pygame.draw.rect(win, (255, 0, 0), 
                           (self.rect.x - offset_x, self.rect.y - 10, dash_bar_width, dash_bar_height))
            pygame.draw.rect(win, (0, 255, 0), 
                           (self.rect.x - offset_x, self.rect.y - 10, dash_bar_width * dash_progress, dash_bar_height))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fruit(Object):
    def __init__(self, x, y, fruit_type="apple"):
        super().__init__(x, y, 32, 32, "fruit")
        self.fruit_type = fruit_type
        
        # Create fruit sprite based on type
        colors = {
            "apple": (255, 0, 0),
            "banana": (255, 255, 0),
            "orange": (255, 165, 0),
            "grape": (128, 0, 128)
        }
        
        color = colors.get(fruit_type, (255, 0, 0))
        pygame.draw.circle(self.image, color, (16, 16), 14)
        pygame.draw.circle(self.image, (0, 255, 0), (16, 8), 4)  # Leaf
        
        self.mask = pygame.mask.from_surface(self.image)
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.bob_count = 0
        self.points = 100
        
    def update(self):
        self.bob_count += 0.1
        bob_y = math.sin(self.bob_count + self.bob_offset) * 5
        new_y = self.rect.y + bob_y - getattr(self, 'prev_bob_y', 0)
        self.prev_bob_y = bob_y
        self.rect.y = new_y

class HealthPotion(Object):
    def __init__(self, x, y):
        super().__init__(x, y, 24, 32, "health_potion")
        # Draw health potion
        pygame.draw.rect(self.image, (255, 0, 0), (6, 8, 12, 20))
        pygame.draw.rect(self.image, (139, 69, 19), (8, 4, 8, 8))
        pygame.draw.circle(self.image, (255, 255, 255), (12, 16), 3)
        self.mask = pygame.mask.from_surface(self.image)
        self.heal_amount = 25

class Checkpoint(Object):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 64, "checkpoint")
        # Draw checkpoint flag
        pygame.draw.rect(self.image, (139, 69, 19), (4, 0, 4, 64))  # Pole
        pygame.draw.rect(self.image, (255, 0, 0), (8, 8, 20, 12))  # Flag
        self.mask = pygame.mask.from_surface(self.image)
        self.activated = False

class LevelExit(Object):
    def __init__(self, x, y):
        super().__init__(x, y, 48, 96, "level_exit")
        # Draw exit flag
        pygame.draw.rect(self.image, (139, 69, 19), (8, 0, 8, 96))  # Pole
        pygame.draw.rect(self.image, (0, 255, 0), (16, 16, 28, 20))  # Flag
        self.mask = pygame.mask.from_surface(self.image)

class Projectile(Object):
    def __init__(self, x, y, direction, speed=8):
        super().__init__(x, y, 12, 6, "projectile")
        pygame.draw.ellipse(self.image, (255, 100, 0), (0, 0, 12, 6))
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = speed
        self.direction = direction
        
    def update(self):
        self.rect.x += self.speed * self.direction

class Enemy(Object):
    def __init__(self, x, y, width, height, enemy_type="walker"):
        super().__init__(x, y, width, height, f"enemy_{enemy_type}")
        self.enemy_type = enemy_type
        self.start_x = x
        self.direction = 1
        self.shoot_cooldown = 0
        
        if enemy_type == "walker":
            self.image.fill((150, 0, 0))
            self.move_range = 150
            self.speed = 1
        elif enemy_type == "shooter":
            self.image.fill((0, 150, 0))
            self.move_range = 100
            self.speed = 0.5
        elif enemy_type == "jumper":
            self.image.fill((0, 0, 150))
            self.move_range = 200
            self.speed = 2
            self.jump_timer = 0
        
        self.mask = pygame.mask.from_surface(self.image)
        
    def update(self, player_pos, projectiles):
        if self.enemy_type == "walker":
            self.rect.x += self.speed * self.direction
            if self.rect.x >= self.start_x + self.move_range or self.rect.x <= self.start_x:
                self.direction *= -1
                
        elif self.enemy_type == "shooter":
            self.rect.x += self.speed * self.direction
            if self.rect.x >= self.start_x + self.move_range or self.rect.x <= self.start_x:
                self.direction *= -1
            
            # Shoot at player
            self.shoot_cooldown -= 1
            if self.shoot_cooldown <= 0:
                player_distance = abs(player_pos[0] - self.rect.centerx)
                if player_distance < 300:  # Shoot if player is close
                    shoot_direction = 1 if player_pos[0] > self.rect.centerx else -1
                    projectile = Projectile(self.rect.centerx, self.rect.centery, shoot_direction)
                    projectiles.append(projectile)
                    self.shoot_cooldown = 120  # 2 seconds at 60 FPS
                    if shoot_sound:
                        shoot_sound.play()
                        
        elif self.enemy_type == "jumper":
            self.rect.x += self.speed * self.direction
            if self.rect.x >= self.start_x + self.move_range or self.rect.x <= self.start_x:
                self.direction *= -1

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        try:
            self.fire = load_sprite_sheets("Traps", "Fire", width, height)
            if self.fire:
                self.image = self.fire["off"][0] if "off" in self.fire else list(self.fire.values())[0][0]
            else:
                # Fallback fire animation
                self.create_fallback_fire()
        except:
            self.create_fallback_fire()
        
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def create_fallback_fire(self):
        self.fire = {"on": [], "off": []}
        # Create simple fire animation
        for i in range(4):
            surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            height_var = random.randint(-2, 2)
            pygame.draw.rect(surface, (255, 100 + i * 30, 0), 
                           (0, height_var, self.width, self.height - height_var))
            self.fire["on"].append(surface)
        
        # Off state
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.fire["off"] = [surface]

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        if self.fire and self.animation_name in self.fire:
            sprites = self.fire[self.animation_name]
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.image = sprites[sprite_index]
            self.animation_count += 1

            self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
            self.mask = pygame.mask.from_surface(self.image)

            if self.animation_count // self.ANIMATION_DELAY > len(sprites):
                self.animation_count = 0

def create_level(level_num):
    block_size = 96
    objects = []
    projectiles = []
    
    if level_num == 1:
        # Level 1: Basic platforming
        # Floor
        floor = [Block(i * block_size, HEIGHT - block_size, block_size)
                 for i in range(-WIDTH // block_size, (WIDTH * 4) // block_size)]
        objects.extend(floor)
        
        # Platforms
        objects.append(Block(block_size * 3, HEIGHT - block_size * 3, block_size))
        objects.append(Block(block_size * 6, HEIGHT - block_size * 4, block_size))
        objects.append(Block(block_size * 9, HEIGHT - block_size * 2, block_size))
        
        # Fruits
        objects.append(Fruit(block_size * 2, HEIGHT - block_size * 2, "apple"))
        objects.append(Fruit(block_size * 5, HEIGHT - block_size * 5, "banana"))
        objects.append(Fruit(block_size * 8, HEIGHT - block_size * 3, "orange"))
        
        # Health potion
        objects.append(HealthPotion(block_size * 4, HEIGHT - block_size * 4))
        
        # Simple enemy
        objects.append(Enemy(block_size * 7, HEIGHT - block_size - 40, 40, 40, "walker"))
        
        # Level exit
        objects.append(LevelExit(block_size * 12, HEIGHT - block_size * 2))
        
    elif level_num == 2:
        # Level 2: More challenging with checkpoint
        # Floor with gaps
        floor_sections = [
            range(-WIDTH // block_size, 3),
            range(5, 10),
            range(12, 20),
            range(22, 30)
        ]
        for section in floor_sections:
            for i in section:
                objects.append(Block(i * block_size, HEIGHT - block_size, block_size))
        
        # Vertical wall sections for wall jumping
        for i in range(3):
            objects.append(Block(block_size * 4, HEIGHT - block_size * (2 + i), block_size))
            objects.append(Block(block_size * 11, HEIGHT - block_size * (2 + i), block_size))
        
        # Higher platforms
        objects.append(Block(block_size * 15, HEIGHT - block_size * 6, block_size))
        objects.append(Block(block_size * 18, HEIGHT - block_size * 4, block_size))
        
        # Checkpoint
        objects.append(Checkpoint(block_size * 13, HEIGHT - block_size * 2))
        
        # Enemies
        objects.append(Enemy(block_size * 6, HEIGHT - block_size - 40, 40, 40, "shooter"))
        objects.append(Enemy(block_size * 16, HEIGHT - block_size - 40, 40, 40, "walker"))
        
        # Fruits
        objects.append(Fruit(block_size * 8, HEIGHT - block_size * 2, "grape"))
        objects.append(Fruit(block_size * 14, HEIGHT - block_size * 7, "apple"))
        objects.append(Fruit(block_size * 19, HEIGHT - block_size * 5, "banana"))
        
        # Health potions
        objects.append(HealthPotion(block_size * 10, HEIGHT - block_size * 2))
        objects.append(HealthPotion(block_size * 17, HEIGHT - block_size * 7))
        
        # Fire hazard
        fire = Fire(block_size * 21, HEIGHT - block_size - 64, 16, 32)
        fire.on()
        objects.append(fire)
        
        # Level exit
        objects.append(LevelExit(block_size * 25, HEIGHT - block_size * 2))
        
    elif level_num == 3:
        # Level 3: Advanced level with all mechanics
        # Complex floor layout
        floor_sections = [
            range(-WIDTH // block_size, 2),
            range(4, 8),
            range(10, 15),
            range(17, 22),
            range(24, 35)
        ]
        for section in floor_sections:
            for i in section:
                objects.append(Block(i * block_size, HEIGHT - block_size, block_size))
        
        # Multi-level platforms and walls for wall jumping
        # Left wall section
        for i in range(5):
            objects.append(Block(block_size * 3, HEIGHT - block_size * (2 + i), block_size))
        
        # Middle wall sections
        for i in range(4):
            objects.append(Block(block_size * 9, HEIGHT - block_size * (3 + i), block_size))
            objects.append(Block(block_size * 16, HEIGHT - block_size * (2 + i), block_size))
        
        # High platforms
        objects.append(Block(block_size * 6, HEIGHT - block_size * 8, block_size))
        objects.append(Block(block_size * 12, HEIGHT - block_size * 7, block_size))
        objects.append(Block(block_size * 19, HEIGHT - block_size * 6, block_size))
        objects.append(Block(block_size * 26, HEIGHT - block_size * 4, block_size))
        
        # Checkpoint
        objects.append(Checkpoint(block_size * 20, HEIGHT - block_size * 7))
        
        # Multiple enemy types
        objects.append(Enemy(block_size * 5, HEIGHT - block_size - 40, 40, 40, "walker"))
        objects.append(Enemy(block_size * 11, HEIGHT - block_size - 40, 40, 40, "shooter"))
        objects.append(Enemy(block_size * 18, HEIGHT - block_size - 40, 40, 40, "jumper"))
        objects.append(Enemy(block_size * 27, HEIGHT - block_size - 40, 40, 40, "shooter"))
        
        # Multiple fire hazards
        fire1 = Fire(block_size * 8, HEIGHT - block_size - 64, 16, 32)
        fire1.on()
        objects.append(fire1)
        
        fire2 = Fire(block_size * 23, HEIGHT - block_size - 64, 16, 32)
        fire2.on()
        objects.append(fire2)
        
        # Fruits scattered throughout
        fruits_data = [
            (block_size * 2, HEIGHT - block_size * 2, "apple"),
            (block_size * 7, HEIGHT - block_size * 9, "banana"),
            (block_size * 13, HEIGHT - block_size * 8, "orange"),
            (block_size * 15, HEIGHT - block_size * 3, "grape"),
            (block_size * 21, HEIGHT - block_size * 8, "apple"),
            (block_size * 28, HEIGHT - block_size * 5, "banana")
        ]
        
        for x, y, fruit_type in fruits_data:
            objects.append(Fruit(x, y, fruit_type))
        
        # Health potions
        objects.append(HealthPotion(block_size * 4, HEIGHT - block_size * 6))
        objects.append(HealthPotion(block_size * 14, HEIGHT - block_size * 4))
        objects.append(HealthPotion(block_size * 25, HEIGHT - block_size * 2))
        
        # Level exit
        objects.append(LevelExit(block_size * 32, HEIGHT - block_size * 2))
    
    return objects, projectiles

def draw(window, background, bg_image, player, objects, projectiles, offset_x, game_state):
    # Clear screen
    window.fill((50, 50, 100))  # Dark blue fallback
    
    # Draw background
    for tile in background:
        window.blit(bg_image, (tile[0] - offset_x % bg_image.get_width(), tile[1]))

    # Draw objects
    for obj in objects:
        obj.draw(window, offset_x)
    
    # Draw projectiles
    for projectile in projectiles:
        projectile.draw(window, offset_x)

    # Draw player
    if game_state.state == GameState.PLAYING:
        player.draw(window, offset_x)
    
    # Draw UI
    game_state.draw_ui(window)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

def check_wall_slide(player, objects):
    # Check for wall sliding
    wall_left = collide(player, objects, -5)
    wall_right = collide(player, objects, 5)
    
    if (wall_left or wall_right) and player.y_vel > 0 and player.jump_count > 0:
        player.wall_slide = True
        if wall_left and player.direction != "left":
            player.direction = "left"
        elif wall_right and player.direction != "right":
            player.direction = "right"
    else:
        player.wall_slide = False

def handle_move(player, objects, projectiles, game_state):
    if game_state.state != GameState.PLAYING:
        return

    keys = pygame.key.get_pressed()

    # Apply friction when no keys are pressed
    if not (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]):
        player.apply_friction()

    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    # Check for wall sliding
    check_wall_slide(player, objects)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    # Check for collisions and handle different object types
    objects_to_remove = []
    for obj in to_check:
        if obj and obj.name:
            if obj.name == "fire" or obj.name.startswith("enemy"):
                player.make_hit()
                game_state.take_damage(25)
            elif obj.name == "fruit":
                if collect_sound:
                    collect_sound.play()
                game_state.fruits_collected += 1
                game_state.score += obj.points
                objects_to_remove.append(obj)
            elif obj.name == "health_potion":
                if collect_sound:
                    collect_sound.play()
                game_state.heal(obj.heal_amount)
                game_state.score += 50
                objects_to_remove.append(obj)
            elif obj.name == "checkpoint":
                if not obj.activated:
                    obj.activated = True
                    game_state.checkpoint_reached = True
                    game_state.checkpoint_pos = (player.rect.x, player.rect.y)
                    if checkpoint_sound:
                        checkpoint_sound.play()
                    # Change checkpoint appearance
                    obj.image.fill((0, 0, 0, 0))
                    pygame.draw.rect(obj.image, (139, 69, 19), (4, 0, 4, 64))
                    pygame.draw.rect(obj.image, (0, 255, 0), (8, 8, 20, 12))  # Green flag
            elif obj.name == "level_exit":
                game_state.state = GameState.LEVEL_COMPLETE
                if level_complete_sound:
                    level_complete_sound.play()
    
    # Check projectile collisions
    for projectile in projectiles[:]:
        if pygame.sprite.collide_mask(player, projectile):
            player.make_hit()
            game_state.take_damage(15)
            projectiles.remove(projectile)
    
    # Remove collected items
    for obj in objects_to_remove:
        if obj in objects:
            objects.remove(obj)

def update_enemies_and_projectiles(objects, projectiles, player_pos):
    # Update enemies
    for obj in objects:
        if obj.name and obj.name.startswith("enemy"):
            obj.update(player_pos, projectiles)
    
    # Update projectiles
    for projectile in projectiles[:]:
        projectile.update()
        # Remove projectiles that are off screen
        if projectile.rect.x < -50 or projectile.rect.x > WIDTH + 50:
            projectiles.remove(projectile)

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Pink.png")
    
    game_state = GameState()
    player = Player(100, 100, 50, 50)
    objects, projectiles = create_level(1)

    offset_x = 0
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if game_state.state == GameState.MENU:
                    if event.key == pygame.K_RETURN:
                        game_state.state = GameState.PLAYING
                        game_state.current_level = 1
                        objects, projectiles = create_level(1)
                        player = Player(100, 100, 50, 50)
                        offset_x = 0
                    elif event.key == pygame.K_q:
                        run = False
                
                elif game_state.state == GameState.PLAYING:
                    if event.key == pygame.K_SPACE:
                        player.jump()
                    elif event.key == pygame.K_x:
                        player.dash()
                    elif event.key == pygame.K_p:
                        game_state.state = GameState.PAUSED
                
                elif game_state.state == GameState.PAUSED:
                    if event.key == pygame.K_p:
                        game_state.state = GameState.PLAYING
                    elif event.key == pygame.K_m:
                        game_state.state = GameState.MENU
                
                elif game_state.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        # Restart current level
                        game_state = GameState()
                        game_state.state = GameState.PLAYING
                        game_state.current_level = 1
                        player = Player(100, 100, 50, 50)
                        objects, projectiles = create_level(1)
                        offset_x = 0
                    elif event.key == pygame.K_m:
                        game_state = GameState()
                
                elif game_state.state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_n and game_state.current_level < game_state.max_level:
                        # Next level
                        game_state.current_level += 1
                        game_state.state = GameState.PLAYING
                        game_state.checkpoint_reached = False
                        player = Player(100, 100, 50, 50)
                        objects, projectiles = create_level(game_state.current_level)
                        offset_x = 0
                    elif event.key == pygame.K_m:
                        game_state = GameState()

        if game_state.state == GameState.PLAYING:
            # Update moving objects
            for obj in objects:
                if hasattr(obj, 'update') and obj.name and not obj.name.startswith("enemy"):
                    obj.update()
            
            # Update enemies and projectiles
            update_enemies_and_projectiles(objects, projectiles, (player.rect.centerx, player.rect.centery))
            
            player.loop(FPS)
            
            # Update fire animations
            for obj in objects:
                if obj.name and obj.name == "fire":
                    obj.loop()
            
            handle_move(player, objects, projectiles, game_state)
            
            # Check if player falls off the world
            if player.rect.y > HEIGHT + 100:
                if game_state.checkpoint_reached:
                    # Respawn at checkpoint
                    player.rect.x, player.rect.y = game_state.checkpoint_pos
                    game_state.take_damage(25)
                else:
                    # Respawn at start
                    player.rect.x, player.rect.y = 100, 100
                    game_state.take_damage(50)
                
                player.x_vel = player.y_vel = 0

            # Camera scrolling
            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel

        draw(window, background, bg_image, player, objects, projectiles, offset_x, game_state)

    pygame.quit()
    quit()

if __name__ == "__main__":
    main(window)