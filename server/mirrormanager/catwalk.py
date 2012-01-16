from turbogears import expose
from turbogears.toolbox.catwalk import CatWalk

class MMCatWalk(CatWalk):
    @expose(template="mirrormanager.templates.catwalk")
    def index(self):
        # same as CatWalk, merely changed the template
        return dict(models=self.models())
