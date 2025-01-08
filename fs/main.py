from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import argparse
import random
import os
from multiprocessing import Pool

import pygame
import sys
import numpy as np
from elements import COLOURS, ELEMENTS, Particle, Metal, Water, Sand, Acid
from utils import bezier


@dataclass
class Config:
    width: int
    height: int
    ms_per_frame: float
    scale: int
    num_sims: int
    aircolor: tuple[int, int, int]


@dataclass
class PenStrokeAction:
    x: int
    y: int
    frame_delay: int


@dataclass
class PenStroke:
    particle: type[Particle]
    pen_size: int
    path: list[PenStrokeAction]


@dataclass
class SimulationConfig(Config):
    data_path: str
    max_frames: int
    n_strokes: int


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


class ReplayRenderer(Renderer):
    def __init__(self, config: SimulationConfig):
        self.frames = np.load(config.data_path + "/frames.npy")
        self.frame_idx = 0
        pygame.init()
        self.window = pygame.display.set_mode((config.width, config.height))
        pygame.display.set_caption("Falling Sand Replay")

    def draw(self, state: dict[tuple[int, int], Particle], config: Config):
        if self.frame_idx >= len(self.frames):
            pygame.quit()
            sys.exit()

        frame = self.frames[self.frame_idx]
        surface = pygame.surfarray.make_surface(frame)
        self.window.blit(surface, (0, 0))
        pygame.display.update()
        self.frame_idx += 1


class SimulationRenderer(Renderer):
    def __init__(self, config: SimulationConfig):
        self.window = np.memmap(
            dtype=np.uint8,
            shape=(
                config.max_frames,
                config.height,
                config.width,
                3,
            ),
            mode="w+",
            filename=f"{config.data_path}/frames.npy",
        )
        self.frame = 0

    def draw(self, state: dict[tuple[int, int], Particle], config: Config):
        for element in state.values():
            self.window[
                self.frame,
                element.y : element.y + config.scale,
                element.x : element.x + config.scale,
                :,
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
        if pensize == 0 and state.get((x, y)):
            state[(x, y)] = active_element(x, y)  # place 1 pixel
        else:
            for xdisp in range(-pensize, pensize):
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


class DummyInputHandler(InputHandler):
    def __init__(self, config: Config):
        self.config = config

    def update(self, state: dict[tuple[int, int], Particle]):
        pass


class SimulationInputHandler(InputHandler):
    def __init__(self, config: SimulationConfig):
        self.n_strokes = config.n_strokes
        self.max_x = config.width // config.scale
        self.max_y = config.height // config.scale
        self.stroke_idx = 0
        self.action_idx = 0
        self.action_frame_delay = 0
        self.current_frame = -1
        self.actions = np.memmap(
            dtype=np.uint8,
            shape=(config.max_frames, 4),
            mode="w+",
            filename=f"{config.data_path}/actions.npy",
        )
        self.generate_pen_strokes()

    def generate_pen_strokes(self):
        self.strokes = []
        for _ in range(self.n_strokes):
            path = bezier(4, (0, self.max_x), (0, self.max_y), 0.01)
            frame_delays = [random.randint(1, 1)] + [1] * 99
            self.strokes.append(
                PenStroke(
                    particle=random.choice(ELEMENTS),
                    pen_size=2,
                    path=[
                        PenStrokeAction(xy[0], xy[1], f)
                        for xy, f in zip(path, frame_delays)
                    ],
                )
            )

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
        if self.current_frame == self.config.max_frames:
            sys.exit()
        if self.current_frame < self.action_frame_delay + current_action.frame_delay:
            return
        self.pendraw(
            current_action.x,
            current_action.y,
            state,
            current_stroke.pen_size,
            current_stroke.particle,
        )
        self.actions[self.current_frame, 0] = current_action.x
        self.actions[self.current_frame, 1] = current_action.y
        self.actions[self.current_frame, 2] = current_stroke.pen_size
        self.actions[self.current_frame, 3] = ELEMENTS.index(current_stroke.particle)

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


def create_arg_parser():
    parser = argparse.ArgumentParser(description="Falling Sand Simulation")

    parser.add_argument(
        "--input-handler",
        choices=["pygame", "simulation"],
        default="pygame",
        help="Select input handler type",
    )

    parser.add_argument(
        "--renderer",
        choices=["pygame", "simulation", "replay"],
        default="pygame",
        help="Select renderer type",
    )

    # Config options.
    parser.add_argument("--width", type=int, default=400, help="Window width")
    parser.add_argument("--height", type=int, default=400, help="Window height")
    parser.add_argument(
        "--ms-per-frame",
        type=float,
        default=50.0,
        help="Milliseconds per frame (default: 50.0 for 20fps)",
    )
    parser.add_argument("--scale", type=int, default=2, help="Pixel scale factor")
    parser.add_argument("--num-sims", type=int, default=1, help="Number of simulations")
    parser.add_argument("--aircolor", type=str, default="black", help="Air color")
    parser.add_argument(
        "--data-path", default="data", help="Path for saving/loading simulation data"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=1000,
        help="Maximum number of frames for simulation",
    )
    parser.add_argument(
        "--n-strokes", type=int, default=5, help="Number of strokes for simulation"
    )

    return parser


def create_engine(args: argparse.Namespace) -> Engine:
    config = SimulationConfig(
        width=args.width,
        height=args.height,
        ms_per_frame=args.ms_per_frame,
        scale=args.scale,
        num_sims=args.num_sims,
        aircolor=COLOURS[args.aircolor],
        data_path=args.dta_path,
        max_frames=args.max_frames,
        n_strokes=args.n_strokes,
    )
    renderers = {
        "pygame": PygameRenderer,
        "simulation": SimulationRenderer,
        "replay": ReplayRenderer,
    }
    renderer = renderers[args.renderer](config)
    input_handlers = {
        "pygame": PygameInputHandler,
        "simulation": SimulationInputHandler,
        "dummy": DummyInputHandler,
    }
    # In replay mode, no input is accepted.
    input_handler = input_handlers[
        args.input_handler if args.renderer != "replay" else "dummy"
    ](config)
    return Engine(config, renderer, input_handler)


def main():
    parser = create_arg_parser()
    args = parser.parse_args()
    if args.num_sims > 1:
        with Pool(os.cpu_count()) as pool:
            pool.map(lambda _: create_engine(args).run(), range(args.num_sims))
    else:
        create_engine(args).run()


if __name__ == "__main__":
    main()
