from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, FileField
from wtforms.validators import DataRequired, URL, NumberRange, Optional
from .models import Brand

class AddFirmwareForm(FlaskForm):
    brand = SelectField('Brand', coerce=int, validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    version = StringField('Version', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    gmail_link = StringField('Gmail Drive Link', validators=[
        DataRequired(),
        URL(message="Please enter a valid URL")
    ])
    icon = FileField('Icon', validators=[Optional()])
    price = DecimalField('Price', validators=[
        DataRequired(),
        NumberRange(min=0, message="Price must be greater than or equal to 0")
    ])
    
    def __init__(self, *args, **kwargs):
        super(AddFirmwareForm, self).__init__(*args, **kwargs)
        # Populate brand choices
        self.brand.choices = [
            (brand.id, brand.name) 
            for brand in Brand.query.order_by(Brand.name).all()
        ]
