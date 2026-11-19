"""A small turtle module for PythonIDE online.

Python's real turtle needs a desktop window (Tk), which a browser does not
have. This module keeps the same names and sends drawing commands to the
page, which draws them on the "Drawing" panel.
"""

import json
import math

import ide

__all__ = [
    "Turtle", "Pen", "RawTurtle", "Screen", "done", "mainloop", "exitonclick", "bye", "bgcolor",
    "title", "setup", "colormode", "tracer", "update", "speed", "forward", "fd", "backward", "bk",
    "back", "left", "lt", "right", "rt", "goto", "setpos", "setposition", "setx", "sety",
    "setheading", "seth", "home", "circle", "dot", "penup", "pu", "up", "pendown", "pd", "down",
    "pensize", "width", "color", "pencolor", "fillcolor", "begin_fill", "end_fill", "hideturtle",
    "ht", "showturtle", "st", "position", "pos", "xcor", "ycor", "heading", "write", "clear",
    "reset", "shape", "stamp", "isdown", "distance", "towards", "delay", "screensize",
]

_pending = []
_colormode = 1.0
_turtles = []


def _send(cmd):
    _pending.append(cmd)
    if len(_pending) >= 200:
        _flush()


def _flush():
    if _pending:
        ide.post(json.dumps({"t": "turtle", "cmds": _pending}))
        del _pending[:]


def _css(color):
    """Turn a turtle colour ("red", "#ff0000", (1, 0, 0)) into a CSS colour."""
    if isinstance(color, str):
        return color
    r, g, b = color
    if _colormode == 1.0:
        r, g, b = r * 255, g * 255, b * 255
    return "rgb({},{},{})".format(int(r), int(g), int(b))


class Screen:
    """There is only one screen, like in real turtle."""

    def bgcolor(self, *color):
        if color:
            _send({"op": "bg", "color": _css(color[0] if len(color) == 1 else color)})

    def title(self, text):
        _send({"op": "title", "text": str(text)})

    def setup(self, width=None, height=None, startx=None, starty=None):
        pass

    def screensize(self, canvwidth=None, canvheight=None, bg=None):
        if bg:
            self.bgcolor(bg)

    def colormode(self, mode=None):
        global _colormode
        if mode is None:
            return _colormode
        _colormode = 255 if mode == 255 else 1.0

    def tracer(self, n=None, delay=None):
        if n is not None:
            _send({"op": "tracer", "on": bool(n)})

    def update(self):
        _flush()

    def delay(self, delay=None):
        pass

    def mainloop(self):
        _flush()

    done = mainloop
    exitonclick = mainloop

    def bye(self):
        _flush()

    def onclick(self, *args, **kwargs):
        pass

    onscreenclick = onclick

    def onkey(self, *args, **kwargs):
        pass

    def listen(self, *args, **kwargs):
        pass


_screen = Screen()


class Turtle:
    def __init__(self, shape="classic", visible=True):
        self._id = len(_turtles)
        _turtles.append(self)
        self._x = 0.0
        self._y = 0.0
        self._heading = 0.0  # degrees, 0 = east, counter-clockwise
        self._down = True
        self._pencolor = "black"
        self._fillcolor = "black"
        self._size = 1
        self._speed = 3
        self._visible = visible
        self._fill = None
        self._pose()

    # -- sending ---------------------------------------------------------------

    def _pose(self):
        _send({"op": "pose", "id": self._id, "x": self._x, "y": self._y,
               "h": self._heading, "visible": self._visible, "color": self._pencolor})

    def _move_to(self, x, y):
        if self._down:
            _send({"op": "line", "id": self._id, "x1": self._x, "y1": self._y, "x2": x, "y2": y,
                   "color": self._pencolor, "width": self._size, "speed": self._speed})
        else:
            _send({"op": "move", "id": self._id, "speed": self._speed})
        self._x, self._y = float(x), float(y)
        if self._fill is not None:
            self._fill.append([self._x, self._y])
        self._pose()

    # -- moving ----------------------------------------------------------------

    def forward(self, distance):
        rad = math.radians(self._heading)
        self._move_to(self._x + distance * math.cos(rad), self._y + distance * math.sin(rad))

    fd = forward

    def backward(self, distance):
        self.forward(-distance)

    bk = back = backward

    def left(self, angle):
        self._heading = (self._heading + angle) % 360
        self._pose()

    lt = left

    def right(self, angle):
        self.left(-angle)

    rt = right

    def goto(self, x, y=None):
        if y is None:
            x, y = x
        self._move_to(x, y)

    setpos = setposition = goto

    def setx(self, x):
        self._move_to(x, self._y)

    def sety(self, y):
        self._move_to(self._x, y)

    def setheading(self, angle):
        self._heading = angle % 360
        self._pose()

    seth = setheading

    def home(self):
        self._move_to(0, 0)
        self.setheading(0)

    def circle(self, radius, extent=None, steps=None):
        if extent is None:
            extent = 360
        if steps is None:
            frac = abs(extent) / 360
            steps = 1 + int(min(11 + abs(radius) / 6.0, 59.0) * frac)
        w = extent / steps
        w2 = 0.5 * w
        length = 2.0 * radius * math.sin(math.radians(w2))
        if radius < 0:
            length, w, w2 = -length, -w, -w2
        self.left(w2)
        for _ in range(steps):
            self.forward(length)
            self.left(w)
        self.left(-w2)

    def dot(self, size=None, *color):
        if size is None:
            size = max(self._size + 4, 2 * self._size)
        c = _css(color[0] if len(color) == 1 else color) if color else self._pencolor
        _send({"op": "dot", "x": self._x, "y": self._y, "size": size, "color": c})

    def stamp(self):
        _send({"op": "stamp", "id": self._id, "x": self._x, "y": self._y, "h": self._heading,
               "color": self._fillcolor})
        return 0

    def write(self, arg, move=False, align="left", font=("Arial", 8, "normal")):
        name, size, style = (list(font) + ["Arial", 8, "normal"])[:3]
        _send({"op": "text", "x": self._x, "y": self._y, "text": str(arg), "color": self._pencolor,
               "font": "{} {}px {}".format(style if style != "normal" else "", int(size) * 4 // 3, name),
               "align": align})

    # -- pen ---------------------------------------------------------------------

    def penup(self):
        self._down = False

    pu = up = penup

    def pendown(self):
        self._down = True

    pd = down = pendown

    def isdown(self):
        return self._down

    def pensize(self, width=None):
        if width is None:
            return self._size
        self._size = width

    width = pensize

    def speed(self, speed=None):
        if speed is None:
            return self._speed
        names = {"fastest": 0, "fast": 10, "normal": 6, "slow": 3, "slowest": 1}
        speed = names.get(speed, speed)
        self._speed = int(speed) if 0.5 <= speed <= 10.5 else 0

    def pencolor(self, *color):
        if not color:
            return self._pencolor
        self._pencolor = _css(color[0] if len(color) == 1 else color)
        self._pose()

    def fillcolor(self, *color):
        if not color:
            return self._fillcolor
        self._fillcolor = _css(color[0] if len(color) == 1 else color)

    def color(self, *args):
        if not args:
            return self._pencolor, self._fillcolor
        if len(args) == 1:
            self.pencolor(args[0])
            self.fillcolor(args[0])
        elif len(args) == 2:
            self.pencolor(args[0])
            self.fillcolor(args[1])
        else:
            self.pencolor(args)
            self.fillcolor(args)

    def begin_fill(self):
        self._fill = [[self._x, self._y]]

    def end_fill(self):
        if self._fill and len(self._fill) > 2:
            _send({"op": "fill", "points": self._fill, "color": self._fillcolor})
        self._fill = None

    def filling(self):
        return self._fill is not None

    def hideturtle(self):
        self._visible = False
        self._pose()

    ht = hideturtle

    def showturtle(self):
        self._visible = True
        self._pose()

    st = showturtle

    def isvisible(self):
        return self._visible

    def shape(self, name=None):
        return "classic"

    def shapesize(self, *args, **kwargs):
        pass

    turtlesize = shapesize

    # -- information -------------------------------------------------------------

    def position(self):
        return (round(self._x, 2), round(self._y, 2))

    pos = position

    def xcor(self):
        return self._x

    def ycor(self):
        return self._y

    def heading(self):
        return self._heading

    def distance(self, x, y=None):
        if y is None:
            x, y = x
        return math.hypot(x - self._x, y - self._y)

    def towards(self, x, y=None):
        if y is None:
            x, y = x
        return math.degrees(math.atan2(y - self._y, x - self._x)) % 360

    def clear(self):
        _send({"op": "clear"})

    def reset(self):
        self.clear()
        self.__init__()

    def getscreen(self):
        return _screen

    def hide(self):
        self.hideturtle()


Pen = RawTurtle = Turtle
_default = None


def _turtle():
    global _default
    if _default is None:
        _default = Turtle()
    return _default


def _make(name):
    def function(*args, **kwargs):
        return getattr(_turtle(), name)(*args, **kwargs)

    function.__name__ = name
    return function


for _name in ["forward", "fd", "backward", "bk", "back", "left", "lt", "right", "rt", "goto",
              "setpos", "setposition", "setx", "sety", "setheading", "seth", "home", "circle", "dot",
              "stamp", "write", "penup", "pu", "up", "pendown", "pd", "down", "isdown", "pensize",
              "width", "speed", "pencolor", "fillcolor", "color", "begin_fill", "end_fill",
              "filling", "hideturtle", "ht", "showturtle", "st", "isvisible", "shape", "shapesize",
              "position", "pos", "xcor", "ycor", "heading", "distance", "towards", "clear", "reset"]:
    globals()[_name] = _make(_name)

bgcolor = _screen.bgcolor
title = _screen.title
setup = _screen.setup
screensize = _screen.screensize
colormode = _screen.colormode
tracer = _screen.tracer
update = _screen.update
delay = _screen.delay
done = mainloop = exitonclick = _screen.mainloop
bye = _screen.bye


def getscreen():
    return _screen


class Terminator(Exception):
    pass


class TurtleGraphicsError(Exception):
    pass
