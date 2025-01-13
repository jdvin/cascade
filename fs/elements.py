import random

yellow = (181, 137, 0)
beige = (238, 232, 213)
darkbeige = (171, 152, 92)
orange = (203, 75, 22)
blue = (38, 139, 210)
red = (220, 50, 47)
green = (133, 153, 0)
grey = (88, 110, 117)
magenta = (211, 54, 130)
black = (0, 0, 0)

COLOURS = {
    "yellow": yellow,
    "beige": beige,
    "darkbeige": darkbeige,
    "orange": orange,
    "blue": blue,
    "red": red,
    "green": green,
    "grey": grey,
    "magenta": magenta,
    "black": black,
}


class Particle:
    def __init__(self, x, y):
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

    def update(self, state, config):
        if self.checkkill(self.x, self.y, state, config):
            return
        updates = 0
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

    def checkkill(self, x, y, state, config):
        if not 0 <= self.x <= config.width:
            del state[(x, y)]
            return True
        elif not 0 <= self.y <= config.height:
            del state[(x, y)]
            return True
        return False

    def goto(self, newx, newy, state, overwrite_chance: float = 0.0):
        target = state.get((newx, newy))
        if not target or random.random() < (overwrite_chance or self.dissolve_chance):
            (oldx, oldy) = (self.x, self.y)
            del state[(oldx, oldy)]
            (self.x, self.y) = (newx, newy)
            state[(newx, newy)] = self
            return True
        elif self.density > target.density:
            # A denser particle will swap places with a ligheter particle.
            # Effectively pushing it out of the way.
            target.x, target.y = self.x, self.y
            state[(self.x, self.y)] = target
            self.x, self.y = newx, newy
            state[(newx, newy)] = self
            return True

        return False


class Metal(Particle):  # metal just sits there and doesnt move
    def __init__(self, x, y):
        super().__init__(x, y)
        self.density = 5

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

    def goto(self, newx, newy, state, overwrite_chance: float = 0.0):
        target = state.get((newx, newy))
        if isinstance(target, Sand):
            target.is_wet = True

        return super().goto(newx, newy, state, overwrite_chance)


class Acid(Particle):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_updates = 2
        self.dissolve_chance = 0.01
        self.flow_chance = 0.9
        self.density = 3
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

    def goto(self, newx, newy, state, overwrite_chance: float = 0.0):
        target = state.get((newx, newy))
        if isinstance(target, Water):
            self.is_wet = True
        if (
            self.is_wet
            and isinstance(target, Sand)
            and target.is_wet
            and random.random() < 0.08
        ):
            state[(newx, newy)].is_wet = True
        return super().goto(newx, newy, state, overwrite_chance)

    def update(self, state, config):
        self.flowchance = 0.05 if not self.is_wet else 0
        self.density = 3 if not self.is_wet else 4

        return super().update(state, config)


ELEMENTS = [
    Metal,
    Sand,
    Water,
    Acid,
]
