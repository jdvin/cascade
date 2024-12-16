# from FallingSand import Particle
from abc import abstractmethod
import random

scale = 2
aircolor = (0, 0, 0)
allelements = {}
(Nx, Ny) = (400, 450)
FPS = 20

yellow = (181, 137, 0)
beige = (238, 232, 213)
darkbeige = (171, 152, 92)
orange = (203, 75, 22)  # orange
blue = (38, 139, 210)  # blue
red = (220, 50, 47)
green = (133, 153, 0)
grey = (88, 110, 117)
magenta = (211, 54, 130)


class Particle:
    def __init__(self, x, y):
        # allelements is a REFERENCE to a dictionary containing all element instances
        self.x = x
        self.y = y
        self.dissolve_chance = 0.0
        self.max_updates = 0
        self.density = 0
        self.flow_chance = 0.0
        self.elasticity = 0

    @property
    def color(self) -> tuple[int, int, int]:
        return (0, 0, 0)

    def update(self, state):

        if self.checkkill(self.x, self.y, state):
            return
        updates = 0  # start with zero actions
        flowdirection = (
            (random.randint(0, 1) * 2 - 1) if random.random() < self.flow_chance else 0
        )
        while updates < self.max_updates:
            # Fall in proportion to density.
            for _ in range(1, self.density + 1):
                if self.goto(self.x, self.y + 1, state):
                    updates += 1

            if self.goto(self.x + flowdirection, self.y, state):
                pass
            elif self.elasticity and self.goto(
                self.x - flowdirection * self.elasticity, self.y, state
            ):
                flowdirection *= -self.elasticity
            updates += 1

    def checkkill(self, x, y, state):  # checks to see if particle can be deleted
        if not 0 <= self.x <= Nx:
            del state[(x, y)]
            return True
        elif not 0 <= self.y <= 300:
            del state[(x, y)]
            return True
        return False

    def goto(self, newx, newy, state):
        if (
            not state.get((newx, newy)) or random.random() < self.dissolve_chance
        ):  # go ahead with move IF space is free
            (oldx, oldy) = (self.x, self.y)
            del state[(oldx, oldy)]
            (self.x, self.y) = (newx, newy)
            state[(newx, newy)] = self
            return True
        return False


class Metal(Particle):  # metal just sits there and doesnt move
    def __init__(self, x, y):
        super().__init__(x, y)

    @property
    def color(self):
        return grey


class Water(Particle):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_updates: int = 3
        self.dissolve_chance: float = 0.0
        self.flow_chance: float = 0.90
        self.density: int = 2
        self.elasticity: int = 1

    @property
    def color(self):
        return blue

    def goto(self, newx, newy, state):
        target = state.get((newx, newy))
        if isinstance(target, Sand):
            target.is_wet = True

        return super().goto(newx, newy, state)


class Acid(Particle):  # like water, can eat through metal
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_updates = 2
        self.dissolve_chance = 0.01
        self.flow_chance = 0.9
        self.density = 2
        self.elasticity = 1

    @property
    def color(self):
        return green


class Sand(Particle):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.is_wet = False
        self.max_updates = 2
        self.density = 3

    @property
    def color(self):
        return darkbeige if self.is_wet else beige

    def goto(self, newx, newy, state):
        # SAND/WATER interaction - sand changes color and overwrites water
        target = state.get((newx, newy))
        if isinstance(target, Water):
            self.is_wet = True  # CHANGE SAND COLOR TO WETSAND COLOR
            overwritechance = 1  # set overwrite
            # WETSAND/DRYSAND interaction (wetness should spread slowly through sand)
        if (
            self.is_wet
            and isinstance(target, Sand)
            and target.is_wet
            and random.random() < 0.08
        ):
            state[(newx, newy)].is_wet = True
        return super().goto(newx, newy, state)

    def update(self, state):
        """
        Sand is like water but it hardly ever flows sideways, and if it gets wet
        then it solidifies and becomes immovable. Wet sand slowly "infects" nearby dry sand
        (This behaviour is codified inside the goto function)
        """

        self.flowchance = 0.05 if not self.is_wet else 0

        return super().update(state)
