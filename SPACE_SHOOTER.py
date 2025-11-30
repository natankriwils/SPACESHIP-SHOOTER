import pygame
from pygame import mixer
from pygame.locals import *
import random
import math

pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()

clock = pygame.time.Clock()
fps = 60

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SPACE SHOOTER")

font30 = pygame.font.SysFont("constantia", 30)
font40 = pygame.font.SysFont("constantia", 40)
font20 = pygame.font.SysFont("constantia", 20) 

GUARD_ALIEN_DATA = [] 

def safe_load_sound(path, default_volume=0.1):
    try:
        s = mixer.Sound(path)
        s.set_volume(default_volume)
        return s
    except Exception:
        return None

def safe_load_image(path, size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception:
        if size and isinstance(size, tuple):
            surf = pygame.Surface(size, pygame.SRCALPHA)
        else:
            surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        surf.fill((200, 200, 200, 255))
        return surf

explosion_sound = safe_load_sound("Tugas/SPACESHIP SHOOTER/img/explosion.wav", 0.12)
explosion2_sound = safe_load_sound("Tugas/SPACESHIP SHOOTER/img/explosion2.wav", 0.25)
laser_sound = safe_load_sound("Tugas/SPACESHIP SHOOTER/img/laser.wav", 0.08)

bg = safe_load_image("Tugas/SPACESHIP SHOOTER/img/bg.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
player_img = safe_load_image("Tugas/SPACESHIP SHOOTER/img/spaceship.png")
alien_img = safe_load_image("Tugas/SPACESHIP SHOOTER/img/alien.png")
bullet_img = safe_load_image("Tugas/SPACESHIP SHOOTER/img/bullet.png")
alien_bullet_img = safe_load_image("Tugas/SPACESHIP SHOOTER/img/alien_bullet.png")
boss_img_base = safe_load_image("Tugas/SPACESHIP SHOOTER/img/alien2.png")
asteroid = safe_load_image("Tugas/SPACESHIP SHOOTER/img/asteroid.jpg")
boss_img = pygame.transform.scale(boss_img_base, (120, 120))
exp_imgs = []
for n in range(1, 6):
    exp_imgs.append(safe_load_image(f"Tugas/SPACESHIP SHOOTER/img/exp{n}.png"))

powerup_images = {
    "speed": safe_load_image("Tugas/SPACESHIP SHOOTER/img/power_speed.png", (32, 32)),
    "triple": safe_load_image("Tugas/SPACESHIP SHOOTER/img/power_triple.png", (32, 32)),
    "five": safe_load_image("Tugas/SPACESHIP SHOOTER/img/power_five.png", (32, 32)),
    "heal": safe_load_image("Tugas/SPACESHIP SHOOTER/img/power_heal.png", (32, 32))
}

RED = (255,0,0)
GREEN = (0,255,0)
WHITE = (255,255,255)

game_state = "menu"
paused = False

alien_cooldown = 900
last_alien_shot = pygame.time.get_ticks()

countdown = 3
last_countdown = pygame.time.get_ticks()
countdown_started_after_drop = False

score = 0
current_wave = 1
max_waves = 5

game_over = 0
boss_phase = 1

wave_reward = {1:"speed", 2:"triple", 3:"five", 4:"heal", 5:"heal"}

wave_transition = False
wave_transition_timer = 0
wave_transition_delay = 2000

player_fire_rate = 350
player_bullet_speed = 4

spaceship_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
alien_group = pygame.sprite.Group()
alien_bullets_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
powerup_group = pygame.sprite.Group()
asteroid_group = pygame.sprite.Group()

btn_w, btn_h = 200, 60
center_x = SCREEN_WIDTH // 2
start_rect = pygame.Rect(center_x - btn_w//2, 345 - btn_h//2, btn_w, btn_h)
quit_rect = pygame.Rect(center_x - btn_w//2, 415 - btn_h//2, btn_w, btn_h)
credits_rect = pygame.Rect(SCREEN_WIDTH - 140, 20, 130, 40)
pause_rect = pygame.Rect(SCREEN_WIDTH - 60, 20, 40, 40)
back_rect = pygame.Rect(20, 20, 100, 40)
restart_rect = pygame.Rect(center_x - btn_w//2, 440 - btn_h//2, btn_w, btn_h)
go_back_rect = pygame.Rect(center_x - btn_w//2, 520 - btn_h//2, btn_w, btn_h)
pause_resume_rect = pygame.Rect(center_x - btn_w//2, 345 - btn_h//2, btn_w, btn_h)
pause_restart_rect = pygame.Rect(center_x - btn_w//2, 415 - btn_h//2, btn_w, btn_h)
pause_menu_rect = pygame.Rect(center_x - btn_w//2, 485 - btn_h//2, btn_w, btn_h)

def draw_bg():
    screen.blit(bg, (0,0))

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x,y))

def draw_button(text, rect, font, text_col, rect_col=WHITE):
    pygame.draw.rect(screen, rect_col, rect, 2)
    img = font.render(text, True, text_col)
    screen.blit(img, img.get_rect(center=rect.center))

def difficulty_multiplier(wave):
    return 1.0 + 0.15 * max(0, wave - 1)

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size=1):
        super().__init__()
        self.images = []
        for img in exp_imgs:
            if size == 1:
                self.images.append(pygame.transform.scale(img, (20, 20)))
            elif size == 2:
                self.images.append(pygame.transform.scale(img, (40, 40)))
            else:
                self.images.append(pygame.transform.scale(img, (160, 160)))
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(center=(x, y))
        self.counter = 0

    def update(self):
        self.counter += 1
        if self.counter >= 3:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.index]

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, health=5):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect(center=(x,y))
        self.health_start = health
        self.health_remaining = health
        self.last_shot = pygame.time.get_ticks()
        self.weapon_level = 1
        self.fire_rate = player_fire_rate
        self.bullet_speed = player_bullet_speed
        self.mask = pygame.mask.from_surface(self.image)

    def shoot(self):
        cx, cy = self.rect.centerx, self.rect.top
        if self.weapon_level == 1:
            bullet_group.add(Bullet(cx, cy, 0, self.bullet_speed))
        elif self.weapon_level == 2:
            bullet_group.add(Bullet(cx, cy, 0, self.bullet_speed))
            bullet_group.add(Bullet(cx-15, cy, -1, self.bullet_speed))
            bullet_group.add(Bullet(cx+15, cy, 1, self.bullet_speed))
        elif self.weapon_level == 3:
            bullet_group.add(Bullet(cx, cy, 0, self.bullet_speed))     
            bullet_group.add(Bullet(cx-18, cy, 0, self.bullet_speed))  
            bullet_group.add(Bullet(cx+18, cy, 0, self.bullet_speed))  
            bullet_group.add(Bullet(cx-30, cy, -2, self.bullet_speed)) 
            bullet_group.add(Bullet(cx+30, cy, 2, self.bullet_speed))  

    def update(self):
        global game_over
        keys = pygame.key.get_pressed()
        
        PLAYER_TOP_BOUNDARY = 500
        
        if keys[K_LEFT]:
            self.rect.x -= 8
        if keys[K_RIGHT]:
            self.rect.x += 8
        
        if keys[K_UP]:
            self.rect.y -= 8
        if keys[K_DOWN]:
            self.rect.y += 8

        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)

        if self.rect.top < PLAYER_TOP_BOUNDARY:
            self.rect.top = PLAYER_TOP_BOUNDARY
        
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

        now = pygame.time.get_ticks()
        if keys[K_SPACE] and now - self.last_shot > self.fire_rate:
            if laser_sound: laser_sound.play()
            self.shoot()
            self.last_shot = now

        self.mask = pygame.mask.from_surface(self.image)
        if self.health_remaining <= 0:
            if game_over == 0:
                explosion_group.add(Explosion(self.rect.centerx, self.rect.centery, 3))
                if explosion2_sound: explosion2_sound.play()
            self.kill()
            return -1
        return 0

    def draw_health_bar(self):
        w = self.rect.width
        h = 12
        y = self.rect.bottom + 8
        pygame.draw.rect(screen, RED, (self.rect.x, y, w, h))
        if getattr(self, 'health_remaining', 0) > 0:
            pygame.draw.rect(screen, GREEN, (self.rect.x, y, int(w * (self.health_remaining/self.health_start)), h))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, speed):
        super().__init__()
        self.image = bullet_img
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.speed = speed
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        global score, current_wave, last_killed_alien_pos
        self.rect.y -= self.speed
        self.rect.x += self.dx
        if self.rect.bottom < 0:
            self.kill()
            return

        hit = pygame.sprite.spritecollideany(self, alien_group, collided=pygame.sprite.collide_mask)
        if hit:
            hit.health -= 1

            hit_x = self.rect.centerx
            hit_y = self.rect.centery

            if hit.health > 0:
                if explosion2_sound:
                    explosion2_sound.play()
                explosion_group.add(Explosion(hit_x, hit_y, 1))
            else:
                last_killed_alien_pos = (hit.rect.centerx, hit.rect.centery) 
                if explosion_sound:
                    explosion_sound.play()
                explosion_group.add(Explosion(hit_x, hit_y, 2))
                score += 10 * current_wave
                hit.kill()

            self.kill()

class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, hp=3, amplitude=25, is_boss=False, is_guard=False, relative_pos=None):
        super().__init__()
        
        if is_boss:
            global boss_img
            self.image = boss_img
            self.is_boss = True
            self.last_shot_time = pygame.time.get_ticks() 
        else:
            self.image = alien_img
            self.is_boss = False
            
        self.rect = self.image.get_rect(center=(x, y))
        self.initial_x = x
        self.offset = 0.0
        self.offset_dir = 1
        self.amplitude = amplitude
        self.speed = max(0.0, speed)  
        self.health_start = hp
        self.health = hp
        self.mask = pygame.mask.from_surface(self.image)
        
        self.is_guard = is_guard
        self.relative_pos = relative_pos 

    def draw_health_bar(self):
        if self.is_boss:
            w = SCREEN_WIDTH * 0.4 
            h = 10 
            
            x = self.rect.centerx - w // 2 
            y = self.rect.bottom + 15 
            
            TOTAL_BOSS_HP = 100
            ratio = self.health / TOTAL_BOSS_HP
            
            pygame.draw.rect(screen, RED, (x, y, w, h)) 
            
            if self.health > 0:
                pygame.draw.rect(screen, GREEN, (x, y, int(w * ratio), h))

    def update(self):
        if self.is_boss:
            
            margin = 20 
            
            boss_min_x = 0 + margin
            boss_max_x = SCREEN_WIDTH - margin

            self.offset += self.offset_dir * self.speed
            
            if self.offset > self.amplitude or self.offset < -self.amplitude:
                self.offset_dir *= -1
                self.offset = max(-self.amplitude, min(self.amplitude, self.offset))

            new_center_x = self.initial_x + self.offset
            
            if new_center_x < boss_min_x:
                new_center_x = boss_min_x
                self.offset_dir = 1
                self.offset = new_center_x - self.initial_x 
            elif new_center_x > boss_max_x:
                new_center_x = boss_max_x
                self.offset_dir = -1
                self.offset = new_center_x - self.initial_x
            
            self.rect.centerx = int(new_center_x)
            
        else:
            self.offset += self.offset_dir * self.speed
            
            if self.offset > self.amplitude or self.offset < -self.amplitude:
                self.offset_dir *= -1
                self.offset = max(-self.amplitude, min(self.amplitude, self.offset))

            new_x = int(self.initial_x + self.offset)
            
            if new_x - self.rect.width//2 < 0:
                self.rect.left = 0
                if self.offset_dir == -1:
                    self.offset_dir = 1 
            elif new_x + self.rect.width//2 > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
                if self.offset_dir == 1:
                    self.offset_dir = -1 
            else:
                self.rect.x = new_x - self.rect.width//2

class AlienBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, dx=0):
        super().__init__()
        self.image = alien_bullet_img
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.dx = dx
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        global score
        self.rect.y += self.speed
        self.rect.x += self.dx
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
            return
        hits = pygame.sprite.spritecollide(self, spaceship_group, False, pygame.sprite.collide_mask)
        if hits:
            for ship in hits:
                if hasattr(ship, 'health_remaining') and ship.health_remaining > 0:
                    if explosion2_sound:
                        explosion2_sound.play()
                    ship.health_remaining -= 1
                    score = max(0, score - (5 * current_wave))
                    explosion_group.add(Explosion(self.rect.centerx, self.rect.centery, 1))
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        self.image = powerup_images.get(kind, powerup_images['speed'])
        self.rect = self.image.get_rect(center=(x,y))
        self.speed = 1.49
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT + 10: 
            self.kill()
            return
        
        hit = pygame.sprite.spritecollideany(self, spaceship_group, collided=pygame.sprite.collide_mask)
        if hit:
            for ship in spaceship_group:
                if self.kind == "speed":
                    ship.bullet_speed = max(ship.bullet_speed, 7)
                    ship.fire_rate = max(80, int(ship.fire_rate * 0.8))
                elif self.kind == "triple":
                    ship.weapon_level = 2
                elif self.kind == "five":
                    ship.weapon_level = 3
                elif self.kind == "heal":
                    ship.health_remaining = min(ship.health_start, ship.health_remaining + 1)
            self.kill()

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(asteroid, (40, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 3
        self.mask = pygame.mask.from_surface(self.image)
        self.pos_x = float(x)
        self.pos_y = float(y)

    def update(self, player_rect):
        global score
        self.pos_y += self.speed

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.kill()
            return

        hits = pygame.sprite.spritecollide(self, spaceship_group, False, pygame.sprite.collide_mask)
        if hits:
            for ship in hits:
                if hasattr(ship, 'health_remaining') and ship.health_remaining > 0:
                    if explosion_sound:
                        explosion_sound.play()
                    ship.health_remaining = max(0, ship.health_remaining - 1)
                    score = max(0, score - (5 * current_wave))
                    explosion_group.add(Explosion(self.rect.centerx, self.rect.centery, 1))
            self.kill()

def alien_hp_for_wave(wave):
    if wave <= 4:
        if wave <= 2: return 1
        return 3
    
    return 8 

def spawn_alien_for_wave(wave):
    alien_group.empty()
    global last_alien_shot, boss_phase, GUARD_ALIEN_DATA

    if wave != 5:
        boss_phase = 1 
    
    hp_for_wave = alien_hp_for_wave(wave)
    speed = max(0.2, 0.4 * difficulty_multiplier(wave))
    amplitude = 20 + (wave-1)*5

    if wave == 1:
        spawn_triangle_down(hp_for_wave, speed, amplitude) 
    elif wave == 2:
        spawn_circle(hp_for_wave, speed, amplitude) 
    elif wave == 3:
        spawn_double_right_triangle(hp_for_wave, speed, amplitude) 
    elif wave == 4:
        spawn_diamond_plus(hp_for_wave, speed, amplitude) 
    elif wave == 5:
        spawn_boss_alien()
    else:
        spawn_boss_alien()

    last_alien_shot = pygame.time.get_ticks()

def create_alien(x, y, speed, hp, amplitude, is_boss=False, is_guard=False, relative_pos=None):
    a = Alien(x, y, speed, hp=hp, amplitude=amplitude, is_boss=is_boss, is_guard=is_guard, relative_pos=relative_pos)
    alien_group.add(a)

def spawn_triangle_down(hp, speed, amplitude):
    center_x = SCREEN_WIDTH // 2
    y_start = 100
    y_spacing = 40
    x_spacing = 40
    rows = [5, 4, 3, 2, 1] 
    y_offset = y_start

    for count in rows:
        start_x = center_x - (count - 1) * x_spacing // 2
        for i in range(count):
            x = start_x + i * x_spacing
            create_alien(x, y_offset, speed, hp, amplitude)
        y_offset += y_spacing

def spawn_circle(hp, speed, amplitude):
    center_x = SCREEN_WIDTH // 2
    y_base = 200
    spacing = 50 

    create_alien(center_x - spacing/2, y_base - spacing, speed, hp, amplitude) 
    create_alien(center_x + spacing/2, y_base - spacing, speed, hp, amplitude)
    create_alien(center_x, y_base, speed, hp, amplitude) 
    create_alien(center_x - spacing/2, y_base + spacing, speed, hp, amplitude)
    create_alien(center_x + spacing/2, y_base + spacing, speed, hp, amplitude)
    
    radius = 120 
    num_aliens = 15
    angle_step = 2 * math.pi / num_aliens 
    
    for i in range(num_aliens):
        angle = (i * angle_step) - (math.pi / 2)
        x = center_x + int(radius * math.cos(angle))
        y = y_base + int(radius * math.sin(angle))
        create_alien(x, y, speed, hp, amplitude)

def spawn_double_right_triangle(hp, speed, amplitude):
    center_x = SCREEN_WIDTH // 2
    y_start = 80
    spacing = 40
    x_base_left = 60
    
    for r in range(4):
        y = y_start + r * spacing
        for c in range(r + 1):
            x = x_base_left + c * spacing
            create_alien(x, y, speed, hp, amplitude)
    
    x_base_right = SCREEN_WIDTH - 60
    for r in range(4):
        y = y_start + r * spacing
        for c in range(r + 1):
            x = x_base_right - (r * spacing) + c * spacing
            create_alien(x, y, speed, hp, amplitude)

    y_center_start = y_start + 4 * spacing + 20
    spacing_c = 40
    create_alien(center_x, y_center_start, speed, hp, amplitude)
    create_alien(center_x - spacing_c, y_center_start + spacing_c, speed, hp, amplitude)
    create_alien(center_x + spacing_c, y_center_start + spacing_c, speed, hp, amplitude)
    create_alien(center_x - 2*spacing_c, y_center_start + 2*spacing_c, speed, hp, amplitude)
    create_alien(center_x + 2*spacing_c, y_center_start + 2*spacing_c, speed, hp, amplitude)


def spawn_diamond_plus(hp, speed, amplitude):
    center_x = SCREEN_WIDTH // 2
    y_start = 50
    spacing = 40
    rows = [1, 3, 5, 7, 9, 5]
    y_offset = y_start

    for count in rows:
        start_x = center_x - (count - 1) * spacing // 2

        for i in range(count):
            x = start_x + i * spacing
            create_alien(x, y_offset, speed, hp, amplitude)

        y_offset += spacing

def get_stationary_guard_positions():
    coords = []
    rows, cols = 3, 5
    spacing = 35
    
    start_y = 300
    
    center_x_left = SCREEN_WIDTH // 2 - 120 
    start_x_left = center_x_left - (cols * spacing / 2) + (spacing / 2) 
    
    center_x_right = SCREEN_WIDTH // 2 + 120 
    start_x_right = center_x_right - (cols * spacing / 2) + (spacing / 2) 

    for r in range(rows):
        y = start_y + r * spacing
        for c in range(cols):
            x_left = start_x_left + c * spacing - (spacing / 2) 
            coords.append((x_left, y))
            
            x_right = start_x_right + c * spacing - (spacing / 2) 
            coords.append((x_right, y))
            
    return coords 


def spawn_boss_alien():
    global boss_phase, GUARD_ALIEN_DATA
    center_x = SCREEN_WIDTH // 2
    
    alien_group.empty()
    alien_bullets_group.empty()
    
    boss_y_start = 120 

    guard_speed = 0.03 
    guard_amplitude = SCREEN_WIDTH // 6 
    guard_hp = alien_hp_for_wave(5) 

    TOTAL_BOSS_HP = 100 
    
    boss_hp = TOTAL_BOSS_HP 
    boss_speed = 0.05
    boss_amplitude = SCREEN_WIDTH // 4 

    a = Alien(center_x, boss_y_start, boss_speed, hp=boss_hp, amplitude=boss_amplitude, is_boss=True)
    alien_group.add(a)

    guard_positions = get_stationary_guard_positions()

    for x, y in guard_positions:
        create_alien(x, y, guard_speed, guard_hp, guard_amplitude, is_guard=True, relative_pos=None)

    boss_phase = 1 

def drop_item_after_wave(wave, pos):
    if pos is None:
        pos = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)
    kind = wave_reward.get(wave, None)
    if kind:
        powerup_group.add(PowerUp(pos[0], pos[1] + 20, kind)) 

last_killed_alien_pos = None
spawn_alien_for_wave(current_wave)
player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100)
spaceship_group.add(player)

run = True
drop_spawned_this_wave = False

while run:
    clock.tick(fps)
    for event in pygame.event.get():
        if event.type == QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx,my = pygame.mouse.get_pos()
            if game_state == "menu":
                if start_rect.collidepoint(mx,my):
                    game_state = "playing"
                    countdown = 3
                    last_countdown = pygame.time.get_ticks()
                if quit_rect.collidepoint(mx,my):
                    run = False
                if credits_rect.collidepoint(mx,my):
                    game_state = "credit"
            elif game_state == "credit":
                if back_rect.collidepoint(mx,my):
                    game_state = "menu"
            elif game_state == "playing":
                if not paused and game_over == 0:
                    if pause_rect.collidepoint(mx,my):
                        paused = not paused
                elif paused:
                    if pause_resume_rect.collidepoint(mx,my):
                        paused = False
                    if pause_restart_rect.collidepoint(mx,my):
                        current_wave = 1
                        score = 0
                        game_over = 0
                        spawn_alien_for_wave(current_wave)

                        bullet_group.empty(); alien_bullets_group.empty(); explosion_group.empty(); powerup_group.empty(); asteroid_group.empty()
                        spaceship_group.empty()

                        player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT-100, health=5); spaceship_group.add(player)

                        drop_spawned_this_wave = False
                        wave_transition = False
                        countdown_started_after_drop = False
                        last_killed_alien_pos = None 
                        boss_phase = 1
                        GUARD_ALIEN_DATA = []

                        countdown = 3
                        last_countdown = pygame.time.get_ticks()
                        paused = False
                    if pause_menu_rect.collidepoint(mx,my):
                        game_state = "menu"
                        paused = False
                
                if countdown == 0 and game_over != 0:
                    if restart_rect.collidepoint(mx,my):
                        current_wave = 1
                        score = 0
                        game_over = 0
                        spawn_alien_for_wave(current_wave)
                        
                        bullet_group.empty(); alien_bullets_group.empty(); explosion_group.empty(); powerup_group.empty(); asteroid_group.empty()
                        spaceship_group.empty()
                        
                        player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT-100, health=5); spaceship_group.add(player)
                        drop_spawned_this_wave = False
                        wave_transition = False
                        countdown_started_after_drop = False
                        last_killed_alien_pos = None 
                        boss_phase = 1
                        GUARD_ALIEN_DATA = []
                        countdown = 3
                        last_countdown = pygame.time.get_ticks()
                    if go_back_rect.collidepoint(mx,my):
                        game_state = "menu"
                        current_wave = 1
                        score = 0
                        game_over = 0
                        spawn_alien_for_wave(current_wave)
                        bullet_group.empty(); alien_bullets_group.empty(); explosion_group.empty(); powerup_group.empty(); asteroid_group.empty() 
                        spaceship_group.empty()
                        player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT-100, health=5); spaceship_group.add(player) 
                        drop_spawned_this_wave = False
                        wave_transition = False
                        countdown_started_after_drop = False
                        last_killed_alien_pos = None
                        boss_phase = 1
                        GUARD_ALIEN_DATA = []
                        countdown = 3
                        last_countdown = pygame.time.get_ticks()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                if game_state == "playing" and game_over == 0:
                    paused = not paused

    if game_state == "menu":
        draw_bg()
        draw_text("SPACE SHOOTER", font40, WHITE, SCREEN_WIDTH//2 - 150, 260)
        draw_button("START", start_rect, font30, WHITE)
        draw_button("QUIT", quit_rect, font30, WHITE)
        draw_button("CREDITS", credits_rect, font30, WHITE)
        pygame.display.update()
        continue

    if game_state == "credit":
        draw_bg()
        draw_text("CREDITS", font40, WHITE, SCREEN_WIDTH//2 - 60, 100)
        draw_text("Game developed by NatanKriwil", font30, WHITE, 100, 200)
        draw_button("BACK", back_rect, font30, WHITE)
        pygame.display.update()
        continue

    if game_state == "playing":
        draw_bg()
        draw_button("||", pause_rect, font30, WHITE)
        draw_text(f"Score: {score}", font30, WHITE, 10, 10)
        draw_text(f"Wave: {current_wave}/{max_waves}", font30, WHITE, SCREEN_WIDTH - 200, 10)

        if not paused:
            if countdown == 0:
                if game_over == 0:
                    game_over = player.update()
                    bullet_group.update()
                    alien_group.update()
                    alien_bullets_group.update()
                    explosion_group.update()
                    powerup_group.update()
                    
                    if len(spaceship_group) > 0: 
                        asteroid_group.update(player.rect)
                    else:
                        asteroid_group.empty()
                    
                    now = pygame.time.get_ticks()

                    if current_wave == 5:
                        boss_interval = 600
                        guard_interval = 1200

                        boss = next((a for a in alien_group if a.is_boss), None)
                        guards = [a for a in alien_group if a.is_guard]

                        if boss and now - boss.last_shot_time > boss_interval:
                            boss.last_shot_time = now
                            ab_speed = 6
                            
                            dx_options = [0, 0, 1.5, -1.5, 3.0, -3.0] 
                            dx = random.choice(dx_options)
                            
                            alien_bullets_group.add(AlienBullet(boss.rect.centerx, boss.rect.bottom + 10, ab_speed, dx)) 

                        if guards and now - last_alien_shot > guard_interval:
                            shooter = random.choice(guards)
                            ab_speed = max(3, int(3 * difficulty_multiplier(current_wave))) 
                            alien_bullets_group.add(AlienBullet(shooter.rect.centerx, shooter.rect.bottom + 10, ab_speed, dx=0)) 
                            last_alien_shot = now
                    
                    else:
                        interval = max(200, int(alien_cooldown / difficulty_multiplier(current_wave)))
                        if now - last_alien_shot > interval:
                            if len(alien_group.sprites()) > 0 and len(alien_bullets_group) < 15: 
                                shooter = random.choice(alien_group.sprites())
                                ab_speed = max(3, int(3 * difficulty_multiplier(current_wave))) 
                                alien_bullets_group.add(AlienBullet(shooter.rect.centerx, shooter.rect.bottom + 10, ab_speed, dx=0))
                                last_alien_shot = now
                    
                    if current_wave == 5 and len(spaceship_group) > 0:
                        if random.randint(1, 180) == 1:
                            asteroid_group.add(Asteroid(random.randint(0, SCREEN_WIDTH), 0))
                    
                    if len(alien_group) == 0 and not wave_transition and current_wave < max_waves:
                        wave_transition = True
                        wave_transition_timer = pygame.time.get_ticks()
                        drop_spawned_this_wave = False
                        countdown_started_after_drop = False

                    elif len(alien_group) == 0 and current_wave >= max_waves:
                        game_over = 1 
            
            if wave_transition:
                draw_text("PREPARING NEXT WAVE...", font30, WHITE, SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 40)
                
                if not drop_spawned_this_wave:
                    pos = last_killed_alien_pos if last_killed_alien_pos else (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)
                    drop_item_after_wave(current_wave, pos)
                    drop_spawned_this_wave = True

                if drop_spawned_this_wave and len(powerup_group) == 0:
                    if not countdown_started_after_drop:
                        countdown = 3
                        last_countdown = pygame.time.get_ticks()
                        countdown_started_after_drop = True

                if countdown_started_after_drop and countdown > 0:
                    draw_text("GET READY!", font40, WHITE, SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT//2 + 50)
                    draw_text(str(countdown), font40, WHITE, SCREEN_WIDTH//2 - 10, SCREEN_HEIGHT//2 + 100)
                    if pygame.time.get_ticks() - last_countdown > 1000:
                        countdown -= 1
                        last_countdown = pygame.time.get_ticks()
                
                elif countdown == 0 and countdown_started_after_drop:
                    current_wave += 1
                    spawn_alien_for_wave(current_wave)
                    bullet_group.empty(); alien_bullets_group.empty()
                    wave_transition = False
                    countdown_started_after_drop = False
                    drop_spawned_this_wave = False
                    last_killed_alien_pos = None 

            if not wave_transition and countdown > 0:
                draw_text("GET READY!", font40, WHITE, SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT//2 + 50)
                draw_text(str(countdown), font40, WHITE, SCREEN_WIDTH//2 - 10, SCREEN_HEIGHT//2 + 100)
                if pygame.time.get_ticks() - last_countdown > 1000:
                    countdown -= 1
                    last_countdown = pygame.time.get_ticks()

        spaceship_group.draw(screen)
        for s in spaceship_group.sprites():
            s.draw_health_bar()
            
        bullet_group.draw(screen)
        alien_group.draw(screen)
        alien_bullets_group.draw(screen)
        explosion_group.draw(screen)
        powerup_group.draw(screen)
        asteroid_group.draw(screen)

        for a in alien_group:
            if a.is_boss:
                a.draw_health_bar()
                
        if paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,150))
            screen.blit(overlay, (0,0))
            draw_text("PAUSED", font40, WHITE, SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 - 150)
            draw_button("RESUME", pause_resume_rect, font30, WHITE)
            draw_button("RESTART", pause_restart_rect, font30, WHITE)
            draw_button("MENU", pause_menu_rect, font30, WHITE)
        
        if countdown == 0 and game_over != 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,150))
            screen.blit(overlay, (0,0))
            if game_over == -1:
                draw_text("GAME OVER!", font40, WHITE, SCREEN_WIDTH//2 - 125, SCREEN_HEIGHT//2 - 50)
            elif game_over == 1:
                draw_text("YOU WIN!", font40, WHITE, SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50)
            draw_button("RESTART", restart_rect, font30, WHITE)
            draw_button("MENU UTAMA", go_back_rect, font30, WHITE)

        pygame.display.update()

pygame.quit()
