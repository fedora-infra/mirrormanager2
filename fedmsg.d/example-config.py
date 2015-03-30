import socket
hostname = socket.gethostname().split('.')[0]

config = dict(
    endpoints={
        "mirrormanager2.%s" % hostname: [
            "tcp://127.0.0.1:6009",
            "tcp://127.0.0.1:6010",
            "tcp://127.0.0.1:6011",
            "tcp://127.0.0.1:6012",
        ],
    },
)
