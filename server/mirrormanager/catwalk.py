from turbogears import expose
from turbogears.toolbox.catwalk import CatWalk
from mirrormanager.lib import project_dict

class MMCatWalk(CatWalk):
    @expose(template="kid:mirrormanager.templates.catwalk")
    def index(self):
        # same as CatWalk, merely changed the template
        return project_dict('catwalk', models=self.models())
