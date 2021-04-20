from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms.validators import DataRequired

class Prontuario (FlaskForm):
	cabecalho  = StringField("cabecalho", validators=[DataRequired()])
	subjective = TextAreaField("subjective", validators=[DataRequired()])
	objective  = TextAreaField("objective", validators=[DataRequired()])
	assessment = TextAreaField("assessment", validators=[DataRequired()])
	plan       = TextAreaField("plan", validators=[DataRequired()])
	file	   = FileField("file",validators=[DataRequired()])

