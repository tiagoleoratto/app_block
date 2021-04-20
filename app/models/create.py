from flask_wtf import FlaskForm
from wtforms import StringField,

class Create (FlaskForm):
	id =  StringField("id")
	nome = StringField("nome")

