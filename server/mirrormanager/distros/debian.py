from base import Distro
import re

class DebianDistro(Distro):
    def get_version_from_path(path):
        # Debian/Ubuntu versioning
        s = r'dists/(\w+)/' # this ignores 10.10 and maverick-{anything}, but picks up 'maverick'
        m = re.search(re.compile(s), path)
        if m is not None:
            return m.group(1)
        return None
