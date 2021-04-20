from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class InfoInstituicao (FlaskForm):
	id =  StringField("id", validators=[DataRequired()])
