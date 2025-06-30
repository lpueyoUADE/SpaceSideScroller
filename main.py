import pygame
# import sys
import random
import asyncio
from enum import Enum


# =============================
# Configuración del juego
# =============================
WIDTH = 600
HEIGHT = 400
FPS = 60

# =============================
# Inicialización
# =============================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sidescroller Espacial")
clock = pygame.time.Clock()

# Fuentes
font_path = "Assets/Fonts/Silkscreen/Silkscreen-Regular.ttf"
font_bold_path = "Assets/Fonts/Silkscreen/Silkscreen-Bold.ttf"
font = pygame.font.Font(font_path, 24)
font_bold_large = pygame.font.Font(font_bold_path, 48)

# Cursor
# Ocultar cursor por defecto
pygame.mouse.set_visible(False)
cursor_image = pygame.image.load("Assets/Images/Icons/Cursor.png").convert_alpha()

# =============================
# Música de fondo
# =============================
pygame.mixer.music.load("Assets/Audio/Music/StageSelect.ogg")
pygame.mixer.music.play(-1) # Repite indefinidamente
pygame.mixer.music.set_volume(0.2)

# =============================
# Efectos de sonido
# =============================
shoot_sound = pygame.mixer.Sound("Assets/Audio/Effects/Lasershoot.ogg")
shoot_sound.set_volume(0.3)

hit_sound = pygame.mixer.Sound("Assets/Audio/Effects/Explosion.ogg")
hit_sound.set_volume(0.3)

death_sound = pygame.mixer.Sound("Assets/Audio/Effects/Explosion2.ogg")
death_sound.set_volume(0.3)

# =============================
# Parallax
# =============================
parallax_layers_config = [
    {"path": "Assets/Images/Parallax/Nivel1/1.png", "speed": 0.15},
    {"path": "Assets/Images/Parallax/Nivel1/2.png", "speed": 0.30},
    {"path": "Assets/Images/Parallax/Nivel1/3.png", "speed": 0.45},
    {"path": "Assets/Images/Parallax/Nivel1/4.png", "speed": 0.60},
    {"path": "Assets/Images/Parallax/Nivel1/5.png", "speed": 0.75},
    {"path": "Assets/Images/Parallax/Nivel1/6.png", "speed": 0.90}
]

class ParallaxLayer:
    def __init__(self, image_path, speed):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (WIDTH, HEIGHT))
        self.speed = speed
        self.x = 0

    def update(self, dt):
        self.x -= self.speed * dt * 0.1
        if self.x <= -WIDTH:
            self.x += WIDTH

    def draw(self, surface):
        surface.blit(self.image, (self.x, 0))
        surface.blit(self.image, (self.x + WIDTH, 0))

parallax_layers = [ParallaxLayer(layer["path"], layer["speed"]) for layer in parallax_layers_config]

# =============================
# Proyectil
# =============================
class Bullet:
    def __init__(self, pos, image_path, direction=1):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        
        self.speed = 800 * direction
        
        self.lifetime = 1500
        self.age = 0

    def update(self, dt):
        self.rect.x += self.speed * dt / 1000
        self.age += dt

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def is_off_screen(self):
        return self.rect.right < 0 or self.rect.right > WIDTH
    
    def is_alive(self):
        return self.age < self.lifetime

    def destroy(self):
        self.age = self.lifetime
# =============================
# Naves
# =============================
class Spaceship:
    def __init__(self, image, bullet_image, bullet_direction, start_pos, speed, shoot_cooldown, health):
        self.original_image = pygame.image.load(image).convert_alpha()
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=start_pos)
        self.bullet_image = bullet_image
        self.bullet_direction = bullet_direction
        self.bullets = []

        self.speed = speed
        self.shoot_cooldown = shoot_cooldown
        self.last_shot_time = 0
        self.health = health

    def move(self):
        pass

    def update(self, dt):
        self.move(dt)
        self.rect = self.image.get_rect(center=self.rect.center)

        self.last_shot_time += dt

        self.bullets = [b for b in self.bullets if not b.is_off_screen() and b.is_alive()]
        for bullet in self.bullets:
            bullet.update(dt)

    def draw(self, surface):
        surface.blit(self.image, self.rect)        
        for bullet in self.bullets:
            bullet.draw(surface)

    def shoot(self):
        if self.last_shot_time >= self.shoot_cooldown:
            self.bullets.append(Bullet(self.rect.center, self.bullet_image, self.bullet_direction))
            shoot_sound.play()
            self.last_shot_time = 0

    def take_damage(self, amount):
        self.health -= amount

        if(self.is_dead()):
            death_sound.play()
        else:
            hit_sound.play()

    def is_off_screen(self):
        return self.rect.right < 0
    
    def is_dead(self):
        return self.health <= 0

# Clase para la nave del jugador
class Player(Spaceship):
    def move(self, dt):
        keys = pygame.key.get_pressed()

        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_w]: direction.y -= 1
        if keys[pygame.K_s]: direction.y += 1
        if keys[pygame.K_a]: direction.x -= 1
        if keys[pygame.K_d]: direction.x += 1

        self.rect.x += direction.x * self.speed * dt / 1000
        self.rect.y += direction.y * self.speed * dt / 1000

        self.rect.clamp_ip(screen.get_rect())

# Clase para enemigos
class Enemy(Spaceship):
    def move(self, dt):
        self.rect.x -= self.speed * dt / 1000

    def update(self, dt):
        super().update(dt)
        self.shoot()

# =============================
# Fábrica de naves
# =============================
class SpaceshipFactory:
    @classmethod
    def new_player(cls):
        return Player(
            image="Assets/Images/Ships/Player/ship003.png",
            bullet_image="Assets/Images/Bullets/PlayerBullet.png",
            bullet_direction=1,
            start_pos=(WIDTH // 4, HEIGHT // 2),
            speed=600,
            shoot_cooldown=200,
            health=3
        )

    @classmethod
    def new_enemy(cls):
        return Enemy(
            image="Assets/Images/Ships/Enemies/Enemy005.png",
            bullet_image="Assets/Images/Bullets/EnemyBullet.png",
            bullet_direction=-1,
            start_pos=(WIDTH + 50, random.randint(50, HEIGHT - 50)),
            speed=300,
            shoot_cooldown=700 + random.randint(0, 500),
            health=2
        )

# =============================
# Reiniciar el juego
# =============================
def restart_game():
    global player, enemies, score, game_time, current_screen
    player = SpaceshipFactory.new_player()
    enemies = []
    score = 0
    game_time = 0
    current_screen = Screens.GAMEPLAY
    pygame.mixer.music.rewind()
    pygame.mixer.music.play(-1)

# =============================
# Pantallas
# =============================
class Screens(Enum):
    GAMEPLAY = 1
    PAUSE = 2
    DEFEAT = 3

# =============================
# Botones
# =============================
def draw_button(surface, rect, text, hover=False):
    color = (255, 255, 0) if hover else (255, 255, 255)
    txt = font.render(text, True, color)
    surface.blit(txt, txt.get_rect(center=rect.center))

def draw_gameplay_UI():
    # Mostrar vida del jugador
    vida_text = font.render(f"VIDA: {player.health}", True, (255, 100, 100))
    screen.blit(vida_text, (WIDTH - vida_text.get_width() - 10, HEIGHT - 80))

    # Mostrar puntos del jugador
    score_text = font.render(f"PUNTOS: {score}", True, (255, 255, 100))
    screen.blit(score_text,(WIDTH - score_text.get_width() - 10, HEIGHT - 40))

    # Mostrar reloj en pantalla
    minutes = int(game_time // 60000)
    seconds = int((game_time % 60000) // 1000)
    time_text = font.render(f"{minutes:02}:{seconds:02}", True, (255, 255, 255))
    screen.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 10))

def draw_pause_UI(mouse_pos):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    pausa_text = font_bold_large.render("PAUSA", True, (255, 255, 0))
    screen.blit(pausa_text, (WIDTH // 2 - pausa_text.get_width() // 2, 100))

    controles = [
        "[WASD] - Mover nave",
        "[Mouse Izq.] - Disparar",
        "[ESC] - Pausar"
    ]

    for i, linea in enumerate(controles):
        control_text = font.render(linea, True, (255, 255, 255))
        screen.blit(control_text, (40, HEIGHT - 100 + i * 20))

    draw_button(screen, button_restart, "Reintentar", button_restart.collidepoint(mouse_pos))

def draw_defeat_UI(mouse_pos):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    score_text = font.render(f"PUNTOS: {score}", True, (255, 255, 100))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2,  HEIGHT // 2 + 40))

    minutes = int(game_time // 60000)
    seconds = int((game_time % 60000) // 1000)
    time_text = font.render(f"TIEMPO: {minutes:02}:{seconds:02}", True, (255, 255, 100))
    screen.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, HEIGHT // 2 + 80))

    derrota_text = font_bold_large.render("DERROTA", True, (255, 80, 80))
    screen.blit(derrota_text, (WIDTH // 2 - derrota_text.get_width() // 2, 100))

    draw_button(screen, button_restart, "Reintentar", button_restart.collidepoint(mouse_pos))

# =============================
# Variables de estado
# =============================
# Condición para seguir jugando
running = True

# Jugador
player = SpaceshipFactory.new_player()
score = 0
game_time = 0

# Enemigos
enemies = []
spawn_timer = 0
spawn_interval = 3000 # milisegundos

# Pantalla inicial
current_screen = Screens.GAMEPLAY

# Botón de reinicio
button_restart = pygame.Rect(WIDTH // 2 - 80, HEIGHT // 2 - 40, 160, 40)

# =============================
# Bucle principal
# =============================
async def main():
    global running, player, score, game_time, enemies, spawn_timer, spawn_interval, current_screen, button_restart
    while running:
        # Limitador de FPS
        dt = clock.tick(FPS)
        await asyncio.sleep(0) 

        # Leo la Posición del mouse
        mouse_pos = pygame.mouse.get_pos()  
        
        # Eventos del teclado y mouse
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if current_screen is Screens.GAMEPLAY:
                            current_screen = Screens.PAUSE
                            pygame.mixer.music.pause()

                        elif current_screen is Screens.PAUSE:
                            current_screen = Screens.GAMEPLAY
                            pygame.mixer.music.unpause()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if current_screen is Screens.GAMEPLAY:
                        player.shoot()

                    else:
                        if button_restart.collidepoint(event.pos):
                            restart_game()

        if current_screen is Screens.GAMEPLAY:
            game_time += dt

            if player.is_dead():
                current_screen = Screens.DEFEAT
                pygame.mixer.music.pause()

            # Actualizo el parallax
            for layer in parallax_layers:
                layer.update(dt)

            # Actualizo el player
            player.update(dt)

            # Enemigos
            spawn_timer += dt
            if spawn_timer >= spawn_interval:
                enemies.append(SpaceshipFactory.new_enemy())
                spawn_timer = 0

            # Actualizo los enemigos
            for enemy in enemies:
                enemy.update(dt)

                # Checkeo si una bala del jugador choca con un enemigo
                for bullet in player.bullets:
                    if enemy.rect.colliderect(bullet.rect):
                        enemy.take_damage(1)
                        bullet.destroy()

                # Checkeo si una bala enemiga choca con el jugador
                for bullet in enemy.bullets:
                    if player.rect.colliderect(bullet.rect):
                        player.take_damage(1)
                        bullet.destroy()

                # Checkeo si un enemigo choca con el jugador
                if player.rect.colliderect(enemy.rect):
                    player.take_damage(1)
                    enemy.take_damage(3)

                # Si el enemigo muere, sumo 1 punto
                if enemy.is_dead():
                    score += 1

            # Dejo en la lista solo aquellos enemigos que están vivos y dentro del mapa
            enemies = [e for e in enemies if not e.is_off_screen() and not e.is_dead()]

        # Renderizado
        screen.fill((0, 0, 0))

        for layer in parallax_layers:
            layer.draw(screen)
        player.draw(screen)

        for enemy in enemies:
            enemy.draw(screen)

        # UI
        if current_screen is Screens.GAMEPLAY:
            draw_gameplay_UI()

        if current_screen is Screens.PAUSE:
            draw_pause_UI(mouse_pos)

        if current_screen is Screens.DEFEAT:
            draw_defeat_UI(mouse_pos)

        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        screen.blit(fps_text, (WIDTH - fps_text.get_width() - 10, 10))
        
        cursor_rect = cursor_image.get_rect(center=mouse_pos)
        screen.blit(cursor_image, cursor_rect)

        pygame.display.flip()

asyncio.run(main())
