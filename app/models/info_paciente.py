from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class InfoPaciente (FlaskForm):
	idP =  StringField("idP", validators=[DataRequired()])
