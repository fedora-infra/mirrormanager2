"""CatWalk - model browser for TurboGears"""

__version__ = "0.9.4"
__author__ = "Ronald Jaramillo"
__email__ = "ronald@checkandhsare.com"
__copyright__ = "Copyright 2005 Ronald Jaramillo"
__license__ = "MIT"

from browse import Browse
import cPickle as pickle
import datetime
import os
import re
import socket
import struct
import time
try:
    import decimal
except ImportError:
    decimal = None

import pkg_resources

import cherrypy

try:
    import sqlobject
except ImportError:
    sqlobject = None

import turbogears
from turbogears import expose, identity


date_parser = re.compile(r"""^
    (?P<year>\d{4,4})
    (?:
        -
        (?P<month>\d{1,2})
        (?:
            -
            (?P<day>\d{1,2})
            (?:
                T
                (?P<hour>\d{1,2})
                :
                (?P<minute>\d{1,2})
                (?:
                    :
                    (?P<second>\d{1,2})
                    (?:
                        \.
                        (?P<dec_second>\d+)?
                    )?
                )?
                (?:
                    Z
                    |
                    (?:
                        (?P<tz_sign>[+-])
                        (?P<tz_hour>\d{1,2})
                        :
                        (?P<tz_min>\d{2,2})
                    )
                )
            )?
        )?
    )?
$""", re.VERBOSE)


def parse_datetime(s):
    """Parse a string and return a datetime object."""
    assert isinstance(s, basestring)
    r = date_parser.search(s)
    try:
        a = r.groupdict('0')
    except:
        raise ValueError, 'invalid date string format'
    dt = datetime.datetime(
        int(a['year']), int(a['month']) or 1, int(a['day']) or 1,
        # If not given these will default to 00:00:00.0
        int(a['hour']), int(a['minute']), int(a['second']),
        # Convert into microseconds
        int(a['dec_second'])*100000)
    t = datetime.timedelta(hours=int(a['tz_hour']), minutes=int(a['tz_min']))
    if a.get('tz_sign', '+') == "-":
        return dt + t
    else:
        return dt - t


class CatWalk(turbogears.controllers.Controller):
    """Model Browser.

    An administration tool for listing, creating, updating or deleting
    your SQLObject instances.

    """

    __label__ = "CatWalk"
    __version__ = "0.9"
    __author__ = "Ronald Jaramillo"
    __email__ = "ronald@checkandshare.com"
    __copyright__ = "Copyright 2005 Ronald Jaramillo"
    __license__ = "MIT"
    browse = Browse()
    need_project = True
    icon = "/tg_static/images/catwalk.png"

    def __init__(self, model=None):
        """CatWalk's initializer.

        @param model: reference to a project model module
        @type model: yourproject.model

        """

        try:
            if not sqlobject:
                raise ImportError, "The SQLObject package is not installed."
            if not model:
                model = turbogears.util.get_model()
            if not model:
                raise ImportError, ("No SQLObject model found.\n"
                    "If you are mounting CatWalk to your controller,\n"
                    "remember to import your model and pass a reference to it.")
            self.model = model
            if not self.models():
                raise ImportError, "The SQLObject model is empty."
            try:
                self._connection = model.hub
            except Exception:
                self._connection = sqlobject.sqlhub
        except Exception, e:
            raise ImportError, (
                "CatWalk failed to load your model file.\n" + str(e))
        self.browse.catwalk = self
        turbogears.config.update({'log_debug_info_filter.on': False})
        self.register_static_directory()

    def register_static_directory(self):
        static_directory = pkg_resources.resource_filename(__name__, 'static')
        turbogears.config.update({'/tg_toolbox/catwalk': {
            'static_filter.on': True,
            'static_filter.dir': static_directory}})

    [expose(format="json")]
    def error(self, msg='', _csrf_token=None):
        """Generic error handler for json replies."""
        return dict(error=msg)

    def load_object(self, object_name):
        """Return a class reference from the models module by name.

        @param object_name: name of the object
        @type object_name: string

        """
        try:
            obj = getattr(self.model, object_name)
        except:
            msg = 'Fail to get reference to object %s' % object_name
            raise cherrypy.HTTPRedirect(turbogears.url('error', msg=msg))
        return obj

    def load_instance(self, object_name, id):
        """Return and instance of the named object with the requested id"""
        obj = self.load_object(object_name)
        try:
            return obj.get(id)
        except:
            msg ='Fail to get instance of object: %s with id: %s' % (
                object_name, id)
            raise cherrypy.HTTPRedirect(turbogears.url('error', msg=msg))

    def object_field(self, row, column):
        """Get object field.

        Returns a dict containing the column name and value for the
        specific column and row,

        @param row: model instance
        @param column: dict containing columnName, title, type,
                    eventually join, joinMethodName and/or options
        @type column: dict

        """
        column_type = column.get('type', '')
        if column_type == 'SOSingleJoin':
            try:
                subject =  getattr(row, column['joinMethodName'])
                value = '%s' % getattr(subject, column['labelColumn'])
            except Exception:
                return {'column': column['columnName'],
                    'value': 'None', 'id': '0'}
            return {'column': column['columnName'], 'value': value}
        elif column_type in ('SORelatedJoin', 'SOSQLRelatedJoin'):
            return self.related_join_count(row, column)
        elif column_type in ('SOMultipleJoin', 'SOSQLMultipleJoin'):
            return self.multiple_join_count(row, column)
        elif column_type == 'SOForeignKey':
            return self.object_field_for_foreign_key(row, column)
        elif column_type == 'SOStringCol':
            value = getattr(row, column['columnName'])
            value = self.encode_label(value)
            return {'column': column['columnName'], 'value': value}
        else:
            value = getattr(row, column['columnName'])
            if value is not None:
                try:
                    value = u'%s' % value
                except UnicodeDecodeError:
                    value = unicode(value, 'UTF-8')
            return {'column': column['columnName'], 'value': value}

    def multiple_join_count(self, row, column):
        """Return the total number of related objects."""
        try:
            columnObject = getattr(self.model, column['join'])
            for clm in columnObject.sqlmeta.columnList:
                if type(clm) == sqlobject.SOForeignKey:
                    if column['objectName'] == clm.foreignKey:
                        foreign_key = clm
            fkName = foreign_key.name
            fkQuery = getattr(columnObject.q, str(fkName))
            select = columnObject.select(fkQuery == row.id)
            value = '%s' % select.count()
        except Exception:
            value = '0'
        return {'column': column['joinMethodName'], 'value': value}

    def related_join_count(self, row, column):
        """Return the total number of related objects."""
        try:
            value = '%s' % len(list(getattr(row, column['joinMethodName'])))
        except Exception:
            value = '0'
        return {'column': column['joinMethodName'], 'value': value}

    def object_field_for_foreign_key(self, row, column):
        """Return the foreign key value."""
        try:
            name = getattr(row, column['columnName'])
            value = getattr(name, column['labelColumn'])
            value = self.encode_label(value)
        except AttributeError:
            return {'column': column['columnName'],
                'value': 'None', 'id': '0'}
        return {'column': column['columnName'],
                'value': value, 'id': '%s' % name.id}

    def update_object(self, object_name, id, values):
        self.load_object(object_name)
        instance = self.load_instance(object_name, id)
        columns = self.object_columns(object_name)
        parameters = self.extract_parameters(columns, values)
        instance.set(**parameters)

    def remove_object(self, object_name, id):
        """Remove the object by id."""
        obj = self.load_object(object_name)
        try:
            obj.delete(id)
        except:
            msg = 'Fail to delete instance id: %s for object: %s' % (
                id, object_name)
            raise cherrypy.HTTPRedirect(turbogears.url('error', msg=msg))

    def extract_parameters(self, cols, values):
        """Loop trough the columns and extract the values from the dictionary.

        @param cols: column list
        @param values: dict of submited values

        """
        params = {}
        for col in cols:
            column_name = col['columnName']
            if column_name not in values:
                continue
            value = values[column_name]
            not_none = col['notNone']
            column_type = col['type']
            if column_type == 'SODateTimeCol':
                try:
                    value = parse_datetime('%sZ' % value.replace(' ', 'T'))
                except ValueError:
                    value  = None
            elif column_type == 'SOBoolCol':
                try:
                    value= bool(int(value))
                except ValueError:
                    if not_none:
                        value = False
                    else:
                        value = None
            elif column_type == 'SOFloatCol':
                try:
                    value = float(value)
                except ValueError:
                    if not_none:
                        value = 0.0
                    else:
                        value = None
            elif column_type == 'SOIntCol':
                try:
                    value = int(value)
                except ValueError:
                    if not_none:
                        value = 0
                    else:
                        value = None
            elif column_type in ('SODecimalCol','SOCurrencyCol'):
                value = self.extract_decimal_value(value, not_none)
            elif column_type == 'SOForeignKey':
                value = self.extract_foreign_key(value, not_none)
            else:
                if not (value or not_none):
                    value = None
            params[column_name] = values[column_name] = value
        return params

    def extract_foreign_key(self, value, not_none):
        if value == '__default_none__':
            return value
        try:
            return int(value)
        except ValueError:
            if not_none:
                return 0
            else:
                return None

    def extract_decimal_value(self, value, not_none):
        if decimal:
            try:
                return decimal.Decimal(value)
            except (TypeError, ValueError, decimal.InvalidOperation):
                if not_none:
                    return decimal.Decimal('0.0')
                else:
                    return None
        else:
            try:
                return float(value)
            except ValueError:
                if not_none:
                    return 0.0
                else:
                    return None

    def object_instances(self, object_name, start=0):
        """Return dictionary containing all instances for the requested object.

        @param object_name: name of the object
        @type object_name: string

        """
        obj = self.load_object(object_name)
        total = 0
        page_size = 10
        start = int(start)
        try:
            query = obj.select()
            total = query.count()
            results = query[start:start+page_size]
            headers, rows = self.headers_and_rows(object_name, list(results))
        except Exception, e:
            msg = 'Fail to load object instance: %s' % e
            raise cherrypy.HTTPRedirect(turbogears.url('error', msg=msg))
        return dict(objectName=object_name,
            rows=rows, headers=headers, start=start,
            page_size=page_size, total=total,
            hidden_columns=self.load_columns_visibility_state(object_name))

    def foreign_key_alternatives(self, foreign_key, column_label):
        """Return list of dictionaries containing the posible foreignKey values.

        @param foreign_key: name of the foreignKey object
        @type foreign_key: string
        @param column_label: name of the column to use as instance identifier
        @type column_label: string

        """
        obj = self.load_object(foreign_key)
        alt = []
        for x in list(obj.select()):
            label = self.encode_label(getattr(x, column_label))
            alt.append({'id': type(x.id)(x.id), 'label': label})
        return alt

    def encode_label(self, label):
        try:
            return unicode(label, 'UTF-8')
        except TypeError:
            return u'%s' % label # this is an integer (fx. an id)
        except UnicodeEncodeError:
            return u'%s' % label

    def headers_and_rows(self, objectName, rows):
        """Return a tuple containing a list of rows and header labels.

        @param objectName: name of the object
        @type objectName: string
        @param rows: list of intances

        """
        cols = self.object_columns(objectName)
        labels = [{'column': col['columnName'],
            'label': (col['title'] or col['columnName'])} for col in cols]
        labels.insert(0, {'column': 'id', 'label': 'ID'})
        values = []
        for row in rows:
            tmp = []
            tmp.append(self.object_field(row, {'columnName': 'id'}))
            for col in cols:
                col['objectName'] = objectName
                tmp.append(self.object_field(row, col))
            values.append(list(tmp))
        return labels, values

    def object_joins(self, objectName, id, join, joinType, joinObjectName=''):
        """Collect the joined instances into a dictionary.

        @param objectName: name of the object
        @type objectName: string
        @param id: id of the instance
        @type id: string
        @param join: name of the join (joinMethodName in SQLObject parlance)
        @type join: string
        @param joinType: name of join type
        @type joinType: string
        @param joinObjectName: otherClassName (in SQLObject parlance)
        @type joinObjectName: string

        """
        hostObject = objectName
        obj = self.load_object(objectName)
        try:
            rows = list(getattr(obj.get(id), join))
        except:
            msg = 'Error, joins objectName: %s, id: %s, join: %s' % (
                objectName, id, join)
            raise cherrypy.HTTPRedirect(turbogears.url('error', msg=msg))

        view = '%s_%s' % (hostObject, joinObjectName)
        hidden_columns = self.load_columns_visibility_state(view)

        joinsDict = dict(objectName=objectName, rows=[], headers=[],
            join=join, id=id, joinType=joinType, joinObjectName=joinObjectName,
            hostObject=hostObject, hidden_columns=hidden_columns)
        if not rows:
            return joinsDict

        c = '%s' % rows[0].sqlmeta.soClass
        objectName = c.split('.')[-1].replace("'>", '')
        headers, rows = self.headers_and_rows(objectName, rows)
        joinsDict['objectName'] = objectName
        joinsDict['rows'] = rows
        joinsDict['headers'] = headers
        return joinsDict

    def object_representation(self, obj):
        """Utility method that returns a stripped object representation."""
        return str(obj).replace('<', '').replace('>', '')

    def get_column_type(self, column):
        """Given a column representation return the column type."""
        column_type = '%r' % column
        return column_type.split()[0][1:].split('.')[-1]

    def column_title(self, column):
        if isinstance(column, sqlobject.col.SOForeignKey):
            return column.name.replace('ID', '')
        try:
            title = getattr(column,'title') or ''
        except AttributeError:
            title = ''
        return title

    def column_default(self, column, column_type):
        try:
            default = column.default
        except AttributeError:
            return ''
        if default == sqlobject.sqlbuilder.NoDefault:
            return ''
        if column_type in ('SOIntCol', 'SOFloatCol', 'SOStringCol',
                'SODecimalCol', 'SOCurrencyCol', 'SOBoolCol'):
            return default
        elif column_type == 'SODateTimeCol':
            d = '%s' % default
            return ':'.join(d.split(':')[:-1])
        elif column_type == 'SODateCol':
            d = '%s' % default
            return d.split()[0]
        return ''

    def column_not_none(self, column):
        try:
            return column.notNone
        except AttributeError:
            return False

    def get_column_properties(self, column_name, column):
        """Return a dictionary containing the column properties.

        Depending on the column type the properties returned could be:
        type, title, join (otherClassName), joinMethodName,
        length, varchar,labelColumn,opetions

        @param column_name: name of the column
        @type column_name: string
        @param column: column instance

        """
        props = {'type': self.get_column_type(column),
            'columnName': column_name}
        props['title'] = self.column_title(column)
        props['default'] = self.column_default(column, props['type'])
        props['notNone'] = self.column_not_none(column)
        if props['type'] == 'SOEnumCol':
            props['options'] = column.enumValues
        if props['type'] in ('SOMultipleJoin', 'SOSQLMultipleJoin',
          'SORelatedJoin', 'SOSQLRelatedJoin'):
            props['join'] = column.otherClassName
            props['joinMethodName'] = column.joinMethodName
        if props['type'] == 'SOSingleJoin':
            props['join'] = column.otherClassName
            props['joinMethodName'] = column.joinMethodName
            props['labelColumn'] = self.load_label_column_for_object(
                column.otherClassName)
            props['options'] = self.foreign_key_alternatives(
                column.otherClassName, props['labelColumn'])
        props['objectName'] = column.soClass.__name__
        if props['type'] in ['SOStringCol', 'SOUnicodeCol']:
            props = self.get_string_properties(column, props)
        if props['type'] == 'SOForeignKey':
            props = self.get_foreign_key_properties(column, props)
        return props

    def get_string_properties(self, column, properties):
        """Extract the SOStringCol properties from the column object."""
        properties['length'] = column.length
        properties['varchar'] = column.varchar
        return properties

    def get_foreign_key_properties(self, column, properties):
        """Extract the foreignKey properties from the column object."""
        properties['join'] = column.foreignKey
        properties['columnName'] = column.foreignName
        properties['labelColumn'] = self.load_label_column_for_object(
            column.foreignKey)
        properties['options'] = self.foreign_key_alternatives(
            column.foreignKey, properties['labelColumn'])
        if not column.notNone:
            properties['options'].insert(0,
                {'id': '__default_none__', 'label': 'None'})
        return properties

    def object_columns(self, object_name):
        """Return list of columns properties arranged in dicts.

        @param object_name: name of the object
        @type object_name: string

        """
        obj = self.load_object(object_name)
        cols = self.get_columns_for_object(obj)
        return self.order_columns(object_name, cols)

    def get_columns_for_object(self, obj):
        """Return list of columns properties arranged in dicts.

        @param object: model instance

        """
        cols = []
        # get normal columns
        for column_name in obj.sqlmeta.columns:
            column = obj.sqlmeta.columns[column_name]
            if obj._inheritable and column_name == 'childName':
                continue
            cols.append(self.get_column_properties(column_name, column))
        # get join columns
        for column in obj.sqlmeta.joins:
            cols.append(self.get_column_properties(
                column.joinMethodName, column))
        # get inherited columns
        if obj._inheritable and not self.is_inheritable_base_class(obj):
            inherited_columns = self.get_inherited_columns(obj)
            if inherited_columns:
                cols.extend(inherited_columns)
        return cols

    def get_inherited_columns(self, obj):
        """Return the columns inherited from the parent class"""
        return self.get_columns_for_object(obj._parentClass)

    def is_inheritable_base_class(self, obj):
        """Check if the object is  a direct subclass of InheritableSQLObject"""
        return 'sqlobject.inheritance.InheritableSQLObject' in str(obj.__bases__)

    ## configuration state ##

    def state_path(self):
        """Return the path to the catwalk session pickle.

        Create a session directory if nescesary.

        """
        catwalk_session_dir = os.path.join(turbogears.util.get_package_name()
            or '', 'catwalk-session')
        catwalk_session_dir = os.path.abspath(catwalk_session_dir)
        if not os.path.exists(catwalk_session_dir):
            try:
                os.mkdir(catwalk_session_dir)
            except IOError, e:
                msg = 'Fail to create session directory %s' % e
                raise cherrypy.HTTPRedirect(turbogears.url('error', msg=msg))
        return os.path.join(catwalk_session_dir, 'session.pkl')

    def load_state(self):
        """Retrieve the pickled state from disc."""
        if not os.path.exists(self.state_path()):
            return {}
        try:
            return pickle.load(open(self.state_path(),'rb'))
        except pickle.PicklingError, e:
            msg = 'Fail to load pickled session file %s' % e
            raise cherrypy.HTTPRedirect(turbogears.url('error', msg=msg))

    def save_state(self, state):
        """Pickle the state."""
        try:
            pickle.dump(state, open(self.state_path(), 'wb'), True)
        except pickle.PicklingError, e:
            msg = 'Fail to store pickled session file %s' % e
            raise cherrypy.HTTPRedirect(turbogears.url('error', msg=msg))

    def hide_columns(self, view, columns=''):
        state = self.load_state()
        hidden_columns = state.get('hidden_columns', {})
        hidden_columns[view] = columns.split('|')
        state['hidden_columns'] = hidden_columns
        self.save_state(state)

    def toggle_columns_visibility_state(self, view, columns):
        """Toggle the columns visibility and store the new state.

        @param view: name of the grid view to be stored
        @type view: string
        @param columns: name of the columns to be hidden or shown
        @type column: bar separated string

        """
        state = self.load_state()
        hidden_columns = state.get('hidden_columns', {})
        if not columns:
            hidden_columns[view] = []
            hidden_columns_list = []
        else:
            hidden_columns_list = hidden_columns.get(view, [])
            columns = columns.split('|')
            for column in columns:

                if column in hidden_columns_list:
                    hidden_columns_list = [x for x in hidden_columns_list
                      if x != column]
                else:
                    hidden_columns_list.append(column)

        hidden_columns[view] = hidden_columns_list
        state['hidden_columns'] = hidden_columns
        self.save_state(state)

    def load_columns_visibility_state(self, view):
        """Return a list of hidden columns names for the requested view.

        @param view: name of the grid view to be stored
        @type view: string

        """
        state = self.load_state()
        hidden_columns = state.get('hidden_columns', {})
        return hidden_columns.get(view, [])

    def load_label_column_for_object(self, objectName):
        """Get the column name (foreignKey label) for an object.


        @param objectName: name of the object
        @type objectName: string

        """
        state = self.load_state()
        lables = state.get('columns', {})
        return lables.get(objectName, 'id')

    def column_label_for_object(self, objectName, columnName):
        """Store the column name (foreignKey label) for an object.

        @param objectName: name of the object
        @type objectName: string
        @param columnName: name of the column to use as foreignKey label
        @type columnName: string

        """
        state = self.load_state()
        cl = state.get('columns', {})
        cl[objectName] = columnName
        state['columns'] = cl
        self.save_state(state)

    def load_column_order(self, object_name):
        """Get the column order.

        If the user has rearrenged the columns order for an object,
        this will return the prefered order as list.

        @param object_name: name of the object
        @type object_name: string

        """
        state = self.load_state()
        cols = state.get('order', {})
        return cols.get(object_name, [])

    def save_column_order(self, object_name, columns_bsv):
        """Save the prefered order of the object's columns.

        @param object_name: name of the object
        @type object_name: string
        @param columns_bsv: bar (|) delimited columns names
           @type columns_bsv: string

        """
        state = self.load_state()
        cl = state.get('order', {})
        cl[object_name] = columns_bsv.split('|')
        state['order'] = cl
        self.save_state(state)

    def order_columns(self, object_name, cols):
        """Return a rearrenged list of columns as configured by the user.

        @param object_name: name of the object
        @type object_name: string
        @param cols: original list of columns following the default table order
        @type cols: list

        """
        order = self.load_column_order(object_name)
        if not order:
            return cols
        c = {}
        for col in cols:
            c[col['columnName']] = col
            if col['columnName'] not in order:
                order.append(col['columnName'])
        rearrenged = []
        for columnName in order:
            if columnName not in c.keys():
                continue
            rearrenged.append(c[columnName])
        return rearrenged

    def save_model_order(self, models):
        """Store the new order of the listed models."""
        state = self.load_state()
        state['model_order'] = models.split('|')
        self.save_state(state)

    def load_models_order(self):
        state = self.load_state()
        return state.get('model_order', [])

    def order_models(self, models):
        ordered = self.load_models_order()
        if not ordered:
            return models
        #add any new models to the ordered list
        for model in models:
            if not model in ordered:
                ordered.append(model)
        reorderedList = []
        #check that the ordered list don't have delete models
        for model in ordered:
            if model in models:
                reorderedList.append(model)
        return reorderedList

    ## exposed methods ##

    [expose(format="json")]
    def add(self, _csrf_token=None, **v):
        """Create a new instance of an object.

        @param v: dictionary of submited values

        """
        objectName = v['objectName']
        obj = self.load_object(objectName)
        cols = self.object_columns(objectName)
        params = self.extract_parameters(cols, v)
        if not params:
            return self.instances(objectName)
        try:
            new_object = obj(**params)
        except Exception, e:
            cherrypy.response.status = 500
            return dict(error=str(e))
        if not new_object:
            return self.instances(objectName)
        returnlist = self.object_instance(objectName,'%s' % new_object.id)
        returnlist["msg"] = "A new instance of %s was created" % objectName
        return returnlist

    [expose(format="json")]
    def update(self, _csrf_token=None, **values):
        """Update the objects properties.

        @param values: dictionary of key and values, as a bare minimum
                  the name of the object (objectName) and the id

        """
        object_name = values.get('objectName', '')
        id = values.get('id', '')
        try:
            self.update_object(object_name, id, values)
        except Exception, e:
            cherrypy.response.status = 500
            return dict(error=str(e))
        returnlist = self.object_instances(object_name)
        returnlist["msg"] = "The object was successfully updated"
        return returnlist

    [expose(format="json")]
    def remove(self, objectName, id, _csrf_token=None):
        """Remove and instance by id.

        This doesn't handle references (cascade delete).

        @param objectName: name of the object
        @type objectName: string
        @param id: id of the instance to be removed
        @type id: string

        """
        try:
            self.remove_object(objectName, id)
        except Exception, e:
            cherrypy.response.status = 500
            return dict(error=str(e))
        returnlist = self.object_instances(objectName)
        returnlist["msg"] = "The object was successfully deleted"
        return returnlist

    [expose(format="json")]
    def remove_single_join(self, object_name, id,
            join_object_name, join_object_id, _csrf_token=None):
        """Remove a single join instance by id.

        This doesn't handle references (cascade delete).

        @param object_name: name of the host object
        @type object_name: string
        @param id: id of the host instance
        @type id: string
        @param join_object_name: name of the join object
        @type join_object_name: string
        @param join_object_id: id of the join instance to be removed
        @type join_object_id: string

        """
        self.remove_object(join_object_name, join_object_id)
        return self.object_instance(object_name, id)

    [expose(format="json")]
    def saveModelOrder(self, models, _csrf_token=None):
        """Save the prefered order of the listed models."""
        self.save_model_order(models)
        return '' #return dummy string, else json will barf

    [expose(format="json")]
    def columnOrder(self, objectName, cols, _csrf_token=None):
        """Save the prefered order of the object's columns.

        @param objectName: name of the object
        @type objectName: string
        @param cols: columns names separated by '|'
        @type cols: string

        """
        self.save_column_order(objectName, cols)
        """return dummy string, else json will barf"""
        return ''

    [expose(format="json")]
    def instances(self, objectName, start=0, _csrf_token=None):
        """Get object instances.

        Returns a JSON structure containing all instances of the
        requested object.

        @param objectName: name of the object
        @type objectName: string

        """
        return self.object_instances(objectName, start)

    [expose(format="json")]
    def manageRelatedJoins(self, objectName, id,
            join, relatedObjectName, _csrf_token=None, **vargs):
        """Get related joins.

        Returns a JSON structure whith a list of related joins for
        the requested object, and a list of all joins.

        @param objectName: name of the object
        @type objectName: string
        @param id: id of the instance
        @type id: string
        @param join: name of the join (joinMethodName in SQLObject parlance)
        @type join: string
        @param relatedObjectName: otherClassName (in SQLObject parlance)
        @type relatedObjectName: string

        """
        joins = self.object_joins(objectName, id,
            join, 'SORelatedJoin', relatedObjectName)
        joins['allJoins'] = self.object_instances(relatedObjectName)
        return joins

    [expose(format="json")]
    def updateJoins(self, objectName, id,
            join, joinType, joinObjectName, joins, _csrf_token=None):
        """Update joins.

        Drop all related joins first, then loop trought the submited joins
        and set the relation.

        @param objectName: name of the object
        @type objectName: string
        @param id: id of the instance to be removed
        @type id: string
        @param join: name of the join field (joinMethodName)
        @type join: string
        @param joinType: type of the join (Multiple or Related)
        @type joinType: string
        @param joinObjectName: name of the joined object (otherClassName)
        @type joinObjectName: string
        @param joins: coma delimited string of join instances id's
        @type joins: string

        """
        try:
            obj = self.load_object(objectName)
            inst = obj.get(id)

            # get the add/remove method names
            j = [j for j in obj.sqlmeta.joins if (j.joinMethodName == join)][0]
            remove_method = getattr(inst, 'remove' +  j.addRemoveName)
            add_method = getattr(inst, 'add' + j.addRemoveName)

            # remove all joined instances
            for joined_instance in list(getattr(inst, join)):
                remove_method(joined_instance)

            # add the new joined instances
            join_object = self.load_object(joinObjectName)
            joins = joins.split(',')
            for i in joins:
                try:
                    i = int(i)
                except ValueError:
                    continue
                instance = join_object.get(i)
                add_method(instance)
        except Exception, e:
            cherrypy.response.status = 500
            return dict(error=str(e))
        returnlist = self.object_instance(objectName, id)
        returnlist["msg"] = "The object was successfully updated"
        return returnlist

    [expose(format="json")]
    def updateColumns(self, objectName, column, _csrf_token=None):
        """Update a column.

        Toggle (and store) the state of the requested column
        in grid view display.

        @param objectName: name of the object
        @type objectName: string
        @param column: name of the column to be hidden
        @type column: string


        """
        self.toggle_columns_visibility_state(objectName, column)
        return self.object_instances(objectName)

    [expose(format="json")]
    def updateColumnsJoinView(self, objectName, id,
            join, joinType, joinObjectName, column, _csrf_token=None):
        """Update column in join view.

        Toggle (and store) the state of the requested column
        in grid view display for a join view.

        @param objectName: name of the object
        @type objectName: string
        @param id: id of the 'parent' instance
        @type id: string
        @param join: name of the join (joinMethodName in SQLObject parlance)
        @type join: string
        @param joinType: name of join type
        @type joinType: string
        @param joinObjectName: otherClassName (in SQLObject parlance)
        @type joinObjectName: string
        @param column: name of the column to be hidden or shown
        @type column: string

        """
        self.toggle_columns_visibility_state('%s_%s' % (
            objectName, joinObjectName), column)
        return self.object_joins(objectName, id,
            join, joinType, joinObjectName)

    [expose(format="json")]
    def joins(self, objectName, id, join, joinType, joinObjectName, _csrf_token=None):
        """Get joins.

        Return a JSON structure containing a list joins for
        the requested object's joinMethodName.

        @param objectName: name of the object
        @type objectName: string
        @param id: id of the instance
        @type id: string
        @param join: name of the join (joinMethodName in SQLObject parlance)
        @type join: string
        @param joinType: name of join type
        @type joinType: string
        @param joinObjectName: otherClassName (in SQLObject parlance)
        @type joinObjectName: string

        """
        return self.object_joins(objectName, id, join, joinType, joinObjectName)

    def object_instance(self, object_name, id):
        obj = self.load_object(object_name)
        inst = obj.get(id)
        cols = self.object_columns(object_name)
        values = []
        for col in cols:
            colForID = col.copy()
            colForID['type'] = ''
            col['object_id'] = id
            if col['type'] in ('SOMultipleJoin', 'SOSQLMultipleJoin',
                    'SORelatedJoin', 'SOSQLRelatedJoin'):
                col['id'] = id
                try:
                    value = '%s' % len(list(getattr(inst, col['columnName'])))
                except Exception:
                    value = '0'
                col['value'] = {'value': value, 'column': col['columnName']}
            elif col['type'] in ('SOForeignKey', 'SOSingleJoin'):
                try:
                    otherClass = getattr(inst, col['columnName'])
                    col['id'] = self.object_field(inst, colForID)
                    col['id']['value'] = '%s' % otherClass.id
                    try:
                        label_value = '%s' % getattr(
                            otherClass, col['labelColumn'])
                    except AttributeError:
                        label_value = self.object_representation(otherClass)
                    label_value = self.encode_label(label_value)
                    col['value'] = {'column': col['columnName'],
                        'value': label_value}
                except AttributeError:
                    col['id'] = '__default_none__'
                    col['value'] = {'column': col['columnName'],
                        'value': 'None', 'id':'__default_none__'}
            else:
                col['id'] = self.object_field(inst, colForID)
                col['value'] = self.object_field(inst, col)
            col['objectName'] = object_name
            values.append(col)
        return dict(objectName=object_name, id=id, values=values)

    [expose(format="json")]
    def instance(self, objectName, id, _csrf_token=None):
        """Get object instance.

        Return a JSON structure containing the columns and field values for
        the requested object

        @param objectName: name of the object
        @type objectName: string
        @param id: id of the instance
        @type id: string

        """
        return self.object_instance(objectName, id)

    [expose(format="json")]
    def columnsForLabel(self, objectName, foreignObjectName, foreignKeyName, _csrf_token=None):
        """Get columns for label.

        Return a JSON structure with a list of columns to use
        as foreignKey label.

        @param objectName: name of the object
        @type objectName: string
        @param foreignObjectName: name of the object the foreignKey refers to
        @type foreignObjectName: string
        @param foreignKeyName: name of the object foreignKey field
        @type foreignKeyName: string

        """
        cols = [{'columnName': col['columnName'], 'title': col['title']}
            for col in self.object_columns(foreignObjectName)
                if col['type'] !='SOMultipleJoin']
        return dict(columns=cols, foreignKeyName=foreignKeyName,
            foreignKeyColumnForLabel=self.load_label_column_for_object(
                foreignObjectName), foreignObjectName=foreignObjectName,
            objectName=objectName)

    [expose(format="json")]
    def setColumnForLabel(self, objectName, foreignObjectName,
            foreignKeyName, columnName, _csrf_token=None):
        """Set columns for label.

        Exposed method that let you store the column name to be used as
        foreignKey label for the requested object.

        @param objectName: name of the object
        @type objectName: string
        @param foreignObjectName: name of the object the foreignKey refers to
        @type foreignObjectName: string
        @param foreignKeyName: name of the object foreignKey field
        @type foreignKeyName: string
        @param columnName: name of the column to use as foreignKey label
        @type columnName: string

        """
        self.column_label_for_object(foreignObjectName, columnName)
        return self.columns(objectName)

    [expose(format="json")]
    def columns(self, objectName, _csrf_token=None, **kv):
        """Return JSON structure containing a list of column properties.

        @param objectName: name of the object
        @type objectName: string

        """
        reorder = 'foreignObjectName' not in kv
        return dict(objectName=objectName,
            columns=self.object_columns(objectName),
            reorder=reorder, reordering=kv)

    def models(self):
        objs = []
        for m in dir(self.model):
            if m in ('SQLObject', 'InheritableSQLObject'):
                continue
            c = getattr(self.model, m)
            if isinstance(c, type) and issubclass(c, sqlobject.SQLObject):
                objs.append(m)
        return self.order_models(objs)

    [expose(format="json")]
    def list(self, _csrf_token=None):
        """Return JSON structure containing a list of available objects."""
        return dict(SQLObjects=self.models())

    [expose(template='mirrormanager.catwalk.catwalk')]
    def index(self, _csrf_token=None):
        """Main CatWalk page.

        Import the proper client side libraries and set up the placeholder
        for the dynamic elements.

        """
        return dict(models=self.models(), _csrf_token=_csrf_token)
