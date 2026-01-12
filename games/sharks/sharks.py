import pygame
import random
import math

pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 800
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
OCEAN_BLUE = (25, 55, 120)
LIGHT_BLUE = (65, 105, 225)
DARK_BLUE = (15, 35, 80)
YELLOW = (255, 255, 0)
PURPLE = (200, 100, 255)
GRAY = (100, 100, 100)
CORAL_PINK = (255, 127, 80)
CORAL_ORANGE = (255, 140, 0)
SEAWEED_GREEN = (46, 125, 50)
SAND = (194, 178, 128)
ORANGE = (255, 165, 0)
SKIN = (255, 220, 177)

# Game setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shark Survivors")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
tiny_font = pygame.font.Font(None, 18)

# ============= SLIDER =============
class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val, label):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False
        self.handle_radius = 10
        
    def get_handle_x(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.x + ratio * self.width
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            handle_x = self.get_handle_x()
            if (abs(mouse_x - handle_x) < self.handle_radius and 
                abs(mouse_y - self.y) < self.handle_radius):
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            ratio = max(0, min(1, (mouse_x - self.x) / self.width))
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            return True
        return False
    
    def draw(self, screen):
        # Background bar
        pygame.draw.rect(screen, (60, 60, 60), (self.x, self.y - 5, self.width, 10))
        pygame.draw.rect(screen, (100, 100, 100), (self.x, self.y - 5, self.width, 10), 2)
        
        # Handle
        handle_x = self.get_handle_x()
        pygame.draw.circle(screen, (200, 200, 200), (int(handle_x), self.y), self.handle_radius)
        pygame.draw.circle(screen, WHITE, (int(handle_x), self.y), self.handle_radius - 2)
        
        # Label and value
        label_text = tiny_font.render(self.label, True, WHITE)
        screen.blit(label_text, (self.x, self.y - 25))
        
        value_text = tiny_font.render(f"{self.value:.2f}x", True, YELLOW)
        screen.blit(value_text, (self.x + self.width + 10, self.y - 8))

# ============= UTILS =============
class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance_to(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx**2 + dy**2)
    
    def normalize(self):
        length = math.sqrt(self.x**2 + self.y**2)
        if length > 0:
            return Vector2(self.x / length, self.y / length)
        return Vector2(0, 0)

def rotate_point(x, y, cx, cy, angle):
    tx = x - cx
    ty = y - cy
    rx = tx * math.cos(angle) - ty * math.sin(angle)
    ry = tx * math.sin(angle) + ty * math.cos(angle)
    return (rx + cx, ry + cy)

def draw_rotated_ellipse(surface, color, rect, angle, width=0):
    target_rect = pygame.Rect(rect)
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(shape_surf, color, (0, 0, *target_rect.size), width)
    rotated_surf = pygame.transform.rotate(shape_surf, -math.degrees(angle))
    surface.blit(rotated_surf, rotated_surf.get_rect(center=target_rect.center))   

# ============= CAMERA =============
class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
    
    def update(self, target):
        self.x = target.x - WIDTH // 2
        self.y = target.y - HEIGHT // 2
    
    def apply(self, entity):
        return (entity.x - self.x, entity.y - self.y)
    
    def apply_rect(self, rect):
        return pygame.Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)

# ============= OBSTACLES =============
class Obstacle:
    def __init__(self, x, y, width, height, obstacle_type='coral'):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, screen, camera):
        screen_rect = camera.apply_rect(self.rect)
        if self.type == 'coral':
            pygame.draw.ellipse(screen, CORAL_PINK, screen_rect)
            pygame.draw.ellipse(screen, CORAL_ORANGE, screen_rect, 3)
        elif self.type == 'rock':
            pygame.draw.ellipse(screen, GRAY, screen_rect)
            pygame.draw.ellipse(screen, (70, 70, 70), screen_rect, 2)
        elif self.type == 'seaweed':
            for i in range(3):
                offset_x = screen_rect.x + i * (screen_rect.width // 3)
                pygame.draw.line(screen, SEAWEED_GREEN, 
                               (offset_x, screen_rect.bottom), 
                               (offset_x + random.randint(-5, 5), screen_rect.top), 5)

# ============= WEAPONS =============
class Weapon:
    def __init__(self, weapon_type='harpoon'):
        self.type = weapon_type
        self.level = 1
        
        if weapon_type == 'harpoon':
            self.damage = 10
            self.cooldown = 60
            self.projectile_speed = 10
            self.pierce = 1
        elif weapon_type == 'trident':
            self.damage = 10
            self.cooldown = 200
            self.projectile_speed = 5
            self.pierce = 3
        elif weapon_type == 'net':
            self.damage = 5
            self.cooldown = 250
            self.projectile_speed = 2
            self.pierce = 1
            self.aoe_radius = 80
        elif weapon_type == 'torpedo':
            self.damage = 5
            self.cooldown = 120
            self.projectile_speed = 12
            self.pierce = 1
            self.explosive = True
    
    def upgrade(self):
        self.level += 1
        self.damage = int(self.damage * 1.2)
        self.cooldown = max(10, int(self.cooldown * 0.9))

# ============= PLAYER =============
class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.size = 25
        self.speed = 3.5
        self.max_hp = 100
        self.hp = self.max_hp
        self.level = 1
        self.xp = 0
        self.xp_to_next = 10
        self.facing_angle = 0
        self.last_move = Vector2(0, -1)
        self.weapons = [Weapon('harpoon')]
        self.weapon_cooldowns = {}
        
    def move(self, keys, obstacles, speed_multiplier=1.0):
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        
        if dx != 0 or dy != 0:
            self.last_move = Vector2(dx, dy).normalize()
            self.facing_angle = math.atan2(dy, dx)
        
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        
        actual_speed = self.speed * speed_multiplier
        new_x = self.x + dx * actual_speed
        new_y = self.y + dy * actual_speed
        
        player_rect = pygame.Rect(new_x - self.size, new_y - self.size, self.size * 2, self.size * 2)
        
        can_move_x = True
        can_move_y = True
        
        for obstacle in obstacles:
            if player_rect.colliderect(obstacle.rect):
                test_rect_x = pygame.Rect(new_x - self.size, self.y - self.size, self.size * 2, self.size * 2)
                if test_rect_x.colliderect(obstacle.rect):
                    can_move_x = False
                
                test_rect_y = pygame.Rect(self.x - self.size, new_y - self.size, self.size * 2, self.size * 2)
                if test_rect_y.colliderect(obstacle.rect):
                    can_move_y = False
        
        if can_move_x:
            self.x = new_x
        if can_move_y:
            self.y = new_y
    
    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0
    
    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            return True
        return False
    
    def add_weapon(self, weapon_type):
        for weapon in self.weapons:
            if weapon.type == weapon_type:
                weapon.upgrade()
                return
        self.weapons.append(Weapon(weapon_type))
    
    def draw(self, screen, camera):
        screen_pos = camera.apply(self)
        cx, cy = int(screen_pos[0]), int(screen_pos[1])
        
        body_width = 18
        body_height = 30
        body_rect = pygame.Rect(cx - body_width//2, cy - body_height//2, body_width, body_height)
        draw_rotated_ellipse(screen, (50, 50, 50), body_rect, self.facing_angle)
        
        arm_offset_x = 12 * math.cos(self.facing_angle + math.pi/2)
        arm_offset_y = 12 * math.sin(self.facing_angle + math.pi/2)
        
        arm1_start = (cx - arm_offset_x, cy - arm_offset_y)
        arm1_end = (cx - arm_offset_x * 1.8 + 8 * math.cos(self.facing_angle), 
                    cy - arm_offset_y * 1.8 + 8 * math.sin(self.facing_angle))
        pygame.draw.line(screen, (50, 50, 50), arm1_start, arm1_end, 6)
        pygame.draw.circle(screen, SKIN, (int(arm1_end[0]), int(arm1_end[1])), 5)
        
        arm2_start = (cx + arm_offset_x, cy + arm_offset_y)
        arm2_end = (cx + arm_offset_x * 1.8 + 8 * math.cos(self.facing_angle), 
                    cy + arm_offset_y * 1.8 + 8 * math.sin(self.facing_angle))
        pygame.draw.line(screen, (50, 50, 50), arm2_start, arm2_end, 6)
        pygame.draw.circle(screen, SKIN, (int(arm2_end[0]), int(arm2_end[1])), 5)
        
        leg_offset_x = 8 * math.cos(self.facing_angle + math.pi/2)
        leg_offset_y = 8 * math.sin(self.facing_angle + math.pi/2)
        back_offset_x = -15 * math.cos(self.facing_angle)
        back_offset_y = -15 * math.sin(self.facing_angle)
        
        leg1_start = (cx - leg_offset_x + back_offset_x, cy - leg_offset_y + back_offset_y)
        leg1_end = (cx - leg_offset_x + back_offset_x * 1.5, cy - leg_offset_y + back_offset_y * 1.5)
        pygame.draw.line(screen, (255, 140, 0), leg1_start, leg1_end, 8)
        
        leg2_start = (cx + leg_offset_x + back_offset_x, cy + leg_offset_y + back_offset_y)
        leg2_end = (cx + leg_offset_x + back_offset_x * 1.5, cy + leg_offset_y + back_offset_y * 1.5)
        pygame.draw.line(screen, (255, 140, 0), leg2_start, leg2_end, 8)
        
        tank_x = cx - 8 * math.cos(self.facing_angle)
        tank_y = cy - 8 * math.sin(self.facing_angle)
        tank_rect = pygame.Rect(tank_x - 6, tank_y - 10, 12, 20)
        draw_rotated_ellipse(screen, (180, 180, 180), tank_rect, self.facing_angle)
        
        head_x = cx + 12 * math.cos(self.facing_angle)
        head_y = cy + 12 * math.sin(self.facing_angle)
        pygame.draw.circle(screen, SKIN, (int(head_x), int(head_y)), 10)
        
        mask_x = head_x + 6 * math.cos(self.facing_angle)
        mask_y = head_y + 6 * math.sin(self.facing_angle)
        pygame.draw.circle(screen, (50, 150, 200), (int(mask_x), int(mask_y)), 8)
        pygame.draw.circle(screen, (100, 200, 255), (int(mask_x), int(mask_y)), 6)
        
        gun_x = cx + 15 * math.cos(self.facing_angle)
        gun_y = cy + 15 * math.sin(self.facing_angle)
        gun_end_x = gun_x + 20 * math.cos(self.facing_angle)
        gun_end_y = gun_y + 20 * math.sin(self.facing_angle)
        pygame.draw.line(screen, (80, 80, 80), (gun_x, gun_y), (gun_end_x, gun_end_y), 5)
        pygame.draw.circle(screen, (60, 60, 60), (int(gun_x), int(gun_y)), 4)

# ============= PROJECTILES =============
class Projectile:
    def __init__(self, x, y, target_x, target_y, weapon, damage_multiplier=1.0):
        self.x = x
        self.y = y
        self.weapon = weapon
        self.damage = weapon.damage * damage_multiplier
        self.speed = weapon.projectile_speed
        self.size = 8
        self.pierce_count = weapon.pierce
        self.hit_enemies = set()
        
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
            self.angle = math.atan2(dy, dx)
        else:
            self.vx = self.vy = 0
            self.angle = 0

    def collides_with_obstacle(self, obstacles):
        hitbox = pygame.Rect(
            self.x - self.size,
            self.y - self.size,
            self.size * 2,
            self.size * 2
        )
        for obs in obstacles:
            if hitbox.colliderect(obs.rect):
                return True
        return False
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        return self.pierce_count > 0
    
    def hit(self, enemy_id):
        if enemy_id not in self.hit_enemies:
            self.hit_enemies.add(enemy_id)
            self.pierce_count -= 1
            return True
        return False
    
    def draw(self, screen, camera):
        screen_pos = camera.apply(self)
        
        if self.weapon.type == 'harpoon':
            length = 20
            end_x = screen_pos[0] + length * math.cos(self.angle)
            end_y = screen_pos[1] + length * math.sin(self.angle)
            pygame.draw.line(screen, (150, 150, 150), screen_pos, (end_x, end_y), 4)
            pygame.draw.circle(screen, (200, 200, 50), (int(end_x), int(end_y)), 4)
        
        elif self.weapon.type == 'trident':
            length = 25
            end_x = screen_pos[0] + length * math.cos(self.angle)
            end_y = screen_pos[1] + length * math.sin(self.angle)
            pygame.draw.line(screen, (200, 150, 0), screen_pos, (end_x, end_y), 6)
            
            prong_angle = math.pi / 6
            prong_len = 10
            prong1_x = end_x + prong_len * math.cos(self.angle + prong_angle)
            prong1_y = end_y + prong_len * math.sin(self.angle + prong_angle)
            prong2_x = end_x + prong_len * math.cos(self.angle - prong_angle)
            prong2_y = end_y + prong_len * math.sin(self.angle - prong_angle)
            
            pygame.draw.line(screen, (200, 150, 0), (end_x, end_y), (prong1_x, prong1_y), 3)
            pygame.draw.line(screen, (200, 150, 0), (end_x, end_y), (prong2_x, prong2_y), 3)
        
        elif self.weapon.type == 'net':
            pygame.draw.circle(screen, (100, 150, 100), (int(screen_pos[0]), int(screen_pos[1])), 12)
            for i in range(4):
                angle = i * math.pi / 2
                line_end_x = screen_pos[0] + 10 * math.cos(angle)
                line_end_y = screen_pos[1] + 10 * math.sin(angle)
                pygame.draw.line(screen, (80, 120, 80), screen_pos, (line_end_x, line_end_y), 2)
        
        elif self.weapon.type == 'torpedo':
            length = 30
            end_x = screen_pos[0] + length * math.cos(self.angle)
            end_y = screen_pos[1] + length * math.sin(self.angle)
            pygame.draw.line(screen, (120, 120, 120), screen_pos, (end_x, end_y), 10)
            pygame.draw.circle(screen, RED, (int(end_x), int(end_y)), 6)

# ============= ENEMIES =============
class Enemy:
    def __init__(self, x, y, enemy_type='shark', is_elite=False, is_boss=False, difficulty_scale=1.0):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.angle = 0
        self.is_elite = is_elite
        self.is_boss = is_boss
        self.difficulty_scale = difficulty_scale
        
        if enemy_type == 'shark':
            self.size = 20
            self.speed = 2
            self.hp = 30
            self.max_hp = 30
            self.damage = 10
            self.xp_value = 5
            self.color = GRAY
        elif enemy_type == 'jellyfish':
            self.size = 18
            self.speed = 1.5
            self.hp = 20
            self.max_hp = 20
            self.damage = 15
            self.xp_value = 8
            self.color = (200, 100, 200)
            self.float_offset = random.uniform(0, math.pi * 2)
        elif enemy_type == 'eel':
            self.size = 15
            self.speed = 3
            self.hp = 25
            self.max_hp = 25
            self.damage = 12
            self.xp_value = 7
            self.color = (50, 100, 50)
        elif enemy_type == 'octopus':
            self.size = 25
            self.speed = 1
            self.hp = 60
            self.max_hp = 60
            self.damage = 20
            self.xp_value = 15
            self.color = (150, 50, 50)
        elif enemy_type == 'megalodon':
            self.size = 50
            self.speed = 2.5
            self.hp = 500
            self.max_hp = 500
            self.damage = 40
            self.xp_value = 100
            self.color = (40, 40, 40)
            self.is_boss = True
        elif enemy_type == 'kraken':
            self.size = 60
            self.speed = 0.8
            self.hp = 800
            self.max_hp = 800
            self.damage = 50
            self.xp_value = 150
            self.color = (80, 20, 20)
            self.is_boss = True
        elif enemy_type == 'piranha':
            self.size = 12
            self.speed = 4
            self.hp = 18
            self.max_hp = 18
            self.damage = 6
            self.xp_value = 6
            self.color = (200, 60, 60)

        elif enemy_type == 'hammerhead':
            self.size = 28
            self.speed = 2.2
            self.hp = 90
            self.max_hp = 90
            self.damage = 12
            self.xp_value = 20
            self.color = (120, 120, 140)

        elif enemy_type == 'crab':
            self.size = 26
            self.speed = 1.2
            self.hp = 140
            self.max_hp = 140
            self.damage = 10
            self.xp_value = 25
            self.color = (160, 80, 60)

        
        # Apply difficulty scaling (harder than before)
        hp_mult = 2.2 + (difficulty_scale - 1) * 0.7
        self.hp = int(self.hp * hp_mult)
        self.max_hp = int(self.max_hp * hp_mult)
        self.damage = int(self.damage * (0.6 + difficulty_scale * 0.4))
        self.speed *= min(.5, .25 + (difficulty_scale - 1) * 0.3)  # Speed scales slower
        
        # Elite modifiers
        if is_elite:
            self.size = int(self.size * 1.3)
            self.hp = int(self.hp * 2)
            self.max_hp = int(self.max_hp * 2)
            self.damage = int(self.damage * 1.5)
            self.speed *= 1.2
            self.xp_value = int(self.xp_value * 3)
            # Make elite color more vibrant
            self.color = tuple(min(255, c + 50) for c in self.color)
        
        # Boss modifiers
        if is_boss:
            self.xp_value = int(self.xp_value * difficulty_scale)
    
    def update(self, player, obstacles, time):
        if self.type == 'jellyfish':
            self.float_offset += 0.05
            drift_x = math.cos(self.float_offset) * 0.5
            drift_y = math.sin(self.float_offset * 0.7) * 0.5
        else:
            drift_x = drift_y = 0
        
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            self.angle = math.atan2(dy, dx)
            
            move_speed = self.speed
            if self.type == 'eel' and dist < 300:
                move_speed *= 1.5
            
            new_x = self.x + (dx / dist) * move_speed + drift_x
            new_y = self.y + (dy / dist) * move_speed + drift_y
            
            # Enemies ignore obstacles — they always move
            self.x = new_x
            self.y = new_y

    
    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0
    
    def draw(self, screen, camera, time):
        screen_pos = camera.apply(self)
        
        # Elite glow effect
        if self.is_elite:
            for i in range(3):
                glow_size = self.size + 5 + i * 3
                glow_alpha = 100 - i * 30
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*YELLOW, glow_alpha), (glow_size, glow_size), glow_size)
                screen.blit(glow_surf, (screen_pos[0] - glow_size, screen_pos[1] - glow_size))
        
        # Boss glow effect
        if self.is_boss:
            for i in range(4):
                glow_size = self.size + 10 + i * 5
                glow_alpha = 120 - i * 30
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*RED, glow_alpha), (glow_size, glow_size), glow_size)
                screen.blit(glow_surf, (screen_pos[0] - glow_size, screen_pos[1] - glow_size))
        
        # Shark & Megalodon
        body_len = self.size * 2.4
        body_w = self.size * 1.2

        # Main body
        body_rect = pygame.Rect(0, 0, body_len, body_w)
        body_rect.center = screen_pos
        draw_rotated_ellipse(screen, self.color, body_rect, self.angle)

        # Belly
        belly_rect = pygame.Rect(0, 0, body_len * 0.9, body_w * 0.6)
        belly_rect.center = screen_pos
        draw_rotated_ellipse(screen, (200, 200, 200), belly_rect, self.angle)

        # Tail
        tail_base_x = screen_pos[0] - math.cos(self.angle) * body_len * 0.5
        tail_base_y = screen_pos[1] - math.sin(self.angle) * body_len * 0.5
        tail_len = self.size * 1.3

        tail_points = [
            (tail_base_x, tail_base_y),
            (tail_base_x + math.cos(self.angle + 0.7) * tail_len,
            tail_base_y + math.sin(self.angle + 0.7) * tail_len),
            (tail_base_x + math.cos(self.angle - 0.7) * tail_len,
            tail_base_y + math.sin(self.angle - 0.7) * tail_len),
        ]
        pygame.draw.polygon(screen, self.color, tail_points)

        # Dorsal fin
        fin_x = screen_pos[0] - math.cos(self.angle) * self.size * 0.2
        fin_y = screen_pos[1] - math.sin(self.angle) * self.size * 0.2
        fin_tip = (
            fin_x - math.sin(self.angle) * self.size,
            fin_y + math.cos(self.angle) * self.size
        )
        pygame.draw.polygon(screen, self.color, [(fin_x, fin_y), fin_tip,
            (fin_x + math.cos(self.angle)*8, fin_y + math.sin(self.angle)*8)])

        # Eye
        eye_x = screen_pos[0] + math.cos(self.angle) * self.size * 0.7
        eye_y = screen_pos[1] + math.sin(self.angle) * self.size * 0.7
        pygame.draw.circle(screen, WHITE, (int(eye_x), int(eye_y)), 4)
        pygame.draw.circle(screen, BLACK, (int(eye_x), int(eye_y)), 2)

        # Megalodon teeth
        if self.type == 'megalodon':
            mouth_x = screen_pos[0] + math.cos(self.angle) * self.size * 1.1
            mouth_y = screen_pos[1] + math.sin(self.angle) * self.size * 1.1
            for i in range(-3, 4):
                tx = mouth_x + math.sin(self.angle) * i * 4
                ty = mouth_y - math.cos(self.angle) * i * 4
                pygame.draw.circle(screen, WHITE, (int(tx), int(ty)), 3)

        
        elif self.type == 'jellyfish':
            float_y_offset = math.sin(self.float_offset) * 5
            body_y = screen_pos[1] + float_y_offset
            pygame.draw.circle(screen, self.color, (int(screen_pos[0]), int(body_y)), self.size)
            pygame.draw.circle(screen, (220, 120, 220), (int(screen_pos[0]), int(body_y)), self.size - 3)
            
            num_tentacles = 8 if self.is_elite else 6
            for i in range(num_tentacles):
                angle = i * 2 * math.pi / num_tentacles + time * 0.05
                tentacle_len = self.size + 15 + math.sin(time * 0.1 + i) * 5
                end_x = screen_pos[0] + math.cos(angle) * tentacle_len
                end_y = body_y + math.sin(angle) * tentacle_len + tentacle_len * 0.5
                pygame.draw.line(screen, (180, 80, 180), (screen_pos[0], body_y), (end_x, end_y), 2)
        
        elif self.type == 'eel':
            segments = 7 if self.is_elite else 5
            segment_length = self.size
            for i in range(segments):
                wave_offset = math.sin(time * 0.1 + i * 0.5) * 8
                seg_x = screen_pos[0] - i * segment_length * 0.8 * math.cos(self.angle) + wave_offset * math.sin(self.angle)
                seg_y = screen_pos[1] - i * segment_length * 0.8 * math.sin(self.angle) - wave_offset * math.cos(self.angle)
                size = self.size - i * 2
                pygame.draw.circle(screen, self.color, (int(seg_x), int(seg_y)), max(3, size))
        
        elif self.type == 'octopus' or self.type == 'kraken':
            pygame.draw.circle(screen, self.color, (int(screen_pos[0]), int(screen_pos[1])), self.size)
            pygame.draw.circle(screen, (180, 70, 70), (int(screen_pos[0]), int(screen_pos[1])), self.size - 5)
            
            # Draw eyes for kraken
            if self.type == 'kraken':
                eye_offset = self.size * 0.3
                pygame.draw.circle(screen, YELLOW, (int(screen_pos[0] - eye_offset), int(screen_pos[1] - eye_offset)), 8)
                pygame.draw.circle(screen, RED, (int(screen_pos[0] - eye_offset), int(screen_pos[1] - eye_offset)), 4)
                pygame.draw.circle(screen, YELLOW, (int(screen_pos[0] + eye_offset), int(screen_pos[1] - eye_offset)), 8)
                pygame.draw.circle(screen, RED, (int(screen_pos[0] + eye_offset), int(screen_pos[1] - eye_offset)), 4)
            
            num_tentacles = 10 if self.type == 'kraken' else 8
            for i in range(num_tentacles):
                angle = i * 2 * math.pi / num_tentacles + time * 0.03
                tentacle_len = self.size + 20
                mid_x = screen_pos[0] + math.cos(angle) * (self.size + 10)
                mid_y = screen_pos[1] + math.sin(angle) * (self.size + 10)
                end_x = screen_pos[0] + math.cos(angle + 0.5) * tentacle_len
                end_y = screen_pos[1] + math.sin(angle + 0.5) * tentacle_len
                
                thickness = 8 if self.type == 'kraken' else 6
                pygame.draw.line(screen, self.color, (screen_pos[0], screen_pos[1]), (mid_x, mid_y), thickness)
                pygame.draw.line(screen, self.color, (mid_x, mid_y), (end_x, end_y), thickness - 2)
        
        # HP bar
        bar_width = 40 if self.is_boss else (35 if self.is_elite else 30)
        bar_height = 6 if (self.is_boss or self.is_elite) else 4
        hp_ratio = self.hp / self.max_hp
        
        bar_y = screen_pos[1] - self.size - 20
        
        # Background
        pygame.draw.rect(screen, BLACK, (screen_pos[0] - bar_width//2 - 1, bar_y - 1, bar_width + 2, bar_height + 2))
        pygame.draw.rect(screen, RED, (screen_pos[0] - bar_width//2, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (screen_pos[0] - bar_width//2, bar_y, bar_width * hp_ratio, bar_height))
        
        # Elite/Boss label
        if self.is_elite:
            elite_text = small_font.render("ELITE", True, YELLOW)
            screen.blit(elite_text, (screen_pos[0] - elite_text.get_width()//2, bar_y - 20))
        elif self.is_boss:
            boss_text = font.render("BOSS", True, RED)
            screen.blit(boss_text, (screen_pos[0] - boss_text.get_width()//2, bar_y - 35))

# ============= XP GEM =============
class XPGem:
    def __init__(self, x, y, value=5):
        self.x = x
        self.y = y
        self.value = value
        self.size = 8
        self.collection_radius = 150
        self.float_offset = random.uniform(0, math.pi * 2)
    
    def update(self, player, time):
        self.float_offset += 0.1
        
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < self.collection_radius:
            if dist > 0:
                speed = 10
                self.x += (dx / dist) * speed
                self.y += (dy / dist) * speed
        
        if dist < player.size + self.size:
            return True
        return False
    
    def draw(self, screen, camera, time):
        screen_pos = camera.apply(self)
        float_y = screen_pos[1] + math.sin(self.float_offset) * 5
        pygame.draw.circle(screen, (240, 230, 220), (int(screen_pos[0]), int(float_y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(screen_pos[0]), int(float_y)), self.size - 2)

# ============= Chest =============

class Chest:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 22
        self.opened = False

    def update(self, player):
        if self.opened:
            return False
        dx = player.x - self.x
        dy = player.y - self.y
        if math.sqrt(dx*dx + dy*dy) < player.size + self.size:
            self.opened = True
            return True
        return False

    def draw(self, screen, camera):
        pos = camera.apply(self)
        color = (180,120,40) if not self.opened else (80,60,30)
        pygame.draw.rect(screen, color, (pos[0]-15, pos[1]-12, 30, 24))
        pygame.draw.rect(screen, (60,40,20), (pos[0]-15, pos[1]-12, 30, 24), 2)
        pygame.draw.rect(screen, (240,220,120), (pos[0]-3, pos[1]-4, 6, 8))

# ============= Shrine =============

class Shrine:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 28
        self.used = False

    def update(self, player):
        if self.used:
            return False
        dx = player.x - self.x
        dy = player.y - self.y
        if math.sqrt(dx*dx + dy*dy) < player.size + self.size:
            self.used = True
            return True
        return False

    def draw(self, screen, camera):
        pos = camera.apply(self)
        base = (100,150,200) if not self.used else (60,80,100)
        pygame.draw.circle(screen, base, pos, self.size)
        pygame.draw.circle(screen, (200,220,255), pos, self.size-6)
        pygame.draw.circle(screen, (255,255,255), pos, 6)

def point_in_obstacle(x, y, obstacles):
    for obs in obstacles:
        if obs.rect.collidepoint(x, y):
            return True
    return False

# ============= GAME =============
class Game:
    def __init__(self):
        self.player = Player()
        self.camera = Camera()
        self.enemies = []
        self.projectiles = []
        self.xp_gems = []
        self.obstacles = []
        self.time = 0
        self.enemy_spawn_timer = 0
        self.enemy_spawn_rate = 120
        self.boss_spawn_timer = 0
        self.boss_spawn_interval = 3600  # Every 60 seconds
        self.game_over = False
        self.paused = False
        self.show_level_up = False
        self.level_up_options = []
        self.generated_chunks = set()
        self.difficulty_scale = 1.0
        self.bosses_defeated = 0
        self.chests = []
        self.shrines = []
        
        # Debug sliders
        self.show_debug = False
        self.speed_slider = Slider(WIDTH - 250, 150, 200, 0.1, 5.0, 1.0, "Player Speed")
        self.damage_slider = Slider(WIDTH - 250, 220, 200, 0.1, 10.0, 1.0, "Player Damage")
    
    def generate_obstacles_in_chunk(self, chunk_x, chunk_y):
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.generated_chunks:
            return
        
        self.generated_chunks.add(chunk_key)
        random.seed(hash(chunk_key))
        
        chunk_size = 500
        base_x = chunk_x * chunk_size
        base_y = chunk_y * chunk_size
        
        if abs(chunk_x) <= 1 and abs(chunk_y) <= 1:
            random.seed()
            return
        
        num_obstacles = random.randint(3, 8)
        
        for _ in range(num_obstacles):
            obstacle_type = random.choice(['coral', 'rock', 'seaweed'])
            
            if obstacle_type == 'seaweed':
                size_w = random.randint(40, 60)
                size_h = random.randint(60, 100)
            else:
                size_w = random.randint(50, 100)
                size_h = random.randint(50, 100)
            
            x = base_x + random.randint(0, chunk_size - size_w)
            y = base_y + random.randint(0, chunk_size - size_h)
            
            self.obstacles.append(Obstacle(x, y, size_w, size_h, obstacle_type))
        
        random.seed()

        #Create Chests & Shrines
        if random.random() < 0.25:
            for _ in range(10):
                x = base_x + random.randint(50, 450)
                y = base_y + random.randint(50, 450)
                if not point_in_obstacle(x, y, self.obstacles):
                    self.chests.append(Chest(x, y))
                    break

        if random.random() < 0.15:
            for _ in range(10):
                x = base_x + random.randint(50, 450)
                y = base_y + random.randint(50, 450)
                if not point_in_obstacle(x, y, self.obstacles):
                    self.shrines.append(Shrine(x, y))
                    break

    def update_obstacle_generation(self):
        chunk_size = 500
        player_chunk_x = int(self.player.x // chunk_size)
        player_chunk_y = int(self.player.y // chunk_size)
        
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                self.generate_obstacles_in_chunk(player_chunk_x + dx, player_chunk_y + dy)
        
        self.obstacles = [obs for obs in self.obstacles 
                         if abs(obs.x - self.player.x) < 2000 and abs(obs.y - self.player.y) < 2000]
    
    def spawn_enemy(self):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.randint(700, 900)
        
        x = self.player.x + math.cos(angle) * distance
        y = self.player.y + math.sin(angle) * distance
        
        # Calculate difficulty scale based on time (increases every 30 seconds)
        self.difficulty_scale = 1.0 + (self.time // 1800) * 0.3
        
        # Spawn different enemy types based on time
        enemy_types = ['shark', 'shark', 'piranha']

        if self.time > 600:
            enemy_types += ['jellyfish','piranha']
        if self.time > 1200:
            enemy_types += ['eel','hammerhead']
        if self.time > 2400:
            enemy_types += ['crab','octopus']

        if self.time > 600:  # After 10 seconds
            enemy_types.extend(['jellyfish', 'jellyfish'])
        if self.time > 1800:  # After 30 seconds
            enemy_types.extend(['eel', 'eel'])
        if self.time > 3600:  # After 1 minute
            enemy_types.append('octopus')
        
        enemy_type = random.choice(enemy_types)
        
        # 10% chance for elite enemy after 20 seconds
        is_elite = self.time > 1200 and random.random() < 0.1
        
        count = 1
        if self.time > 1200:
            count = 2
        if self.time > 2400:
            count = 3

        for i in range(count):
            spread = random.uniform(-50, 50)
            ex = x + math.cos(angle + i) * spread
            ey = y + math.sin(angle + i) * spread
            self.enemies.append(Enemy(ex, ey, enemy_type, is_elite=is_elite, difficulty_scale=self.difficulty_scale))
    
    def spawn_boss(self):
        # Spawn boss far from player
        angle = random.uniform(0, 2 * math.pi)
        distance = 1000
        
        x = self.player.x + math.cos(angle) * distance
        y = self.player.y + math.sin(angle) * distance
        
        # Alternate between boss types
        boss_types = ['megalodon', 'kraken']
        boss_type = boss_types[self.bosses_defeated % len(boss_types)]
        
        # Scale boss difficulty
        boss_scale = 1.0 + self.bosses_defeated * 0.5
        
        self.enemies.append(Enemy(x, y, boss_type, is_boss=True, difficulty_scale=boss_scale))
        
        # Show boss warning
        print(f"BOSS SPAWNED: {boss_type.upper()}!")
    
    def auto_attack(self):
        for weapon in self.player.weapons:
            cooldown_key = weapon.type
            
            if cooldown_key not in self.player.weapon_cooldowns:
                self.player.weapon_cooldowns[cooldown_key] = 0
            
            if self.enemies and self.player.weapon_cooldowns[cooldown_key] <= 0:
                # Find closest enemy
                closest = None
                min_dist = float('inf')
                
                for enemy in self.enemies:
                    dx = enemy.x - self.player.x
                    dy = enemy.y - self.player.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < min_dist:
                        min_dist = dist
                        closest = enemy
                
                if closest:
                    damage_mult = self.damage_slider.value
                    if weapon.type == 'net':
                        # Net fires 3 projectiles in a spread
                        for i in range(-1, 2):
                            angle_offset = i * 0.3
                            target_x = closest.x + 100 * math.cos(self.player.facing_angle + angle_offset)
                            target_y = closest.y + 100 * math.sin(self.player.facing_angle + angle_offset)
                            self.projectiles.append(Projectile(
                                self.player.x, self.player.y,
                                target_x, target_y, weapon, damage_mult
                            ))
                    else:
                        self.projectiles.append(Projectile(
                            self.player.x, self.player.y,
                            closest.x, closest.y, weapon, damage_mult
                        ))
                    
                    self.player.weapon_cooldowns[cooldown_key] = weapon.cooldown
    
    def generate_level_up_options(self):
        options = []
        
        # Weapon options
        available_weapons = ['harpoon', 'trident', 'net', 'torpedo']
        player_weapon_types = [w.type for w in self.player.weapons]
        
        # Offer new weapons or upgrades
        for weapon_type in available_weapons:
            if weapon_type in player_weapon_types:
                weapon = next(w for w in self.player.weapons if w.type == weapon_type)
                options.append({
                    'type': 'weapon_upgrade',
                    'weapon': weapon_type,
                    'name': f'Upgrade {weapon_type.title()} (Lv{weapon.level + 1})'
                })
            else:
                options.append({
                    'type': 'new_weapon',
                    'weapon': weapon_type,
                    'name': f'New Weapon: {weapon_type.title()}'
                })
        
        # Stat upgrades
        options.extend([
            {'type': 'speed', 'name': 'Swim Speed +0.5'},
            {'type': 'hp', 'name': 'Max HP +30'},
            {'type': 'regen', 'name': 'Heal 50 HP'}
        ])
        
        # Select 3 random options
        self.level_up_options = random.sample(options, 3)
    
    def handle_level_up_choice(self, choice_index):
        if choice_index < len(self.level_up_options):
            option = self.level_up_options[choice_index]
            
            if option['type'] == 'new_weapon':
                self.player.add_weapon(option['weapon'])
            elif option['type'] == 'weapon_upgrade':
                self.player.add_weapon(option['weapon'])
            elif option['type'] == 'speed':
                self.player.speed += 0.5
            elif option['type'] == 'hp':
                self.player.max_hp += 30
                self.player.hp = self.player.max_hp
            elif option['type'] == 'regen':
                self.player.hp = min(self.player.max_hp, self.player.hp + 50)
            
            self.show_level_up = False
            self.level_up_options = []
    
    def update(self):
        if self.game_over or self.paused or self.show_level_up:
            return
        
        self.time += 1
        
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.obstacles, self.speed_slider.value)
        
        self.camera.update(self.player)
        self.update_obstacle_generation()
        
        # Update weapon cooldowns
        for key in self.player.weapon_cooldowns:
            self.player.weapon_cooldowns[key] -= 1
        
        self.auto_attack()
        
        alive = []
        for p in self.projectiles:
            if not p.update():
                continue
            if abs(p.x - self.player.x) > 1500 or abs(p.y - self.player.y) > 1500:
                continue
            if p.collides_with_obstacle(self.obstacles):
                continue  # projectile dies on coral/rock
            alive.append(p)

        self.projectiles = alive

        
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_rate:
            self.spawn_enemy()
            self.enemy_spawn_timer = 0
            # Gradually increase spawn rate (cap at spawning every 0.5 seconds)
            if self.time % 600 == 0 and self.enemy_spawn_rate > 30:
                self.enemy_spawn_rate -= 5
        
        # Boss spawning
        self.boss_spawn_timer += 1
        if self.boss_spawn_timer >= self.boss_spawn_interval:
            self.spawn_boss()
            self.boss_spawn_timer = 0
        
        for enemy in self.enemies:
            enemy.update(self.player, self.obstacles, self.time)
        
        self.enemies = [e for e in self.enemies if abs(e.x - self.player.x) < 2000 and abs(e.y - self.player.y) < 2000]
        
        for proj in self.projectiles[:]:
            for enemy in self.enemies[:]:
                dx = proj.x - enemy.x
                dy = proj.y - enemy.y
                dist = math.sqrt(dx**2 + dy**2)
                
                hit_radius = enemy.size + proj.size
                if hasattr(proj.weapon, 'aoe_radius'):
                    hit_radius = proj.weapon.aoe_radius
                
                if dist < hit_radius:
                    enemy_id = id(enemy)
                    if proj.hit(enemy_id):
                        if enemy.take_damage(proj.damage):
                            # Drop more XP for elites and bosses
                            xp_drop = enemy.xp_value
                            if enemy.is_boss:
                                self.bosses_defeated += 1
                                # Bosses drop multiple XP gems
                                for _ in range(10):
                                    offset_x = random.randint(-50, 50)
                                    offset_y = random.randint(-50, 50)
                                    self.xp_gems.append(XPGem(enemy.x + offset_x, enemy.y + offset_y, xp_drop // 10))
                            else:
                                self.xp_gems.append(XPGem(enemy.x, enemy.y, xp_drop))
                            
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
        
        # Remove projectiles with no pierce left
        self.projectiles = [p for p in self.projectiles if p.pierce_count > 0]
        
        damage_taken = False
        for enemy in self.enemies:
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            if math.sqrt(dx**2 + dy**2) < self.player.size + enemy.size:
                if not damage_taken:
                    if self.player.take_damage(enemy.damage):
                        self.game_over = True
                    damage_taken = True
        
        for gem in self.xp_gems[:]:
            if gem.update(self.player, self.time):
                level_up = self.player.gain_xp(gem.value)
                self.xp_gems.remove(gem)
                if level_up:
                    self.show_level_up = True
                    self.generate_level_up_options()
        
        self.xp_gems = [g for g in self.xp_gems if abs(g.x - self.player.x) < 2000 and abs(g.y - self.player.y) < 2000]

        #Chests & Shrines
        for chest in self.chests[:]:
            if chest.update(self.player):
                # Big XP reward
                self.xp_gems.append(XPGem(chest.x, chest.y, 50))

                # Random weapon upgrade
                self.player.add_weapon(random.choice(['harpoon','trident','net','torpedo']))

                self.chests.remove(chest)

        for shrine in self.shrines[:]:
            if shrine.update(self.player):
                buff = random.choice(['damage','speed','cooldown','heal'])

                if buff == 'damage':
                    for w in self.player.weapons:
                        w.damage = int(w.damage * 1.3)

                elif buff == 'speed':
                    self.player.speed += 1

                elif buff == 'cooldown':
                    for w in self.player.weapons:
                        w.cooldown = max(8, int(w.cooldown * 0.75))

                elif buff == 'heal':
                    self.player.hp = self.player.max_hp

                self.shrines.remove(shrine)

    
    def draw(self):
        # Ocean gradient background
        for y in range(0, HEIGHT, 2):
            color_ratio = y / HEIGHT
            r = int(OCEAN_BLUE[0] + (DARK_BLUE[0] - OCEAN_BLUE[0]) * color_ratio)
            g = int(OCEAN_BLUE[1] + (DARK_BLUE[1] - OCEAN_BLUE[1]) * color_ratio)
            b = int(OCEAN_BLUE[2] + (DARK_BLUE[2] - OCEAN_BLUE[2]) * color_ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y), 2)
        
        # Bubbles
        for i in range(20):
            bubble_x = (self.camera.x * 0.1 + i * 100) % WIDTH
            bubble_y = (self.camera.y * 0.15 + i * 80 + self.time * 0.5) % HEIGHT
            pygame.draw.circle(screen, (50, 80, 140), (int(bubble_x), int(bubble_y)), 3)
        
        for obstacle in self.obstacles:
            if (obstacle.x + obstacle.width > self.camera.x and obstacle.x < self.camera.x + WIDTH and
                obstacle.y + obstacle.height > self.camera.y and obstacle.y < self.camera.y + HEIGHT):
                obstacle.draw(screen, self.camera)
        
        for gem in self.xp_gems:
            gem.draw(screen, self.camera, self.time)
        
        for enemy in self.enemies:
            enemy.draw(screen, self.camera, self.time)
        
        for proj in self.projectiles:
            proj.draw(screen, self.camera)

        for chest in self.chests:
            chest.draw(screen, self.camera)

        for shrine in self.shrines:
            shrine.draw(screen, self.camera)

        
        self.player.draw(screen, self.camera)
        
        # UI
        pygame.draw.rect(screen, RED, (10, 10, 200, 30))
        pygame.draw.rect(screen, GREEN, (10, 10, 200 * (self.player.hp / self.player.max_hp), 30))
        hp_text = small_font.render(f"HP: {int(self.player.hp)}/{self.player.max_hp}", True, WHITE)
        screen.blit(hp_text, (15, 15))
        
        pygame.draw.rect(screen, (50, 50, 50), (10, 50, 200, 20))
        pygame.draw.rect(screen, WHITE, (10, 50, 200 * (self.player.xp / self.player.xp_to_next), 20))
        xp_text = small_font.render(f"Level {self.player.level}", True, WHITE)
        screen.blit(xp_text, (15, 50))
        
        stats_text = small_font.render(f"Time: {self.time // FPS}s | Enemies: {len(self.enemies)} | Difficulty: {self.difficulty_scale:.1f}x", True, WHITE)
        screen.blit(stats_text, (10, 80))
        
        # Boss timer
        boss_time_left = (self.boss_spawn_interval - self.boss_spawn_timer) // FPS
        if boss_time_left < 10:
            boss_text = small_font.render(f"BOSS IN: {boss_time_left}s", True, RED if boss_time_left < 5 else YELLOW)
            screen.blit(boss_text, (WIDTH - 200, 10))
        
        # Weapon display
        weapon_y = 110
        for weapon in self.player.weapons:
            weapon_text = small_font.render(f"{weapon.type.title()} Lv{weapon.level}", True, WHITE)
            screen.blit(weapon_text, (10, weapon_y))
            weapon_y += 25
        
        # Debug panel
        if self.show_debug:
            panel_x = WIDTH - 280
            panel_y = 100
            panel_width = 270
            panel_height = 180
            
            # Semi-transparent background
            debug_surf = pygame.Surface((panel_width, panel_height))
            debug_surf.set_alpha(220)
            debug_surf.fill((20, 20, 40))
            screen.blit(debug_surf, (panel_x, panel_y))
            
            # Border
            pygame.draw.rect(screen, (100, 100, 150), (panel_x, panel_y, panel_width, panel_height), 2)
            
            # Title
            debug_title = small_font.render("DEBUG CONTROLS", True, YELLOW)
            screen.blit(debug_title, (panel_x + 10, panel_y + 10))
            
            # Sliders
            self.speed_slider.draw(screen)
            self.damage_slider.draw(screen)
            
            # Instructions
            toggle_text = tiny_font.render("Press T to toggle", True, (150, 150, 150))
            screen.blit(toggle_text, (panel_x + 10, panel_y + panel_height - 25))
        else:
            # Show hint to open debug
            hint_text = tiny_font.render("Press T for debug controls", True, (100, 100, 100))
            screen.blit(hint_text, (WIDTH - 200, HEIGHT - 30))
        
        if self.show_level_up:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(DARK_BLUE)
            screen.blit(overlay, (0, 0))
            
            title = font.render("LEVEL UP!", True, YELLOW)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
            
            for i, option in enumerate(self.level_up_options):
                choice_text = font.render(f"{i+1} - {option['name']}", True, WHITE)
                screen.blit(choice_text, (WIDTH//2 - choice_text.get_width()//2, 300 + i * 50))
        
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(DARK_BLUE)
            screen.blit(overlay, (0, 0))
            
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 50))
            
            stats = small_font.render(f"Survived: {self.time // FPS}s | Level: {self.player.level}", True, WHITE)
            screen.blit(stats, (WIDTH//2 - stats.get_width()//2, HEIGHT//2))
            
            restart = small_font.render("Press R to Restart", True, WHITE)
            screen.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//2 + 50))
        
        pygame.display.flip()

def main():
    game = Game()
    running = True
    
    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    game.show_debug = not game.show_debug
                elif game.show_level_up:
                    if event.key == pygame.K_1:
                        game.handle_level_up_choice(0)
                    elif event.key == pygame.K_2:
                        game.handle_level_up_choice(1)
                    elif event.key == pygame.K_3:
                        game.handle_level_up_choice(2)
                elif game.game_over and event.key == pygame.K_r:
                    game = Game()
            
            # Handle slider events when debug is open
            if game.show_debug and not game.game_over and not game.show_level_up:
                game.speed_slider.handle_event(event)
                game.damage_slider.handle_event(event)
        
        game.update()
        game.draw()
    
    pygame.quit()

if __name__ == "__main__":
    main()
