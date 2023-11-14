def read_config(filename):
    config = dict()
    with open(filename) as fh:
        exec(compile(fh.read(), filename, "exec"), config)
    return config
