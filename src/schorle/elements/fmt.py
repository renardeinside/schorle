class Formatter:
    def __init__(self, fmt_string, *args):
        self.fmt_string = fmt_string
        self.args = args

    def __str__(self):
        return self.fmt_string.format(*self.args)


def fmt(fmt_string, *args):
    return Formatter(fmt_string, *args)
