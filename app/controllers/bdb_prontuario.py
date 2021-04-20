from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from time import sleep
from sys import exit
import json
from Crypto.Random import get_random_bytes
from pymongo import MongoClient

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256

import zipfile

class Prontuario_bdb:	
	#atributos
	id = ""
	nome = ""
	
	def __init__(self):
		pass
		
	def criar(self, cabecalho, subjective, objective, assessment, plan, chaveI, chaveP, chaveI_rsa, chaveP_rsa, filename, priv_RSA, priv_BDB) :
	
		bdb_root_url = 'http://localhost:9984/'  # Use YOUR BigchainDB Root URL here

		bdb = BigchainDB(bdb_root_url)

		session_key = get_random_bytes(16)
        session_key = session_key.encode('utf-8')
				
		soap_asset = {
		    		'Subjective': subjective,
                    'Objective' : objective,
			    	'Assessment': assessment,
			    	'Plan'      : plan
		}

		result = json.dumps(soap_asset)
		plain_str_16 = result + ( 16 - len(result) % 16 ) * ' ' 

		#------encripta o prontuario SOAP
		chiper = AES.new(session_key, AES.MODE_ECB)
		result = chiper.encrypt(plain_str_16.encode('utf-8'))

		#------criar o ativo do prontuario
		emr_asset = {
			'data' : {
		    		'type': '#99',
				'cabecalho' : cabecalho,
			    	'prontuario': result.decode("iso-8859-1")
			}
		}
		
		# chaves publicas dos donos do ativo
		lista_donos = chaveI #chave publica do doutor 

		prepared_creation_tx = bdb.transactions.prepare(
		    operation='CREATE',
		    signers= chaveI, #chave publica do doutor
		    asset=emr_asset,
		    recipients=lista_donos
		)
		
		try:
			fulfilled_creation_tx = bdb.transactions.fulfill(
			    prepared_creation_tx,
			    private_keys=priv_BDB #chave privada da instituicao
			)

			try:
				sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)
				self.txid = fulfilled_creation_tx['id']
				self.transfer_asset(fulfilled_creation_tx, priv_BDB, chaveI, chaveP, bdb)
				if self.txid:
					self.txid_transf = self.txid 
					#----------------------------------------------------
					#-------------------CRIACAO DO ATIVO DO TIPO ACESSO
					#----------------------------------------------------
					recipient_key = RSA.import_key(chaveI_rsa)
					cipher_rsa = PKCS1_OAEP.new(recipient_key)
					enc_session_key_doctor = cipher_rsa.encrypt(session_key)
					#---------------------------------------------
					recipient_key = RSA.import_key(chaveP_rsa)
					cipher_rsa = PKCS1_OAEP.new(recipient_key)
					enc_session_key_patient = cipher_rsa.encrypt(session_key)
					#-------------------------------------------
					chaves = [
						{
							'pub'     : chaveI, #chave publica da instituicao
							'session' : enc_session_key_doctor.decode("ISO-8859-1")
						},
						{
							'pub'     : chaveP, #chave publica do paciente
							'session' : enc_session_key_patient.decode("ISO-8859-1")
						}
						
					]
					#------criar o ativo do prontuario
					access_asset = {
						'data' : {
					    		'type'   : '#88',
							'id_emr' : fulfilled_creation_tx['id'], #self.txid,
						    	'chaves' : chaves
						}
					}

					# chaves publicas dos donos do ativo
					# paciente dos responsaveis e do doutor
					#lista_donos = (chaveI, #chave publica do paciente
					#		chaveP) #chave publica do doutor) 
					
					lista_donos = (chaveI)

					prepared_creation_tx = bdb.transactions.prepare(
					    operation='CREATE',
					    signers=chaveI, #chave publica do paciente
					    asset=access_asset,
					    recipients=lista_donos
					)

					fulfilled_creation_tx = bdb.transactions.fulfill(
					    prepared_creation_tx,
					    private_keys=priv_BDB #chave privada do paciente
					)

					try:
						sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)
						self.txid = fulfilled_creation_tx['id']
						self.txid_acesso = self.txid
						print('acesso->'+self.txid)
					except:
						self.txid = None
					#----------------------------------------------------
				
			except:
				self.txid = None 
		except:
			self.txid = None
				
	def transfer_asset(self, creation_tx, priv_BDB, chaveI, chaveP, bdb):
		print('transferencia')
		
		asset_id = creation_tx['id']

		print(asset_id)

		transfer_asset = {
			'id': asset_id,
		}
		
		output_index = 0

		output = creation_tx['outputs'][output_index]

		transfer_input = {
			'fulfillment': output['condition']['details'],
			'fulfills': {
				'output_index': output_index,
				'transaction_id': creation_tx['id'],
			},
			'owners_before': output['public_keys'],
		}
		
		prepared_transfer_tx = bdb.transactions.prepare(
			operation='TRANSFER',
			asset=transfer_asset,
			inputs=transfer_input,
			recipients=chaveP,
		)

		fulfilled_transfer_tx = bdb.transactions.fulfill(
			prepared_transfer_tx,
			private_keys=priv_BDB,
		)
		
		try:
			sent_transfer_tx = bdb.transactions.send_commit(fulfilled_transfer_tx)
			self.txid = fulfilled_transfer_tx['id']
			print('transfer->'+self.txid)
		except:
			print('none')
			self.txid = None 

   				
	def buscar(self, id, chaveRSA, chaveBDB):
		bdb_root_url = 'http://localhost:9984/'  # Use YOUR BigchainDB Root URL here

		bdb = BigchainDB(bdb_root_url)

		cliente=MongoClient('localhost', 27017)
		banco = cliente['bigchain']
		
		asset = banco.assets

		enc_session_key = '?'
		access = asset.find({"data.type":"#88", "data.id_emr": id})
		for chave in asset.find({"data.type":"#88", "data.id_emr": id}):
			for item in chave['data']['chaves']:
				if item['pub'] ==  chaveBDB:
					enc_session_key = item['session']
		
		if enc_session_key != '?':
			enc_session_key = enc_session_key.encode("iso-8859-1")
			private_key = RSA.import_key(chaveRSA)
			cipher_rsa = PKCS1_OAEP.new(private_key)
			try:
				session_key = cipher_rsa.decrypt(enc_session_key)
				print(session_key)
				
				emr = asset.find({"data.type":"#99", "id":id})
				ciphertext = emr[0]['data']['prontuario'].encode("iso-8859-1")
				# Decrypt the data with the AES session key
				cipher_aes = AES.new(session_key, AES.MODE_ECB)
				print('aqui')
				data = cipher_aes.decrypt(ciphertext)
				json_object = json.loads(data)
				json_formatted_str = json.dumps(json_object, indent=2)
				
				self.html = json_formatted_str
				#print(json_formatted_str)
			except:
				self.html = None #print('Sem permissão.')
		else:
			self.html = None #print('Sem permissão.')
			
	def listar(self, idP):
		bdb_root_url = 'http://localhost:9984/'  # Use YOUR BigchainDB Root URL here

		bdb = BigchainDB(bdb_root_url)

		cliente=MongoClient('localhost', 27017)
		banco = cliente['bigchain']

		asset = banco.assets
		transactions = banco.transactions

		user = asset.find({"data.type":"#01", "data.ID":idP})
		self.user_pub_key_bdb = user[0]['data']['pubBDB']
		self.html={}
		#transactions = transactions.find({"operation":"CREATE"})
		transactions = transactions.find({"operation":"TRANSFER"})
		
		for transaction in transactions:
		   if transaction['outputs'][0]['public_keys'][0] == self.user_pub_key_bdb:
		      emr = asset.find({"data.type":"#99", "id":transaction['asset']['id']})
		      for item in emr:
		         self.html[item['data']['cabecalho']] = item['id']
		        
	def acesso(self, id, chaveP, idI, priv_bdb, priv_rsa):
		bdb_root_url = 'http://localhost:9984/'  # Use YOUR BigchainDB Root URL here

		bdb = BigchainDB(bdb_root_url)

		cliente=MongoClient('localhost', 27017)
		banco = cliente['bigchain']
		asset = banco.assets

		doctor = asset.find({"data.type":"#02", "data.ID":idI})

		doctor_pub_key_rsa = doctor[0]['data']['pubRSA']
		doctor_pub_key_bdb = doctor[0]['data']['pubBDB']
		#----------------------------
		access = asset.find({"data.type":"#88", "data.id_emr": id})
		for chave in asset.find({"data.type":"#88", "data.id_emr": id}):
			for item in chave['data']['chaves']:
				if item['pub'] ==  chaveP:
					enc_session_key = item['session']
				
		enc_session_key=enc_session_key.encode("iso-8859-1")
				
		private_key = RSA.import_key(priv_rsa)
		cipher_rsa = PKCS1_OAEP.new(private_key)
		session_key = cipher_rsa.decrypt(enc_session_key)
				
		recipient_key = RSA.import_key(doctor_pub_key_rsa)
		cipher_rsa = PKCS1_OAEP.new(recipient_key)
		enc_session_key_doctor = cipher_rsa.encrypt(session_key)
		#---------------------------------------------

		chaves = [
			{
				'pub'     : doctor_pub_key_bdb, #chave publica da instituicao
				'session' : enc_session_key_doctor.decode("ISO-8859-1")
			}
		]

		#------criar o ativo do prontuario
		access_asset = {
			'data' : {
		    		'type'   : '#88',
				'id_emr' : id,
			    	'chaves' : chaves
			}
		}

		# chaves publicas dos donos do ativo
		# paciente dos responsaveis e do doutor
		lista_donos = (chaveP) #chave publica do doutor) 
		print('chavePublica->'+chaveP)
		print('chavePrivada->'+priv_bdb)
		prepared_creation_tx = bdb.transactions.prepare(
		    operation='CREATE',
		    signers=chaveP, #chave publica do paciente
		    asset=access_asset ,
		    recipients=lista_donos
		)

		fulfilled_creation_tx = bdb.transactions.fulfill(
		    prepared_creation_tx,
		    private_keys=priv_bdb #chave privada do paciente
		)

		sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)

		self.txid = fulfilled_creation_tx['id']
