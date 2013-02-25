from turbogears.util import load_class
import re

class Distro(object):
    legacy_site_name = 'Fedora Mirror'

    def __init__(self):
        super(Distro, self).__init__()
        glob_ns = globals()


        classname = 'Base'
        class_path = config.get('mirrormanager.distro', classname)
        class_ = load_class(class_path)
        if class_:
            log.info('Successfully loaded "%s".', class_path)
            glob_ns['%s_class' % classname] = class_
        else:
            log.error('Could not load class "%s".'
                      ' Check mirrormanager.distro setting')


    def trim_os_from_dirname(dirname):
        # trim the /os off the name
        index = dirname.rfind('/os')
        if index > 0:
            dirname = dirname[:index]
        return dirname

    def get_version_from_path(path):
        # Fedora versioning
        s = r'/?(([\.\d]+)(\-\w+)?)/'
        m = re.search(re.compile(s), path)
        if m is not None:
            return m.group(1)
        return None
