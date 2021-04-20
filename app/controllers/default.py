from flask import render_template
from app import app
from flask import send_from_directory, request, url_for
from io import BytesIO
from werkzeug.utils import secure_filename

from app.models.paciente import Paciente
from app.models.instituicao import Instituicao
from app.models.info_instituicao import InfoInstituicao
from app.models.info_paciente import InfoPaciente
from app.models.prontuario import Prontuario
from app.models.pedechave import PedeChave

from app.controllers.bdb_paciente import Paciente_bdb	
from app.controllers.bdb_instituicao import Instituicao_bdb
from app.controllers.bdb_prontuario import Prontuario_bdb

from Crypto.PublicKey import RSA
from os import walk

import shutil
import json 

import zipfile

@app.route("/", methods=["GET", "POST"])
def first():
	return render_template("first.html")
	

@app.route("/first", methods=["GET", "POST"])
def diferencia():
	if request.method == 'POST':
		if 'paciente' in request.form:
			return render_template("index_p.html")
		if 'instituicao' in request.form:
			instituicao = Instituicao()
			return render_template("index_i.html")


@app.route("/index", methods=["GET", "POST"])
def index():
	if request.method == 'POST':
		if 'paciente' in request.form:
			paciente = Paciente()
			return render_template("paciente.html", paciente=paciente)
		if 'instituicao' in request.form:
			instituicao = Instituicao()
			return render_template("instituicao.html", instituicao=instituicao)
		if 'prontuario' in request.form:
			info_instituicao = InfoInstituicao()
			return render_template("info_instituicao.html", info_instituicao=info_instituicao)
		if 'listar' in request.form:
			info_instituicao = InfoInstituicao()
			return render_template("info_instituicao_l.html", info_instituicao=info_instituicao)
		if 'acesso' in request.form:
			info_instituicao = InfoInstituicao()
			return render_template("info_instituicao_a.html", info_instituicao=info_instituicao)
	
	return render_template("index.html")

@app.route("/buscar_prontuario/<string:id>/<string:chave>", methods=["GET", "POST"])
def buscar_prontuario(id, chave):
	pedechave = PedeChave()
	if pedechave.validate_on_submit():
		file = request.files['file']
		
		if arquivo_permitido(file.filename):
			filename = secure_filename(file.filename)
			file.save('./app/static/' + file.filename)
			
			#request.form.get('chaveI'), chaveI_rsa=request.form.get('chaveI_rsa'))	
			
			priv_rsa, priv_bdb = descompacta_chave('./app/static/', file.filename,chave)
			
			prontuario = Prontuario_bdb()
			prontuario.buscar(id, priv_rsa, chave)
			
			if prontuario.html:
				retorno = json.loads(prontuario.html)
				return render_template("mostra_prontuario.html", id=id, prontuario=retorno)
			else:
				return render_template("error.html",msg='Sem permissão')
		
	return render_template("pedechave.html", pedechave=pedechave, id=id, chave=chave)

@app.route("/buscar_paciente_l", methods=["GET", "POST"])
def buscar_paciente_l():
	info_paciente = InfoPaciente()
	if info_paciente.idP.data:
		umPaciente = Paciente_bdb()
		umPaciente.buscar(info_paciente.idP.data)
		if umPaciente.asset_id:
			prontuario = Prontuario()
			return render_template("prontuario.html",prontuario=prontuario,chaveP=umPaciente.bdb,chaveP_rsa=umPaciente.rsa, chaveI=request.form.get('chaveI'), chaveI_rsa=request.form.get('chaveI_rsa') )	
		else:
			return render_template("error.html", msg='Paciente não encontrada')
				
	return render_template("info_paciente_l.html", info_paciente=info_paciente)

@app.route("/buscar_instituicao_l", methods=["GET", "POST"])
def buscar_instituicao_l():
	info_instituicao = InfoInstituicao()
	if info_instituicao.id.data:
		umInstituicao = Instituicao_bdb()
		umInstituicao.buscar(info_instituicao.id.data)
		if umInstituicao.asset_id:
			info_paciente = InfoPaciente()
			return render_template("info_paciente_l.html",info_paciente=info_paciente, chaveI=umInstituicao.bdb, chaveI_rsa=umInstituicao.rsa)	
		else:
			return render_template("error.html", msg='Instituição não encontrada')
				
	return render_template("info_instituicao_l.html", info_instituicao=info_instituicao)
#----------------------------------------------------------------------------
@app.route("/buscar_instituicao_a", methods=["GET", "POST"])
def buscar_instituicao_a():
	info_instituicao = InfoInstituicao()
	if info_instituicao.id.data:
		umInstituicao = Instituicao_bdb()
		umInstituicao.buscar(info_instituicao.id.data)
		if umInstituicao.asset_id:
			info_paciente = InfoPaciente()
			return render_template("info_paciente_a.html",info_paciente=info_paciente, idI=umInstituicao.id)	
		else:
			return render_template("error.html", msg='Instituição não encontrada')
				
	return render_template("info_instituicao_a.html", info_instituicao=info_instituicao)
	
@app.route("/acesso_prontuario", methods=["GET", "POST"])
def acesso_prontuario():
	info_paciente = InfoPaciente()
	if info_paciente.idP.data:
		umPaciente = Paciente_bdb()
		umPaciente.buscar(info_paciente.idP.data)
		if umPaciente.asset_id:
			prontuario = Prontuario_bdb()
			prontuario.listar(info_paciente.idP.data)
			
			return render_template("listar_acesso.html", prontuario=prontuario, chaveI=request.form.get('chaveI'), chaveI_rsa=request.form.get('chaveI_rsa'), chaveP=umPaciente.bdb, idI=request.form.get('idI'))	
		else:
			return render_template("error.html", msg='Paciente não encontrada')
				
	return render_template("info_paciente_a.html", info_paciente=info_paciente)
	
@app.route("/dar_acesso/<string:id>/<string:chave>/<string:idI>", methods=["GET", "POST"])
def dar_acesso(id, chave, idI):
	pedechave = PedeChave()
	if pedechave.validate_on_submit():
		file = request.files['file']
		
		if arquivo_permitido(file.filename):
			filename = secure_filename(file.filename)
			file.save('./app/static/' + file.filename)
			
			#request.form.get('chaveI'), chaveI_rsa=request.form.get('chaveI_rsa'))	
			priv_rsa, priv_bdb = descompacta_chave('./app/static/', file.filename, chave)
			
			prontuario = Prontuario_bdb()
			
			prontuario.acesso(id, chave, idI, priv_bdb, priv_rsa)
			
			if prontuario.txid:
				return render_template("sucesso_no_msg.html", msg=prontuario.txid)
			else:
				return render_template("error.html",msg='Sem permissão')
		
	return render_template("pedechave_a.html", pedechave=pedechave, id=id, chave=chave, idI=idI)
#----------------------------------------------------------------------------

@app.route("/buscar_instituicao", methods=["GET", "POST"])
def buscar_instituicao():
	info_instituicao = InfoInstituicao()
	if info_instituicao.id.data:
		umInstituicao = Instituicao_bdb()
		umInstituicao.buscar(info_instituicao.id.data)
		if umInstituicao.asset_id:
			info_paciente = InfoPaciente()
			return render_template("info_paciente.html",info_paciente=info_paciente, chaveI=umInstituicao.bdb, chaveI_rsa=umInstituicao.rsa)	
		else:
			return render_template("error.html", msg='Instituição não encontrada')
				
	return render_template("info_instituicao.html", info_instituicao=info_instituicao)

@app.route("/listar_prontuario", methods=["GET", "POST"])
def listar_prontuario():
	info_paciente = InfoPaciente()
	if info_paciente.idP.data:
		umPaciente = Paciente_bdb()
		umPaciente.buscar(info_paciente.idP.data)
		if umPaciente.asset_id:
			prontuario = Prontuario_bdb()
			prontuario.listar(info_paciente.idP.data)
			
			return render_template("listar.html", prontuario=prontuario, chaveI=request.form.get('chaveI'), chaveI_rsa=request.form.get('chaveI_rsa'))	
		else:
			return render_template("error.html", msg='Paciente não encontrada')
				
	return render_template("info_paciente_l.html", info_paciente=info_paciente)
	
@app.route("/buscar_paciente", methods=["GET", "POST"])
def buscar_paciente():
	info_paciente = InfoPaciente()
	if info_paciente.idP.data:
		umPaciente = Paciente_bdb()
		umPaciente.buscar(info_paciente.idP.data)
		if umPaciente.asset_id:
			prontuario = Prontuario()
			return render_template("prontuario.html",prontuario=prontuario,chaveP=umPaciente.bdb,chaveP_rsa=umPaciente.rsa, chaveI=request.form.get('chaveI'), chaveI_rsa=request.form.get('chaveI_rsa') )	
		else:
			return render_template("error.html", msg='Paciente não encontrada')
				
	return render_template("info_paciente.html", info_paciente=info_paciente)
	
@app.route("/download/<path:filename>", methods=["GET", "POST"])
def download(filename):
	print(filename)
	return send_from_directory('./app/static/', filename=filename, as_attachment=False)
	
@app.route("/paciente", methods=["GET", "POST"])
def paciente():
	paciente = Paciente()
	if paciente.validate_on_submit():
		umPaciente = Paciente_bdb()
		umPaciente.criar(paciente.id.data, paciente.nome.data)
		if umPaciente.tx_id:
			arquivo = "chaves_" + str(paciente.id.data) + ".zip"
			return render_template("sucesso.html",link=arquivo, tx_id=umPaciente.tx_id)
		else:
			return render_template("error.html")		
		
	return render_template("paciente.html", paciente=paciente)

@app.route("/prontuario", methods=["GET", "POST"])
def prontuario():
	prontuario = Prontuario()
	if prontuario.validate_on_submit():
		
		file = request.files['file']
			
		if arquivo_permitido(file.filename):
			filename = secure_filename(file.filename)
			file.save('./app/static/' + file.filename)
			
			priv_rsa, priv_bdb = descompacta_chave('./app/static/', file.filename, request.form.get('chaveI'))
			
				
			umProntuario = Prontuario_bdb()
			umProntuario.criar(prontuario.cabecalho.data, prontuario.subjective.data,prontuario.objective.data,prontuario.assessment.data,prontuario.plan.data, request.form.get('chaveI'),request.form.get('chaveP'),request.form.get('chaveI_rsa'),request.form.get('chaveP_rsa'), prontuario.file.data, priv_rsa, priv_bdb)
			
			if umProntuario.txid_acesso and umProntuario.txid_transf:
				return render_template("sucesso_no_msg.html",msg='Prontuario:'+umProntuario.txid_transf + ' Acesso:'+umProntuario.txid_acesso )
			else:
				return render_template("error.html")
		else:
			return render_template("error.html",msg='Arquivo invalido. Deve ser .zip')
			
	return render_template("prontuario.html", prontuario=prontuario)
	
@app.route("/instituicao", methods=["GET", "POST"])
def instituicao():
	instituicao = Instituicao()
	if instituicao.validate_on_submit():
		umInstituicao = Instituicao_bdb()
		umInstituicao.criar(instituicao.id.data, instituicao.nome.data)
		if umInstituicao.tx_id:
			arquivo = "chaves_" + str(instituicao.id.data) + ".zip"
			return render_template("sucesso.html",link=arquivo, tx_id=umInstituicao.tx_id)
		else:
			return render_template("error.html")
		
	return render_template("instituicao.html", instituicao=instituicao)	
	
def arquivo_permitido(filename):
	return '.'in filename and filename.rsplit('.',1)[1].lower() == 'zip'
	
def descompacta_chave(dir, filename, chave):
	#shutil.rmtree(dir+filename)
	arq_zip = zipfile.ZipFile(dir+filename)
	arq_zip.extractall(dir+chave)
	priv_RSA = None
	priv_BDB = None
	for(dirpath, dirnames, filenames) in walk(dir+chave):
		for file in filenames: 
			if 'RSA' in file:
				#priv_RSA = RSA.import_key(open(dirpath+'/'+file).read())
				priv_RSA = open(dirpath+'/'+file).read()
			else:
				priv_BDB = open(dirpath+'/'+file).read()
			
	shutil.rmtree(dir+chave)
	return priv_RSA, priv_BDB
		
		
		
		
		
		
		


