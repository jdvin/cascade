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
class SimPenStrokeAction:
    x: int
    y: int
    frame_delay: int


@dataclass
class SimPenStroke:
    particle: type[Particle]
    pen_size: int
    path: list[SimPenStrokeAction]


@dataclass
class SimulationConfig(Config):
    data_path: str = "data"
    max_frames: int = 1000
    pen_strokes: list[SimPenStroke] = field(
        default_factory=lambda: [
            SimPenStroke(
                particle=Metal,
                pen_size=2,
                path=[
                    SimPenStrokeAction(x, y, f)
                    for x, y, f in zip(range(50, 100), range(50, 100), [20] + [1] * 49)
                ],
            ),
            SimPenStroke(
                particle=Metal,
                pen_size=2,
                path=[
                    SimPenStrokeAction(x, y, f)
                    for x, y, f in zip(range(100, 150), range(100, 50, -1), [1] * 50)
                ],
            ),
            SimPenStroke(
                particle=Sand,
                pen_size=2,
                path=[
                    SimPenStrokeAction(x, y, f)
                    for x, y, f in zip(range(50, 100), [40] * 50, [1] * 50)
                ],
            ),
            SimPenStroke(
                particle=Water,
                pen_size=2,
                path=[
                    SimPenStrokeAction(x, y, f)
                    for x, y, f in zip(range(100, 150), [40] * 50, [1] * 50)
                ],
            ),
        ]
    )


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
    config: Config

    def pendraw(
        self,
        x: int,
        y: int,
        state: dict[tuple[int, int], Particle],
        pensize: int,
        active_element: type[Particle],
    ):
        # this function places a suitable number of elements in a circle at the position specified
        if pensize == 0 and state.get((x, y)):
            state[(x, y)] = active_element(x, y)  # place 1 pixel
        else:
            for xdisp in range(-pensize, pensize):  # penzize is the radius
                for ydisp in range(-pensize, pensize):
                    if not state.get((x + xdisp, y + ydisp)):
                        state[(x + xdisp, y + ydisp)] = active_element(
                            x + xdisp, y + ydisp
                        )

    @abstractmethod
    def update(self, state: dict[tuple[int, int], Particle]):
        pass


class PygameInputHandler(InputHandler):
    def __init__(self, config: Config):
        self.config = config
        self.active_element: type[Particle] = Metal
        self.pensize: int = 1

    def update(self, state: dict[tuple[int, int], Particle]):
        for event in pygame.event.get():  # detect events
            if event.type == pygame.QUIT:  # detect attempted exit
                pygame.quit()
                sys.exit()
            if pygame.mouse.get_pressed()[0]:
                self.pendraw(
                    int(pygame.mouse.get_pos()[0] / self.config.scale),
                    int(pygame.mouse.get_pos()[1] / self.config.scale),
                    state,
                    self.pensize,
                    self.active_element,
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


class SimulationInputHandler(InputHandler):
    def __init__(self, config: SimulationConfig):
        self.strokes = config.pen_strokes
        self.stroke_idx = 0
        self.action_idx = 0
        self.action_frame_delay = 0
        self.current_frame = -1

    def update(self, state: dict[tuple[int, int], Particle]):
        if self.action_idx >= len(self.strokes[self.stroke_idx].path):
            if self.stroke_idx == len(self.strokes) - 1:
                # We are at the end.
                return
            self.action_idx = 0
            self.stroke_idx += 1
        current_stroke = self.strokes[self.stroke_idx]
        current_action = current_stroke.path[self.action_idx]
        self.current_frame += 1
        if self.current_frame < self.action_frame_delay + current_action.frame_delay:
            return
        self.pendraw(
            current_action.x,
            current_action.y,
            state,
            current_stroke.pen_size,
            current_stroke.particle,
        )
        self.action_frame_delay += current_action.frame_delay
        self.action_idx += 1


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
                continue
            for particle in list(self.state.values()):
                try:
                    particle.update(self.state, self.config)
                except KeyError:
                    pass
            self.input_handler.update(self.state)
            self.renderer.draw(self.state, self.config)
            frame_time = 0


def main():
    config = SimulationConfig()
    # input_handler = PygameInputHandler(config)
    input_handler = SimulationInputHandler(config)
    renderer = PygameRenderer(config)
    engine = Engine(config, renderer, input_handler)
    engine.run()


if __name__ == "__main__":
    main()
