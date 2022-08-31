"""Implements the game loop and handles the user's events."""

import os
import random
import pygame as pg

from itertools import cycle
from agent import Agent
from obstacle import Obstacle
from helper import message, distance
import constants as const
vec = pg.math.Vector2
n_snap = 0

# Manually places the window
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (50, 50)

MAX_FRAME = 500
REWARD_WANDER = -1
REWARD_CLOSE_WALL = 5
REWARD_CLOSE_FOOD = 1
REWARD_EAT = 10
REWARD_COLLISION = -10


class GameAI:
    def __init__(self, human=False, grid=False) -> None:
        pg.init()
        self.human = human
        self.grid = grid
        self.screen = pg.display.set_mode([const.WIDTH, const.HEIGHT])
        pg.display.set_caption(const.TITLE)
        self.clock = pg.time.Clock()
        
        self.running = True
        self.n_frames = 0
        self.n_frames_threshold = 0
        self.score = 0
        
        self.enemies = [
            # Block(3*const.BLOCK_SIZE, 3*const.BLOCK_SIZE, const.BLOCK_SIZE*2),
            # Block(10*const.BLOCK_SIZE, 3*const.BLOCK_SIZE, const.BLOCK_SIZE*2),
            # Block(3*const.BLOCK_SIZE, 10*const.BLOCK_SIZE, const.BLOCK_SIZE*2),
            # Block(10*const.BLOCK_SIZE, 10*const.BLOCK_SIZE, const.BLOCK_SIZE*2),
            # Block(6*const.BLOCK_SIZE, 6*const.BLOCK_SIZE, const.BLOCK_SIZE*3),
            # Block(6*const.BLOCK_SIZE, 6*const.BLOCK_SIZE, const.BLOCK_SIZE*3),
            # Block(8*const.BLOCK_SIZE, 2*const.BLOCK_SIZE, const.BLOCK_SIZE),
            Block(8*const.BLOCK_SIZE, 3*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            Block(8*const.BLOCK_SIZE, 4*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            Block(8*const.BLOCK_SIZE, 5*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            Block(8*const.BLOCK_SIZE, 6*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            Block(8*const.BLOCK_SIZE, 7*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            Block(8*const.BLOCK_SIZE, 8*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            Block(8*const.BLOCK_SIZE, 9*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            Block(8*const.BLOCK_SIZE, 10*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            Block(8*const.BLOCK_SIZE, 11*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Red")),
            # Block(8*const.BLOCK_SIZE, 12*const.BLOCK_SIZE, const.BLOCK_SIZE),
        ]
        
        self.neighbours = [
            Block2(9*const.BLOCK_SIZE, 3*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
            Block2(9*const.BLOCK_SIZE, 4*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
            Block2(9*const.BLOCK_SIZE, 5*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
            Block2(9*const.BLOCK_SIZE, 6*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
            Block2(9*const.BLOCK_SIZE, 7*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
            Block2(9*const.BLOCK_SIZE, 8*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
            Block2(9*const.BLOCK_SIZE, 9*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
            Block2(9*const.BLOCK_SIZE, 10*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
            Block2(9*const.BLOCK_SIZE, 11*const.BLOCK_SIZE, const.BLOCK_SIZE, pg.Color("Purple")),
        ]
        self.agent = Agent(self)
        self.food = Food(self)
        self.distance_food = distance(self.agent.pos, self.food.pos)

    def reset(self):
        self.n_frames_threshold = 0
        self.score = 0
        self.agent.place()
        self.food.place()
        for neighbour in self.neighbours:
            neighbour.tagged = False
        
    def reset2(self):
        self.n_frames_threshold = 0 
        self.agent.place()
        self.food.place()
        for neighbour in self.neighbours:
            neighbour.tagged = False
        
    def play_step(self, state, action):
        self.n_frames_threshold += 1
        
        self.events()
        self.agent.update(action)
            
        # returning corresponding values
        reward, game_over = self.get_reward(state)
        return reward, game_over, self.score

    def get_reward(self, state) -> tuple:
        game_over = False
        reward = 0

        # stops episode if the agent does nothing but wonder around
        if self.n_frames_threshold > MAX_FRAME:
            return REWARD_WANDER, True
        
        # checking for failure (wall or enemy collision)
        if self.agent.wall_collision(offset=0) or self.agent.enemy_collision():
            return REWARD_COLLISION, True
            
        # checking if agent is getting closer to food
        self.old_distance_food = self.distance_food
        self.distance_food = distance(self.agent.pos, self.food.pos)
        if self.distance_food < self.old_distance_food:
            reward = REWARD_CLOSE_FOOD
        else:
            reward = -REWARD_CLOSE_FOOD

        # tag???
        collisions_sprites = pg.sprite.spritecollide(self.agent, self.neighbours, False)
        if collisions_sprites:
            if not collisions_sprites[0].tagged:
                collisions_sprites[0].tagged = True
                reward = 2
            else:
                reward = -2
            
        # checking if eat:
        if self.agent.food_collision():
            reward = REWARD_EAT
            self.score += 1
            self.agent.reset_ok = True

        return reward, game_over

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN and event.key == pg.K_q:
                self.running = False

    def display(self, mean_scores):
        self.screen.fill(const.BACKGROUND_COLOR)
        
        # Drawing blocks
        for enemy, neighbour in zip(self.enemies, self.neighbours):
            pg.draw.rect(self.screen, enemy.color, enemy.rect)
            neighbour.color = pg.Color("Yellow") if neighbour.tagged else pg.Color("Purple")
            pg.draw.rect(self.screen, neighbour.color, neighbour.rect)
            
        pg.draw.rect(self.screen, self.agent.color, self.agent.rect)
        pg.draw.rect(self.screen, self.food.color, self.food.rect)
        
        # Drawing grid
        if self.grid:
            for i in range(1, const.WIDTH//const.BLOCK_SIZE):
                start_horizontal = const.BLOCK_SIZE*i, 0
                end_horizontal = const.BLOCK_SIZE*i, const.HEIGHT
                start_vertical = 0, const.BLOCK_SIZE*i
                end_vertical = const.WIDTH, const.BLOCK_SIZE*i
                
                pg.draw.line(self.screen, const.GRID_COLOR, start_horizontal, end_horizontal)
                pg.draw.line(self.screen, const.GRID_COLOR, start_vertical, end_vertical)
        
        # Infos texts
        try:
            mean_score = round(mean_scores[-1], 1)
        except IndexError:
            mean_score = 0.0
                        
        perc_exploration = (
            self.agent.n_exploration 
            / (self.agent.n_exploration + self.agent.n_exploitation) 
            * 100
        )
        perc_exploitation = (
            self.agent.n_exploitation 
            / (self.agent.n_exploration + self.agent.n_exploitation)
            * 100
        )
        
        infos = [
            f"Score: {self.score}",
            f"Mean score: {mean_score}",
            f"Epsilon: {round(self.agent.epsilon, 4)}",
            f"Exploration: {round(perc_exploration, 3)}%",
            f"Exploitation: {round(perc_exploitation, 3)}%",
            f"Game: {self.agent.n_games}",
            f"Time: {int(pg.time.get_ticks() / 1e3)}s",
            f"FPS: {int(self.clock.get_fps())}",
        ]
        
        # Drawing infos
        for i, info in enumerate(infos):
            message(
                self.screen, 
                info,
                const.INFOS_SIZE,
                const.INFOS_COLOR, 
                (5, 5 + i*const.Y_OFFSET_INFOS)
            )

        pg.display.flip()
        self.clock.tick(const.FPS)


class Food(pg.sprite.Sprite):
    def __init__(self, game):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.size = const.BLOCK_SIZE
        self.color = pg.Color("Green")
        self.place()

    def place(self):
        # idx_x = random.randint(1, (const.WIDTH//const.BLOCK_SIZE)-1)
        # idx_y = random.randint(1, (const.HEIGHT//const.BLOCK_SIZE)-1)

        # x = idx_x*const.BLOCK_SIZE
        # y = idx_y*const.BLOCK_SIZE
        x = 7*const.BLOCK_SIZE
        y = 7*const.BLOCK_SIZE
        
        self.pos = vec(x, y)
        self.rect = pg.Rect(self.pos.x, self.pos.y, self.size, self.size)
        
        # Checking for potential collisions with other elements
        obstacles = [enemy.rect for enemy in self.game.enemies] + [self.game.agent.rect]
        collision_list = self.rect.collidelist(obstacles)
        
        # -1 is the return default value given by Pygame for the collidelist method if no collision found
        if collision_list != -1:
            self.place()


class Block(pg.sprite.Sprite):
    def __init__(self, x, y, size, color) -> None:
        pg.sprite.Sprite.__init__(self)
        self.size = size
        self.color = color
        self.pos = vec(x, y)
        self.rect = pg.Rect(self.pos.x, self.pos.y, self.size, self.size)
        
class Block2(pg.sprite.Sprite):
    def __init__(self, x, y, size, color) -> None:
        pg.sprite.Sprite.__init__(self)
        self.size = size
        self.color = color
        self.pos = vec(x, y)
        self.rect = pg.Rect(self.pos.x, self.pos.y, self.size, self.size)
        self.tagged = False
