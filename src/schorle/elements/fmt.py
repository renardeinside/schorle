class fmt:
    def __init__(self, fmt_string, *args):
        self.fmt_string = fmt_string
        self.args = args

    def __str__(self):
        return self.fmt_string.format(*self.args)
