import pygame
from pygame import mixer
from pygame.locals import *
pygame.init()
import random

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 600
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("SPACE SHOOTER")

font30 = pygame.font.SysFont("constantia", 30)
font40 = pygame.font.SysFont("constantia", 40)

explosion_sound = mixer.Sound("SPACE SHOOTER/img/explosion.wav")
explosion_sound.set_volume(0.1)

explosion2_sound = mixer.Sound("SPACE SHOOTER/img/explosion2.wav")
explosion2_sound.set_volume(0.25)

laser_sound = mixer.Sound("SPACE SHOOTER/img/laser.wav")
laser_sound.set_volume(0.1)

rows = 5
cols = 5
alien_cooldown = 1000
last_alien_shot = pygame.time.get_ticks()
countdown = 3
last_countdown = pygame.time.get_ticks()
game_over = 0

red = (255, 0, 0)
green = (0, 255, 0)
white = (255, 255, 255)

bg = pygame.image.load("SPACE SHOOTER/img/bg.png")

def draw_bg():
    screen.blit(bg, (0, 0))

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_button(text, rect, font, text_col, rect_col=(255,255,255)):
    pygame.draw.rect(screen, rect_col, rect, 2)
    img = font.render(text, True, text_col)
    text_rect = img.get_rect(center=rect.center)
    screen.blit(img, text_rect)

game_state = "menu"

class spaceship(pygame.sprite.Sprite):
    def __init__(self, x, y, health=3):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("SPACE SHOOTER/img/spaceship.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.health_start = health
        self.health_remaining = health
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        speed = 8
        cooldown = 300
        game_over = 0

        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT] and self.rect.left > 0: 
            self.rect.x -= speed
        if key[pygame.K_RIGHT] and self.rect.right < screen_width: 
            self.rect.x += speed
            
        time_now = pygame.time.get_ticks()
        if key[pygame.K_SPACE] and time_now - self.last_shot > cooldown:
            laser_sound.play()
            bullet = bullets(self.rect.centerx, self.rect.top)
            bullet_group.add(bullet)
            self.last_shot = time_now

        self.mask = pygame.mask.from_surface(self.image)

        pygame.draw.rect(screen, red, (self.rect.x, (self.rect.bottom + 10), self.rect.width, 15))
        if self.health_remaining > 0:
            pygame.draw.rect(screen, green, (self.rect.x, (self.rect.bottom + 10), int(self.rect.width * (self.health_remaining / self.health_start)), 15))
        elif self.health_remaining <= 0:
            exp = explosion(self.rect.centerx, self.rect.centery, 3)
            explosion_group.add(exp)
            self.kill()
            game_over = -1
        return game_over

class bullets(pygame.sprite.Sprite):
    def __init__(self, x, y,):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("SPACE SHOOTER/img/bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
            self.rect.y -= 5
            if self.rect.bottom < 0:
                self.kill()
            hits = pygame.sprite.spritecollide(self, alien_group, True)
            if hits:
                self.kill()
                explosion_sound.play()
                exp = explosion(self.rect.centerx, self.rect.centery, 2)
                explosion_group.add(exp)

class aliens(pygame.sprite.Sprite):
    def __init__(self, x, y,):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("SPACE SHOOTER/img/alien.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.move_counter = 0
        self.move_direction = 1

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= self.move_direction

class alien_bullets(pygame.sprite.Sprite):
    def __init__(self, x, y,):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("SPACE SHOOTER/img/alien_bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
            self.rect.y += 2
            if self.rect.top > screen_height:
                self.kill()
            hits = pygame.sprite.spritecollide(self, spaceship_group, False, pygame.sprite.collide_mask)
            if hits:
                for ship in hits:
                    explosion2_sound.play()
                    if hasattr(ship, 'health_remaining'):
                        ship.health_remaining -= 1
                        exp = explosion(self.rect.centerx, self.rect.centery, 1)
                        explosion_group.add(exp)
                self.kill()

class explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size=1):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f"SPACE SHOOTER/img/exp{num}.png").convert_alpha()
            if size == 1:
                img = pygame.transform.scale(img, (20, 20))
            elif size == 2:
                img = pygame.transform.scale(img, (40, 40))
            elif size == 3:
                img = pygame.transform.scale(img, (160, 160))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0

    def update(self):
        explosion_speed = 3
        self.counter += 1

        if self.counter >= explosion_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]

        if self.index >= len(self.images) - 1 and self.counter >= explosion_speed:
            self.kill()

spaceship_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
alien_group = pygame.sprite.Group()
alien_bullets_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()

def spawn_alien():
    for row in range(rows):
        for col in range(cols):
            x = 100 + col * 100
            y = 100 + row * 70
            alien = aliens(x, y)
            alien_group.add(alien)

def reset_game():
    global countdown, last_countdown, game_over, player
    bullet_group.empty()
    alien_group.empty()
    alien_bullets_group.empty()
    explosion_group.empty()
    spaceship_group.empty()

    spawn_alien()

    player = spaceship(screen_width / 2, screen_height - 100)
    spaceship_group.add(player)

    countdown = 3
    last_countdown = pygame.time.get_ticks()
    game_over = 0
    
    return countdown, game_over

spawn_alien()


player = spaceship(screen_width / 2, screen_height - 100)
spaceship_group.add(player)

run = True
while run:

    clock.tick(fps)

    btn_w = 200
    btn_h = 60
    center_x = int(screen_width / 2)
    start_rect = pygame.Rect(center_x - btn_w // 2, 315 - btn_h // 2, btn_w, btn_h)
    quit_rect = pygame.Rect(center_x - btn_w // 2, 380 - btn_h // 2, btn_w, btn_h)
    credits_rect = pygame.Rect(screen_width - 130, 20, 120, 40)
    back_rect = pygame.Rect(20, 20, 100, 40)
    restart_rect = pygame.Rect(center_x - btn_w // 2, 440 - btn_h // 2, btn_w, btn_h)
    go_back_rect = pygame.Rect(center_x - btn_w // 2, 520 - btn_h // 2, btn_w, btn_h)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()

            if game_state == "menu":
                if start_rect.collidepoint(mx, my):
                    game_state = "playing"
                if quit_rect.collidepoint(mx, my):
                    run = False
                if credits_rect.collidepoint(mx, my):
                    game_state = "credit"

            if game_state == "credit":
                if back_rect.collidepoint(mx, my):
                    game_state = "menu"
            
            if game_state == "playing" and game_over != 0:
                if restart_rect.collidepoint(mx, my):
                    countdown, game_over = reset_game()
                if go_back_rect.collidepoint(mx, my):
                    game_state = "menu"
                    countdown, game_over = reset_game()

    if game_state == "menu":
        draw_bg()
        draw_text("SPACE SHOOTER", font40, white, int(screen_width / 2 - 149.5), 225)
        draw_button("START", start_rect, font30, white)
        draw_button("QUIT", quit_rect, font30, white)
        draw_button("CREDITS", credits_rect, font30, white)
        pygame.display.update()
        continue

    if game_state == "credit":
        draw_bg()
        draw_text("CREDITS", font40, white, int(screen_width / 2 - 80), 100)
        draw_text("Game developed by NatanKriwil", font30, white, 100, 200)
        draw_button("BACK", back_rect, font30, white)
        pygame.display.update()
        continue

    if game_state == "playing":
        draw_bg()

    if countdown == 0:

        time_now = pygame.time.get_ticks()
        
        if time_now - last_alien_shot > alien_cooldown and len(alien_bullets_group) < 5 and len(alien_group) > 0:
            attacking_alien = random.choice(alien_group.sprites())
            alien_bullet = alien_bullets(attacking_alien.rect.centerx, attacking_alien.rect.bottom)
            alien_bullets_group.add(alien_bullet)
            last_alien_shot = time_now

        if len(alien_group) == 0:
            game_over = 1

        if game_over == 0:

            game_over = player.update()

            bullet_group.update()
            alien_group.update()
            alien_bullets_group.update()
        else:
            pass

    if countdown > 0:
        draw_text("GET READY!", font40, white, int(screen_width / 2 - 110), int(screen_height / 2 + 50))
        draw_text(str(countdown), font40, white, int(screen_width / 2 - 10), int(screen_height / 2 + 100))
        countdown_timer = pygame.time.get_ticks()
        if countdown_timer - last_countdown > 1000:
            countdown -= 1
            last_countdown = countdown_timer

    explosion_group.update()

    spaceship_group.draw(screen)
    bullet_group.draw(screen)
    alien_group.draw(screen)
    alien_bullets_group.draw(screen)
    explosion_group.draw(screen)

    if countdown == 0 and game_over != 0:
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        if game_over == -1:
            draw_text("GAME OVER!", font40, white, int(screen_width / 2 - 125), int(screen_height / 2 - 50))
        if game_over == 1:
            draw_text("YOU WIN!", font40, white, int(screen_width / 2 - 100), int(screen_height / 2 - 50))
        draw_button("RESTART", restart_rect, font30, white)
        draw_button("BACK", go_back_rect, font30, white)

    pygame.display.update()

pygame.quit()
