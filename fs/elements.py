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

    @property
    def color(self) -> tuple[int, int, int]:
        return (0, 0, 0)

    @abstractmethod
    def update(self, state: dict[tuple[int, int], "Particle"]):
        pass

    def checkkill(self, x, y, state):  # checks to see if particle can be deleted
        if not 0 <= self.x <= Nx:
            del state[(x, y)]
            return True
        elif not 0 <= self.y <= 300:
            del state[(x, y)]
            return True
        return False

    def goto(self, newx, newy, state, overwritechance=0.0):
        # LIQUID/LIQUID interaction

        # DEFAULT behaviour
        if (
            not state.get((newx, newy)) or random.random() < overwritechance
        ):  # go ahead with move IF space is free
            (oldx, oldy) = (self.x, self.y)
            del state[(oldx, oldy)]  # delete current location from instance dictionary
            (self.x, self.y) = (newx, newy)
            state[(newx, newy)] = self
            # mark locations as changed


class Metal(Particle):  # metal just sits there and doesnt move
    def __init__(self, x, y):
        super().__init__(x, y)

    @property
    def color(self):
        return grey


class Water(Particle):  # water should flow and fall
    def __init__(self, x, y):
        super().__init__(x, y)

    @property
    def color(self):
        return blue

    def goto(self, newx, newy, state, overwritechance=0.0):
        target = state.get((newx, newy))
        if isinstance(target, Sand):
            target.is_wet = True

        super().goto(newx, newy, state, overwritechance)

    def update(self, state):
        """
        Water behaviour is like so: water is allowed to make 2-3 "actions" per turn
        it first tries to fall downward, with a chance to move left or right as it does so
        if it cant fall down it is then almost guaranteed to flow left or right
        if it hits a wall it will "reflect" off and move in the other direction
        """
        if self.checkkill(self.x, self.y, state):
            return
        updates = 0  # start with zero actions
        flowdirection = (
            random.randint(0, 1) * 2 - 1
        )  # returns +-1, decides if particle moves left or right
        if random.random() > 0.9:  # small chance to not flow at all
            flowdirection = 0  # i.e: dont flow
        while updates < 2:
            if self.goto(self.x, self.y + 1, state):
                updates += 1  # log one cycle as complete
                if self.goto(self.x, self.y + 1, state):
                    updates += 1  # log one cycle as complete
            if self.goto(
                self.x + flowdirection, self.y, state
            ):  # if space is available to go sideways
                pass
            elif self.goto(
                self.x - flowdirection, self.y, state
            ):  # if one side is blocked, "reflect" off other way
                flowdirection *= -1
            updates += 0.67


class Acid(Particle):  # like water, can eat through metal
    def __init__(self, x, y):
        super().__init__(x, y)

    @property
    def color(self):
        return green

    def update(self, state):
        """
        ACID behaves like water but has a certain chance to eat through containing
        materials, defined in the variable "acidchance"
        """
        if self.checkkill(self.x, self.y, state):
            return
        acidchance = 0.01
        updates = 0  # start with zero actions
        flowdirection = (
            random.randint(0, 1) * 2 - 1
        )  # returns +-1, decides if particle moves left or right
        if random.random() > 0.9:  # small chance to not flow at all
            flowdirection = 0  # i.e: dont flow
        while updates < 2:
            if self.goto(self.x, self.y + 1, state, acidchance):
                updates += 1  # log one cycle as complete
                if self.goto(self.x, self.y + 1, state, acidchance):
                    updates += 1  # log one cycle as complete
            if self.goto(
                self.x + flowdirection, self.y, state, acidchance
            ):  # if space is available to go sideways
                pass
            elif self.goto(
                self.x - flowdirection, self.y, state, acidchance
            ):  # if one side is blocked, "reflect" off other way
                pass
            updates += 1


class Sand(Particle):
    def __init__(self, x, y):
        self.type = "solid"
        self.is_wet = False
        self.flowchance = (
            0.05  # chance to behave as liquid per tick (CAN CHANGE IF WET)
        )
        super().__init__(x, y)

    @property
    def color(self):
        return darkbeige if self.is_wet else beige

    def goto(self, newx, newy, state, overwritechance=0.0):
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
        super().goto(newx, newy, state, overwritechance)

    def update(self, state):
        """
        Sand is like water but it hardly ever flows sideways, and if it gets wet
        then it solidifies and becomes immovable. Wet sand slowly "infects" nearby dry sand
        (This behaviour is codified inside the goto function)
        """
        if self.checkkill(self.x, self.y, state):
            return
        updates = 0  # start with zero actions

        flowchance = 0.05  # 5% chanc eto flow per tick if dry
        if self.is_wet:
            flowchance = 0  # never flow if wet

        flowdirection = (
            random.randint(0, 1) * 2 - 1
        )  # returns +-1, decides if particle moves left or right
        if random.random() > flowchance:  # LARGE chance to not flow at all for sand
            flowdirection = 0  # i.e: dont flow
        while updates < 2:
            if self.goto(
                self.x, self.y + 2, state
            ):  # if space is available to fall down 2 spaces
                updates += 2
            elif self.goto(self.x, self.y + 1, state):
                updates += 1  # log one cycle as complete
            if self.goto(
                self.x + flowdirection, self.y, state
            ):  # if space is available to go sideways
                pass
            #            elif self.goto(self.x - flowdirection, self.y): #if one side is blocked, "reflect" off other way
            #                pass
            updates += 2
