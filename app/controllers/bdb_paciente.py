from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from time import sleep
from sys import exit
import json
from pymongo import MongoClient

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256

import zipfile
import os

class Paciente_bdb:	

	#atributos
	id = ""
	nome = ""
	
	def __init__(self):	
		pass
		
	def criar(self, id, nome):		
		bdb_root_url = 'http://localhost:9984/'  # Use YOUR BigchainDB Root URL here

		bdb = BigchainDB(bdb_root_url)

		patient = generate_keypair()

		#-----------chaves do paciente-----------------------------
		key = RSA.generate(1024)
		private_key = key.export_key()
		
		arquivo_RSA = "./app/static/" + str(id) + "_RSA.pem"		
		file_out = open(arquivo_RSA, "wb")
		file_out.write(private_key)
		file_out.close()
		
		arquivo_BDB = "./app/static/" + str(id) + "_BDB.pem"
		file_out = open(arquivo_BDB, "w")
		file_out.write(patient.private_key)
		file_out.close()
		#---------------------------------------------------------------------
		arquivo_zip = zipfile.ZipFile("./app/static/chaves_" + str(id) + ".zip","w")
		arquivo_zip.write(arquivo_RSA, str(id) + "_RSA.pem", compress_type=zipfile.ZIP_DEFLATED)
		arquivo_zip.write(arquivo_BDB, str(id) + "_BDB.pem", compress_type=zipfile.ZIP_DEFLATED)
		arquivo_zip.close()
		
		os.remove("./app/static/" + str(id) + "_BDB.pem")
		os.remove("./app/static/" + str(id) + "_RSA.pem")
		
		#---------------------------------------------------------------------
		
		pub_patient_rsa = key.publickey().export_key()
		#---------------------------------------------------------

		pub_patient_bdb = patient.public_key

		#-----------montar ativo do tipo usuario #paciente
		user_asset = {
		    'data': {
			'type'  : '#01',
			'ID'    : id, 
			'nome'  : nome,
			'pubRSA': pub_patient_rsa,
			'pubBDB': pub_patient_bdb
			},
		}

		prepared_creation_tx = bdb.transactions.prepare(
		    operation='CREATE',
		    signers=pub_patient_bdb,
		    asset=user_asset
		)

		fulfilled_creation_tx = bdb.transactions.fulfill(
		    prepared_creation_tx,
		    private_keys=patient.private_key
		)

		sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)
		#print(fulfilled_creation_tx['id'])
		self.tx_id = fulfilled_creation_tx['id']
		
	def buscar(self, id):
		bdb_root_url = 'http://localhost:9984/'  # Use YOUR BigchainDB Root URL here

		bdb = BigchainDB(bdb_root_url)

		cliente=MongoClient('localhost', 27017)
		banco = cliente['bigchain']
		asset = banco.assets
		print('id da instituicao' + id)
		doctor = asset.find({"data.type":"#01", "data.ID":id})
		
		try:	
			if doctor[0] :
				self.rsa   = doctor[0]['data']['pubRSA']
				self.bdb   = doctor[0]['data']['pubBDB']
				self.asset_id = doctor[0]['id']
		except:
			self.asset_id = None

