from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class Instituicao (FlaskForm):
	id =  StringField("id", validators=[DataRequired()])
	nome = StringField("nome", validators=[DataRequired()])

