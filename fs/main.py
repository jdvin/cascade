from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import pygame
import sys
import numpy as np
from elements import Particle, Metal, Water, Sand, Acid


@dataclass
class Config:
    width: int = 400
    height: int = 450
    ms_per_frame: float = 1000 / 20  # 20 fps. Set to 0 to run as fast as possible.
    scale: int = 2
    aircolor: tuple[int, int, int] = (0, 0, 0)


@dataclass
class SimulationConfig(Config):
    data_path: str = "data"
    max_frames: int = 1000


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


class SimulationRenderer(Renderer):
    def __init__(self, config: SimulationConfig):
        self.window = np.memmap(
            dtype=np.uint8,
            shape=(config.height, config.width, 3, config.max_frames),
            mode="w+",
            filename=f"{config.data_path}/frames.npy",
        )
        self.frame = 0

    def draw(self, state: dict[tuple[int, int], Particle], config: Config):
        for element in state.values():
            self.window[
                element.y : element.y + config.scale,
                element.x : element.x + config.scale,
                :,
                self.frame,
            ] = element.color
        self.frame += 1


class InputHandler(ABC):
    active_element: type[Particle] = Metal
    pensize: int = 1

    def pendraw(self, x: int, y: int, state: dict[tuple[int, int], Particle]):
        # this function places a suitable number of elements in a circle at the position specified
        if self.pensize == 0 and state.get((x, y)):
            state[(x, y)] = self.active_element(x, y)  # place 1 pixel
        else:
            for xdisp in range(-self.pensize, self.pensize):  # penzize is the radius
                for ydisp in range(-self.pensize, self.pensize):
                    if not state.get((x + xdisp, y + ydisp)):
                        state[(x + xdisp, y + ydisp)] = self.active_element(
                            x + xdisp, y + ydisp
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
    config: Config
    renderer: Renderer
    input_handler: InputHandler
    state: dict[tuple[int, int], Particle] = field(default_factory=dict)

    def __post_init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()

    def run(self):
        frame_time = 0
        while True:
            frame_time += self.clock.tick()
            if frame_time < self.config.ms_per_frame:
                self.input_handler.update(self.config, self.state)
                continue
            for particle in list(self.state.values()):
                try:
                    particle.update(self.state, self.config)
                except KeyError:
                    pass
            self.renderer.draw(self.state, self.config)
            frame_time = 0


def main():
    config = Config()
    input_handler = PygameInputHandler()
    renderer = PygameRenderer(config)
    engine = Engine(config, renderer, input_handler)
    engine.run()


if __name__ == "__main__":
    main()
