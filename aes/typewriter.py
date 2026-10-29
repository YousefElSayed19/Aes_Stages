import sys
import time

LEVELS = {"slow": 0.008, "normal": 0.002, "fast": 0.0005, "off": 0.0}
ORDER = ["slow", "normal", "fast", "off"]
DEFAULT_LEVEL = "normal"


class Typewriter:
    def __init__(self, level=DEFAULT_LEVEL):
        self.level = level
        self.skip = False

    def reset(self):
        self.level = DEFAULT_LEVEL
        self.skip = False

    def cycle(self):
        self.level = ORDER[(ORDER.index(self.level) + 1) % len(ORDER)]
        return self.level

    def write(self, text):
        stream = sys.stdout
        delay = LEVELS[self.level]
        if delay == 0 or self.skip or not stream.isatty():
            stream.write(text)
            stream.flush()
            return
        position = 0
        try:
            for position, ch in enumerate(text, 1):
                stream.write(ch)
                stream.flush()
                if not ch.isspace():
                    time.sleep(delay)
        except KeyboardInterrupt:
            self.skip = True
            stream.write(text[position:])
            stream.flush()
