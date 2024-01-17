from mirrormanager2 import default_config


def read_config(filename):
    config = dict()
    for key in dir(default_config):
        if key.isupper():
            config[key] = getattr(default_config, key)
    with open(filename) as fh:
        exec(compile(fh.read(), filename, "exec"), config)
    return config
