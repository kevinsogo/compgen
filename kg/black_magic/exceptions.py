class CompileException(Exception):
    def __init__(self, module_loc, lineno, message):
        self.module_loc = module_loc
        self.lineno = lineno
        super(CompileException, self).__init__("[{} Line {}] {}".format(module_loc, lineno, message))

    @classmethod
    def for_parsed(cls, parsed, message):
        return cls(parsed.module_loc, parsed.start_lineno, message)
