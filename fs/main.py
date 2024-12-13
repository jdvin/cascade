from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import pygame
import sys
import numpy as np
from elements import Particle, Metal, Water, Sand, Acid, NullElement


@dataclass
class Config:
    width: int = 400
    height: int = 450
    fps: int = 20
    scale: int = 2
    aircolor: tuple[int, int, int] = (0, 0, 0)


class Renderer(ABC):
    window: Any

    @abstractmethod
    def draw(self, state: dict[tuple[int, int], Particle], config: Config):
        pass


class PygameRenderer(Renderer):
    def __init__(self, config: Config):
        self.window = pygame.display.set_mode((config.width, config.height))
        pygame.display.set_caption("Falling Sand")
        self.config = config
        self.surface = self.window.copy()

    def draw(self, state: dict[tuple[int, int], Particle], config: Config):
        self.surface.fill(config.aircolor)
        for element in state.values():
            self.surface.fill(
                element.color,
                pygame.Rect(
                    element.x * config.scale,
                    element.y * config.scale,
                    config.scale,
                    config.scale,
                ),
            )
        self.window.blit(self.surface, (0, 0))
        pygame.display.update()


class InputHandler(ABC):
    active_element: type[Particle]
    pensize: int

    def pendraw(self, x: int, y: int, state: dict[tuple[int, int], Particle]):
        # this function places a suitable number of elements in a circle at the position specified
        if self.pensize == 0 and state.get((x, y)):
            state[(x, y)] = self.active_element(x, y, state)  # place 1 pixel
        else:
            for xdisp in range(-self.pensize, self.pensize):  # penzize is the radius
                for ydisp in range(-self.pensize, self.pensize):
                    if state.get((x + xdisp, y + ydisp)):
                        state[(x + xdisp, y + ydisp)] = self.active_element(
                            x + xdisp, y + ydisp, state
                        )

    @abstractmethod
    def update(self, config: Config, state: dict[tuple[int, int], Particle]):
        pass


class PygameInputHandler(InputHandler):

    def update(self, config: Config, state: dict[tuple[int, int], Particle]):
        for event in pygame.event.get():  # detect events
            if event.type == pygame.QUIT:  # detect attempted exit
                pygame.quit()
                sys.exit()
            if pygame.mouse.get_pressed()[0]:
                self.pendraw(
                    int(pygame.mouse.get_pos()[0] / config.scale),
                    int(pygame.mouse.get_pos()[1] / config.scale),
                    state,
                )
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[49]:
            self.pensize = 1
            self.active_element = Metal
        if pressed_keys[50]:
            self.pensize = 2
            self.active_element = Water
        if pressed_keys[51]:
            self.pensize = 2
            self.active_element = Sand
        if pressed_keys[52]:
            self.pensize = 2
            self.active_element = Acid


@dataclass
class Engine:
    clock: pygame.time.Clock
    renderer: Renderer
    input_handler: InputHandler
    config: Config
    state: dict[tuple[int, int], Particle] = field(default_factory=dict)

    def __post_init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()

    def run(self):
        while True:
            self.clock.tick(self.config.fps)

            for particle in self.state.values():
                try:
                    particle.update(state)
                except KeyError:
                    pass

            self.renderer.draw(self.state, self.config)


def globalchecktarget(x, y):
    if ():  # return whatever object is at target location, or False if not
        return True  # if space is EMPTY return TRUE
    else:  # if space is occupied, return FALSE (used to return occupier but i nixed that functionality)
        return False  # return self.allelements.get( (x,y) )


def main():

    ###DEBUG INITIALISATION###
    #
    ##for x in range(50,100):
    ##    for y in range(24,26):
    ##        allelements[(x,y)] = Water(x,y,allelements,SURFACE)
    #    #SURFACE.fill((255,255,255), pygame.Rect(x*scale, y*scale, scale, scale))
    # for x in range(70, 150):  # build testing bucket
    #     y = 150
    #     allelements[(x, y)] = Metal(x, y, allelements, SURFACE)
    #     allelements[(x, y + 1)] = Metal(x, y + 1, allelements, SURFACE)
    # for y in range(138, 150):
    #     if y in range(145, 150):
    #         allelements[(70, y)] = Metal(70, y, allelements, SURFACE)
    #         allelements[(80, y)] = Metal(80, y, allelements, SURFACE)
    #     allelements[(149, y)] = Metal(149, y, allelements, SURFACE)

    ##########################
    ActiveElement = Metal  # default
    pensize = 1

    # INITIALISE NULLELEMENT


if __name__ == "__main__":
    main()
