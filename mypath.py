from pathlib import Path


class MyPath(type(Path())):
    def size(self):
        return self.stat().st_size

    def is_good(self):
        return self.exists() and self.size() > 0

