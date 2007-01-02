from formencode import Invalid, schema
from formencode.validators import URL,String, Email, FieldsMatch

class URLWithArchValidator(URL):
    messages = {"no_arch":"No $ARCH variable in url"}
    
    def validate_python(self, value, state):
        if "$ARCH" not in value:
            raise Invalid(self.message("no_arch", state), value, state)


class RegisterSchema(schema.Schema):
    filter_extra_fields = True
    allow_extra_fields = True    
    
    username = String(not_empty=True)
    password1 = String(not_empty=True)
    password2 = String(not_empty=True)
    display_name = String()
    email_address = Email()
    
    chained_validators = [FieldsMatch("password1", "password2")]
    
    
    