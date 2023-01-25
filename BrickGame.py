
'''
TODO:
    Scale to window size
    #Animate paddle selection circle
    #Implement pre-launch state (added just a delay instead)
    #Upgrade pre-launch state (timer)
    #Implement multiple lives
    Finish implementing powerups
        #Move side effects to PlayState
        #Options
            #Paddle gun
            #Extra life
            Splash damage
        #X-axis movement
        #Add points for collection
        Clean up gun positioning code
    #Fix paddle bounce angle (very broken)
    #Implement block map generation
    Fix paddle select bug (press too quickly)
    Paddle HP/color
        Utilize paddle self.hp
        Set color based on inverse of paddle color + offset for HP value
    Add more block colors?  Change block colors to opposite palette of paddle?
    #Fix Title animation color cycling
    #Center-align score text
    #Reverse paddle select rotate direction
    
    #Add countdown timer
    Implement high score names + saving
    Add text
    Add sounds
    Add background
    Improve graphics
        Life counter hearts
'''

import sys
import math
import random
import pygame
import time
import os
os.system('cls' if os.name == 'nt' else 'clear')
print('')

pygame.init()

WINX = 640
WINY = 480
win_radius = math.sqrt(WINX**2 + WINY**2)/2
WIN_BORDER = 4

win = pygame.display.set_mode((WINX, WINY), 0, 32)
pygame.display.set_caption('TEST')
FPSCLOCK = pygame.time.Clock()

basic_font_12 = pygame.font.SysFont('arial', 12)
basic_font_18 = pygame.font.SysFont('arial', 18)
title_font = pygame.font.SysFont('bradleyhanditc', 72)

BLACK = (0, 0, 0)
VDGREY = (20, 20, 20)
DGREY = (80, 80, 80)
MGREY = (140, 140, 140)
LGREY = (200, 200, 200)
VLGREY = (240, 240, 240)
WHITE = (255, 255, 255)
RED = (204, 0, 0)
ORANGE = (255, 128, 0)
GREEN = (0, 204, 0)
BLUE = (0, 0, 255)
BLUEGREY = (0, 102, 204)
PURPLE = (102, 0, 204)
MAGENTA = (204, 0, 204)



class Paddle(object):
    
    STARTING_WIDTH = 50
    PADDLE_COLORS = [RED,
                     ORANGE,
                     GREEN,
                     BLUEGREY,
                     PURPLE,
                     MAGENTA]
              
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 1
        self.accel = 1.3
        self.width = Paddle.STARTING_WIDTH
        self.thickness = self.width/5
        self.color = 0
        self.ellipse_x = 120
        self.ellipse_y = 20
        self.ammo = 0
        self.gun_inset = 2
        self.gun_width = 4
        
    def render(self):
        pygame.draw.rect(win, self.PADDLE_COLORS[self.color], [self.x, self.y, self.width, self.thickness])
    
    def render_guns(self):
        if self.ammo > 0:            
            gun_height = 8
            pygame.draw.rect(win, MGREY, [self.x + self.gun_inset, self.y + (self.thickness - gun_height), self.gun_width, gun_height])
            pygame.draw.rect(win, DGREY, [self.x + self.gun_inset + (self.gun_width/2 - 1), self.y, self.gun_width/2, gun_height + 2])
            pygame.draw.rect(win, MGREY, [self.x + self.width - self.gun_inset - self.gun_width, self.y + (self.thickness - gun_height), self.gun_width, gun_height])
            pygame.draw.rect(win, DGREY, [self.x + self.width - self.gun_inset - self.gun_width + (self.gun_width/2 - 1), self.y, self.gun_width/2, gun_height + 2])
    
    def move(self, direction, last_direction):
        if direction != last_direction:
            self.speed = 1
        self.speed = min(self.speed * self.accel, 6)
        if direction == "left":
            self.x = max(WIN_BORDER, self.x - self.speed)
        elif direction == "right":
            self.x = min(WINX - WIN_BORDER - self.width, self.x + self.speed)
    
    def shoot(self):
        if self.ammo > 0:
            self.ammo -= 1
            return self.x + self.gun_inset + (self.gun_width/2 - 1), self.x + self.width - self.gun_inset - self.gun_width + (self.gun_width/2 - 1)
        else:
            return None
    
    def update_circle(self, selected_x, selected_y, qty, index, offset, max_offset):
        circle_interval = 2 * math.pi/qty
        self.width = Paddle.STARTING_WIDTH/2 * (1.5 + math.sin(((index + offset/max_offset) * circle_interval) + math.pi/2)/2)
        self.thickness = self.width/5
        self.x = selected_x + self.ellipse_x * math.sin((index + offset/max_offset) * circle_interval) + (Paddle.STARTING_WIDTH - self.width)/2
        self.y = selected_y + self.ellipse_y - self.ellipse_y * math.cos((index + offset/max_offset) * circle_interval)
    
    def size_change(self, change):
        if 20 < self.width + change < 100:
            self.width += change
            self.x -= change/2

            
class Bullet(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3
        self.length = 6
    
    def render(self):
        pygame.draw.line(win, BLACK, (int(self.x), int(self.y)), (int(self.x), int(self.y - self.length)), 2)
    
    def move(self):
        self.y = self.y - self.speed
    
    def check_block_collide(self, block):
        if block.x < self.x < block.x + block.width + 1:
            if self.y < block.y + block.thickness:
                return True
        return False


class Ball(object):
              
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.angle = math.pi*7/4
        self.last_angle = self.angle
        self.dx = self.speed*math.cos(self.angle)
        self.dy = self.speed*math.sin(self.angle)
        self.radius = 4
        self.color = BLACK
        self.noclipping = False
        self.splashdmg = False
        
    def render(self):
        # Draw ball
        pygame.draw.circle(win, self.color, [int(self.x), int(self.y)], self.radius)
        # Draw "noclipping" trail
        if self.noclipping == True:
            pygame.draw.line(win, self.color, (int(self.x), int(self.y)), (int(self.x-8), int(self.y-8)), 2)
        # Draw "splashdmg" halo
        if self.splashdmg == True:
            pygame.draw.circle(win, MGREY, [int(self.x), int(self.y)], self.radius + 3, 1)
    
    def update_angle(self, radians):
        self.last_angle = self.angle
        while radians > math.pi:
            radians -= 2 * math.pi
        while radians < -math.pi:
            radians += 2 * math.pi
        self.angle = radians
        self.dx = self.speed*math.cos(radians)
        self.dy = self.speed*math.sin(radians)
    
    def bounce_x(self):
        self.update_angle(math.pi - self.angle)
    
    def bounce_y(self):
        self.update_angle(-self.angle)
    
    def move(self):
        # Update position
        self.x = self.x + self.dx
        self.y = self.y + self.dy
        # Check for collision with window border
        if self.x + self.radius > WINX - WIN_BORDER:
            self.x = WINX - WIN_BORDER - self.radius - 1
            self.bounce_x()
        elif self.x - self.radius < WIN_BORDER:
            self.x = WIN_BORDER + self.radius + 1
            self.bounce_x()
        if self.y - self.radius < WIN_BORDER:
            self.y = WIN_BORDER + self.radius + 1
            self.bounce_y()
    
    def check_loss(self):
        if self.y + self.radius > WINY:
            return True
        else:
            return False
    
    def check_paddle_collide(self, paddle):
        if paddle.y - self.radius < self.y < paddle.y + paddle.thickness - self.radius:
            if paddle.x - self.radius < self.x < paddle.x + paddle.width - self.radius:
                self.y = paddle.y - self.radius - 1
                MIN_BOUNCE_ANGLE = 0.4
                paddle_hit_location = 2 * (self.x - (paddle.x + paddle.width/2))/(paddle.width)
                self.update_angle(-3.14/2 + (3.14/2 - MIN_BOUNCE_ANGLE) * paddle_hit_location)
                # Reset NoClip item powerup
                self.noclipping = False
    
    def check_block_collide(self, block):
        if block.x - self.radius < self.x < block.x + block.width + self.radius:
            if block.y - self.radius < self.y < block.y + block.thickness + self.radius:
                if self.noclipping == False:
                    # if left edge outside & dx positive, trigger left side
                    if block.y - self.y < block.x - self.x and self.y - (block.y + block.thickness) < block.x - self.x and self.dx > 0:
                        self.x = block.x - self.radius - 1
                        self.bounce_x()
                    # elif right edge outside and dx negative, trigger right side
                    elif block.y - self.y < self.x - (block.x + block.width) and self.y - (block.y + block.thickness) < self.x - (block.x + block.width) and self.dx < 0:
                        self.x = block.x + block.width + self.radius + 1
                        self.bounce_x()
                    # elif top is outside, trigger top side
                    elif block.y - self.y > block.x - self.x and block.y - self.y > self.x - (block.x + block.width) and self.dy > 0:
                        self.y = block.y - self.radius - 1
                        self.bounce_y()
                    # else, trigger bottom side
                    elif self.y - (block.y + block.thickness) > block.x - self.x and self.y - (block.y + block.thickness) > self.x - (block.x + block.width) and self.dy < 0:
                        self.y = block.y + block.thickness + self.radius + 1
                        self.bounce_y()
                return True
        return False


class Splash(object):

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 1
        self.dx = self.speed*math.cos(self.angle)
        self.dy = self.speed*math.sin(self.angle)
        self.radius = 3
        self.remaining = 30
    
    def render(self):
        pygame.draw.circle(win, Block.MODIFIERS["splashdmg"], [int(self.x), int(self.y)], self.radius)
    
    def move(self):
        self.remaining -= 1
        if self.remaining < 0:
            return False
        self.x = self.x + self.dx
        self.y = self.y + self.dy
        return True
    
    def check_block_collide(self, block):
        if block.x < self.x < block.x + block.width + 1:
            if self.y < block.y + block.thickness:
                return True
        return False


class Block(object):

    MAX_HP = 3
    
    block_color = GREEN

    BLOCK_COLORS = [LGREY,
                    MGREY,
                    DGREY]
    
    MODIFIERS = {"paddleup": GREEN,
                 "paddledown": RED,
                 "multiball": BLUE,
                 "noclipping": PURPLE,
                 "extralife": ORANGE,
                 "bullets": MAGENTA,
                 "splashdmg": BLUEGREY}
    BORDER = 2
              
    def __init__(self, x, y, hp, color_index):
        self.x = x
        self.y = y
        self.width = 40
        self.thickness = 10
        self.hp = max(hp, 0)
        self.color = [max((value - 80*self.hp),0) for value in self.block_color]
        #self.color_index = color_index + len(Paddle.PADDLE_COLORS)/2 + self.hp
        #while self.color_index > len(Paddle.PADDLE_COLORS)-1:
        #    self.color_index -= len(Paddle.PADDLE_COLORS)
        #self.color = Paddle.PADDLE_COLORS[self.color_index]
        self.points = 10
        empty_block = random.randint(0,6)
        self.item = random.choice(list(self.MODIFIERS.items())) if not empty_block else None
        self.item = ("splashdmg", BLUEGREY)
        #self.item = None
        #print(self.item)
        
    def render(self):
        pygame.draw.rect(win, BLACK, [self.x, self.y, self.width, self.thickness])
        #pygame.draw.rect(win, self.BLOCK_COLORS[self.hp], [self.x + self.BORDER, self.y + self.BORDER, self.width - (self.BORDER * 2), self.thickness - (self.BORDER * 2)])
        pygame.draw.rect(win, self.color, [self.x + self.BORDER, self.y + self.BORDER, self.width - (self.BORDER * 2), self.thickness - (self.BORDER * 2)])
    
    def destroy(self):
        if self.hp > 0:
            self.hp -= 1
            self.color = [max((value - 80*self.hp),0) for value in self.block_color]
            #self.color_index -= 1
            #while self.color_index < 0:
            #    self.color_index += len(Paddle.PADDLE_COLORS)
            #self.color = Paddle.PADDLE_COLORS[self.color_index]
            return None, None, None
        else:
            return self.x+(self.width/2), self.y+self.thickness, self.item

            
class ItemDrop(object):

    def __init__(self, x, y, item):
        self.x = x
        self.y = y
        self.dx = random.random()/4
        self.dy = 1
        self.radius = 7
        self.modifier = item[0]
        self.color = item[1]
        
    def render(self):
        pygame.draw.circle(win, self.color, (int(self.x), int(self.y)), self.radius)
        if self.modifier == "paddledown":
            pygame.draw.line(win, BLACK, (int(self.x-self.radius), int(self.y-self.radius)), (int(self.x+self.radius), int(self.y+self.radius)), 1)
            pygame.draw.line(win, BLACK, (int(self.x-self.radius), int(self.y+self.radius)), (int(self.x+self.radius), int(self.y-self.radius)), 1)
    
    def move(self):
        self.x = self.x + self.dx
        self.y = self.y + self.dy
    
    def check_paddle_collide(self, paddle):
        if paddle.y - self.radius < self.y < paddle.y + paddle.thickness - self.radius:
            if paddle.x - self.radius < self.x < paddle.x + paddle.width - self.radius:    
                return self.modifier
        return None


def map_range():
    pass

def generate_map(paddle_color):
    rows = 4
    columns = 5
    block_list = []
    make_fade = random.choice(["None", "Side", "Center"])   # This is outside the loop so that it will only apply the fade to all rows or none
    print(make_fade)
    for row in range(rows):
        make_holes = random.choice(["None", "Odd", "Even"])
        make_alternate = random.randint(0,1)
        block_row = []
        for col in range(columns):
            hp = 0
            if make_alternate == 1 and col % 2 == 1:
                hp += 1
            if make_fade == "Side":
                #hp = col/math.trunc((columns + 1)/len(Block.BLOCK_COLORS))
                #hp = col/math.trunc((columns + 1)/len(Paddle.PADDLE_COLORS))
                hp = math.trunc(col*min(3,columns)/columns)
                #hp = math.trunc(col*min(len(Paddle.PADDLE_COLORS),columns)/columns) - math.trunc(columns/2)
            elif make_fade == "Center":
                #hp = ((columns + 1)/2 - 1) - abs((columns - 1)/2 - col)
                if col < columns/2:
                    hp = math.trunc(col*min(3,columns/2)/columns)
                    #hp = math.trunc(col*min(len(Paddle.PADDLE_COLORS),columns/2)/columns) - math.trunc(columns/4)
                else:
                    hp = columns - math.trunc(col*min(3,columns)/columns) - 1
                    #hp = columns - math.trunc(col*min(len(Paddle.PADDLE_COLORS),columns)/columns) - 1 - math.trunc(columns/4)
            if make_holes == "Odd" and col % 2 == 1:
                continue
            elif make_holes == "Even" and col % 2 == 0:
                continue
            block_row.append(Block(50+(col*45), 20+(row*15), hp, paddle_color))
        block_list.append(block_row)
    return block_list

    
def draw_heart(x, y, width):
    pygame.draw.polygon(win, RED, ((WINX - x, y),
                                   (WINX - x - width/2, y - width/2),
                                   (WINX - x, y - width),
                                   (WINX - x + width/2, y - width/2)))
    pygame.draw.circle(win, RED, (int(WINX - x - width/4), int(y - 3*width/4)+1), int(math.sqrt((width/2)**2 + (width/2)**2)/2)+1)
    pygame.draw.circle(win, RED, (int(WINX - x + width/4)+1, int(y - 3*width/4)+1), int(math.sqrt((width/2)**2 + (width/2)**2)/2)+1)


class State(object):
    def __init__(self):        
        #print("Current state: " + str(self))
        pass
    
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__
    
    def calculate(self):
        pass
    def render(self):
        pass
    def end(self):
        pass

        
class TitleState(State):
    def __init__(self, high_scores):
        self.high_scores = high_scores
        
        self.selected_x = WINX/2 - 20
        self.selected_y = WINY - 60
        self.offset = 0
        self.max_offset = 30.
        self.paddle_list = [Paddle(self.selected_x, self.selected_y),]
        self.color_choices = self.paddle_list[0].PADDLE_COLORS
        self.interval = len(self.color_choices)
        for index,color in enumerate(self.color_choices[1:], start=1):
            self.paddle_list.append(Paddle(0,0))
        for index,paddle in enumerate(self.paddle_list):
            paddle.color = index
            paddle.update_circle(self.selected_x, self.selected_y, self.interval, index, 0, self.max_offset)
        
        self.paddle_selection = 0
        self.last_keys = time.time()
        self.last_left_state = False
        self.last_right_state = False
        self.left_arrow_enlarge = 0
        self.right_arrow_enlarge = 0
        
        self.bg_timer = 0
        self.bg_colors = [MGREY, LGREY, VLGREY]
        self.bg_divs = 4
        
    def calculate(self, keys):
        # Timer for background animation
        self.bg_timer += 1
        if self.bg_timer >= win_radius/self.bg_divs:
            self.bg_timer = 0
            self.bg_colors.append(self.bg_colors[0])
            self.bg_colors.pop(0)
        
        # Paddle set
        for index,paddle in enumerate(self.paddle_list):
            paddle.update_circle(self.selected_x, self.selected_y, self.interval, index, self.offset, self.max_offset)
        if self.offset >= self.max_offset or self.offset <= -self.max_offset:
            self.offset = 0
            if self.last_left_state == True:
                self.last_left_state = False
                self.paddle_list.insert(0, self.paddle_list.pop(len(self.paddle_list)-1))
            if self.last_right_state == True:
                self.last_right_state = False
                self.paddle_list.append(self.paddle_list.pop(0))
        
        # Key actions & timers
        if time.time() < self.last_keys + 0.5:
            if self.last_left_state == True:
                self.offset += 1
            elif self.last_right_state == True:
                self.offset -= 1
        if time.time() > self.last_keys + 0.1:
            self.last_keys = time.time()
            if keys[pygame.K_LEFT]:
                self.left_arrow_enlarge = 4
                if self.last_left_state == False:
                    self.last_left_state = True
            else:
                self.left_arrow_enlarge = 0
            if keys[pygame.K_RIGHT]:
                self.right_arrow_enlarge = 4
                if self.last_right_state == False:
                    self.last_right_state = True
            else:
                self.right_arrow_enlarge = 0
                
    def render(self):
        # Background
        win.fill(self.bg_colors[-2])
        for index in range(self.bg_divs):
            rad = int(win_radius / self.bg_divs * ((self.bg_divs - index - 1) % self.bg_divs) + self.bg_timer)
            color = ((index - 1) % len(self.bg_colors))
            pygame.draw.circle(win, self.bg_colors[color], [WINX/2, WINY/2], rad)
            
        # Paddles
        for paddle in self.paddle_list:
            paddle.render()
            
        # Arrows
        pygame.draw.polygon(win, BLACK, ((self.selected_x - 10, self.selected_y - self.left_arrow_enlarge),
                                         (self.selected_x - 10, self.selected_y + 8 + self.left_arrow_enlarge),
                                         (self.selected_x - 14 - self.left_arrow_enlarge, self.selected_y + 4)))
        pygame.draw.polygon(win, BLACK, ((self.selected_x + Paddle.STARTING_WIDTH + 10, self.selected_y - self.right_arrow_enlarge),
                                         (self.selected_x + Paddle.STARTING_WIDTH + 10, self.selected_y + 8 + self.right_arrow_enlarge),
                                         (self.selected_x + Paddle.STARTING_WIDTH + 14 + self.right_arrow_enlarge, self.selected_y + 4)))
        
        # Title
        title_surface = title_font.render("Title", True, BLACK)
        title_rect = title_surface.get_rect()
        title_rect = title_surface.get_rect(center=(WINX/2, WINY/2 - 40))
        win.blit(title_surface, title_rect)
        
    def end(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return(PlayState(self.paddle_list[self.paddle_selection], self.high_scores))
        return(self)

        
class PlayState(State):
    def __init__(self, paddle, high_scores):
        self.ball_list = [Ball(WINX/2, WINY-40)]
        self.block_list = generate_map(paddle.color)
        self.item_list = []
        self.bullet_list = []
        self.splash_list = []
        
        self.paddle = paddle
        self.paddle.width = Paddle.STARTING_WIDTH
        self.paddle.thickness = self.paddle.width/4
        self.paddle.x = WINX/2 - 20
        self.paddle.y = WINY - 20
        
        self.last_direction = ""
        start_time = time.time()
        self.last_bullet = start_time
        
        self.high_scores = high_scores
        self.score = 0
        self.lives = 3
        
        self.countdown_duration = 1.5
        self.round_active = False
        self.last_round_start = start_time
        
        # Select opposite color
        #color_options = len(Paddle.PADDLE_COLORS)
        #color_choice = self.paddle.color + color_options/2
        #if color_choice >= color_options:
        #    color_choice -= color_options
        #self.bg_color = Paddle.PADDLE_COLORS[color_choice]
        
        # Select same color
        self.bg_color = Paddle.PADDLE_COLORS[self.paddle.color]
        
    def calculate(self, keys):
        # Balls
        for ball in self.ball_list:
            if self.round_active == True:
                ball.move()
            ball.check_paddle_collide(self.paddle)
            for index,row in enumerate(self.block_list):
                for block in row:
                    if ball.check_block_collide(block) == True:
                        if ball.splashdmg == True:
                            ball.splashdmg = False
                            self.splash_list.append(Splash(ball.x, ball.y, ball.last_angle))
                            #print(self.splash_list)
                        item_x, item_y, item_type = block.destroy()
                        if item_x != None:
                            self.score += block.points
                            self.block_list[index].remove(block)
                            if item_type != None:
                                self.item_list.append(ItemDrop(item_x, item_y, item_type))
                        else:
                            self.score += block.points/2
        
        # Items
        for item in self.item_list:
            item.move()
            check_item_collect = item.check_paddle_collide(self.paddle)
            if check_item_collect != None:
                if check_item_collect == "paddleup":
                    self.score += 20
                    self.paddle.size_change(10)
                elif check_item_collect == "paddledown":
                    self.score -= 20
                    if self.paddle.width >= 30:
                        self.paddle.size_change(-10)
                elif check_item_collect == "multiball":
                    self.score += 20
                    self.ball_list.append(Ball(WINX/2, WINY-40))
                elif check_item_collect == "noclipping":
                    self.score += 20
                    for ball in self.ball_list:
                        ball.noclipping = True
                elif check_item_collect == "extralife":
                    self.score += 20
                    if self.lives < 8:
                        self.lives += 1
                elif check_item_collect == "bullets":
                    self.score += 20
                    self.paddle.ammo += 2
                elif check_item_collect == "splashdmg":
                    self.score += 20
                    for ball in self.ball_list:
                        ball.splashdmg = True
                self.item_list.remove(item)
        
        # Bullets
        for bullet in self.bullet_list:
            bullet.move()
            for index,row in enumerate(self.block_list):
                for block in row:
                    if bullet.check_block_collide(block) == True:
                        self.bullet_list.remove(bullet)
                        item_x, item_y, item_type = block.destroy()
                        if item_x != None:
                            self.score += block.points
                            self.block_list[index].remove(block)
                            if item_type != None:
                                self.item_list.append(ItemDrop(item_x, item_y, item_type))
                        else:
                            self.score += block.points/2
        # Splashes
        for particle in self.splash_list:
            if particle.move() == True:
                for index,row in enumerate(self.block_list):
                    for block in row:
                        if particle.check_block_collide(block) == True:
                            item_x, item_y, item_type = block.destroy()
                            if item_x != None:
                                self.splash_list.remove(particle)
                                self.score += block.points
                                self.block_list[index].remove(block)
                                if item_type != None:
                                    self.item_list.append(ItemDrop(item_x, item_y, item_type))
                            else:
                                self.score += block.points/2
                            
            else:
                #print(particle)
                self.splash_list.remove(particle)
        
        # Key actions & timers
        if keys[pygame.K_LEFT]:
            if self.round_active == False and time.time() > self.last_round_start + self.countdown_duration:
                self.round_active = True
            self.paddle.move("left", self.last_direction)
            self.last_direction = "left"
        elif keys[pygame.K_RIGHT]:
            if self.round_active == False and time.time() > self.last_round_start + self.countdown_duration:
                self.round_active = True
            self.paddle.move("right", self.last_direction)
            self.last_direction = "right"
        elif keys[pygame.K_SPACE]:
            if self.round_active == True and self.paddle.ammo > 0 and time.time() > self.last_bullet + 0.2:
                self.last_bullet = time.time()
                bullet_x1, bullet_x2 = self.paddle.shoot()
                if bullet_x1 != None:
                    self.bullet_list.append(Bullet(bullet_x1, self.paddle.y))
                    self.bullet_list.append(Bullet(bullet_x2, self.paddle.y))
            
    def render(self):
        # Background & border
        win.fill(self.bg_color)
        pygame.draw.rect(win, WHITE, [WIN_BORDER, WIN_BORDER, WINX - (WIN_BORDER * 2), WINY - (WIN_BORDER * 2)])
        
        # Game objects
        for bullet in self.bullet_list:
            bullet.render()
        for item in self.item_list:
            item.render()
        for row in self.block_list:
            for block in row:
                block.render()
        for particle in self.splash_list:
            particle.render()
        for ball in self.ball_list:
            ball.render()
        self.paddle.render()
        self.paddle.render_guns()
        
        # Bullets
        bullet_height = 7
        bullet_width = 2
        for bullet in range(self.paddle.ammo):
            pygame.draw.rect(win, BLACK, [10 + bullet * 6, 5, bullet_width, bullet_height])
        
        # Score
        score_surface = basic_font_12.render("Score: " + str(self.score), False, BLACK)
        score_rect = score_surface.get_rect()
        score_rect.center = (WINX/2, 10)
        win.blit(score_surface, score_rect)
        
        # Lives
        heart_x = 20
        heart_y = 24
        heart_width = 16
        for life in range(self.lives):
            draw_heart(heart_x + life * (heart_width + heart_width/2), heart_y, heart_width)
        
        # Starting countdown
        current_time = time.time()
        if self.round_active == False:
            countdown_text = "3"
            if current_time < self.last_round_start + self.countdown_duration*1/3:
                countdown_text = "3"
            elif current_time < self.last_round_start + self.countdown_duration*2/3:
                countdown_text = "2"
            elif current_time < self.last_round_start + self.countdown_duration:
                countdown_text = "1"
            else:
                countdown_text = "Ready!"
            countdown_surface = basic_font_18.render(countdown_text, False, BLACK)
            countdown_rect = countdown_surface.get_rect()
            countdown_rect.center = (WINX/2, WINY/2)
            win.blit(countdown_surface, countdown_rect)
        
    def end(self, events):
        blocks_exist = [row for row in self.block_list if len(row) > 0]
        
        # Level complete
        if not blocks_exist:
            return(EndState(self.score, self.high_scores))
        
        # Ball loss
        for index,ball in enumerate(self.ball_list):
            if ball.check_loss():
                if len(self.ball_list) > 1:
                    self.ball_list.remove(ball)
                else:
                    self.lives -= 1
                    self.ball_list[0].x = WINX/2
                    self.ball_list[0].y = WINY-40
                    self.ball_list[0].angle = math.pi*7/4
                    self.ball_list[0].dx = self.ball_list[0].speed*math.cos(self.ball_list[0].angle)
                    self.ball_list[0].dy = self.ball_list[0].speed*math.sin(self.ball_list[0].angle)
                    self.round_active = False
                    self.last_round_start = time.time()
        
        # Game over
        if self.lives < 1:
            return(EndState(self.score, self.high_scores))
        else:
            return(self)

            
class EndState(State):
    def __init__(self, score, high_scores):
        self.score = int(score)
        self.high_scores = high_scores
        self.recorded = False
        
    def calculate(self, keys):
        if self.recorded == False:
            for index,high_score in enumerate(self.high_scores):
                if self.score > high_score:
                    self.high_scores.insert(index, self.score)
                    self.high_scores.pop()
                    self.recorded = True
                    break
                    
    def render(self):
        win.fill(WHITE)
        
        # Current score
        x_pos = WINX/2
        score_surface = basic_font_18.render(str(self.score), False, BLACK)
        score_rect = score_surface.get_rect()
        score_rect.topright = (x_pos, 20)
        win.blit(score_surface, score_rect)
        
        # High score table
        for index,high_score in enumerate(self.high_scores):
            high_score_surface = basic_font_18.render(str(high_score), False, BLUE)
            high_score_rect = high_score_surface.get_rect()
            high_score_rect.topright = (x_pos, 80+(index*24))
            win.blit(high_score_surface, high_score_rect)
            
    def end(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return(TitleState(self.high_scores))
        return(self)
        
        
class Game(object):
    def __init__(self):
        self.high_scores = [0,0,0,0,0]
        self.state = TitleState(self.high_scores)

    def next_state(self, state):
        self.state = state




def main():
    game = Game()
    while True:
    
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

        
        game.state.calculate(pygame.key.get_pressed())
        game.state.render()
        game.next_state(game.state.end(events))
        
        pygame.display.update()
        
        FPSCLOCK.tick(60)


main()