from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from time import sleep
from sys import exit
import json

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256

from datetime import datetime
from random import randrange
from Crypto.Random import get_random_bytes

file_out = open("tempos_teste.txt", "w")
file_out.write(str(datetime.now()))
file_out.write('Prontuario;T.Total;T.prontuaria;T.acesso;T.transf\n')

bdb_root_url = 'http://localhost:9984/'  # Use YOUR BigchainDB Root URL here

bdb = BigchainDB(bdb_root_url)

session_key = get_random_bytes(16)
session_key = session_key.encode('utf-8')

tam = 2950

subjective = 'Objective'  * tam
objective  = 'Subjective' * tam 
assessment = 'Assessment' * tam
plan       = 'Plan '      * tam
#----------------------------------------------------------------------------------------------------------------------------

for tentativa in range(1000000):
                
        #file_out.write('Tentativa' + tentativa + '<INICIO>' )
        linha = ''
        now_ini = datetime.now()
        #file_out.write(now)
        
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
                	'cabecalho' : 'Cabecalho 3' + str(tentativa),
                    'prontuario': result.decode("ISO-8859-1")
	        }
        }

        # chaves publicas dos donos do ativo
        # paciente e dos responsaveis
        lista_donos = ('8W2F16nh5Rgwg5Pb37ZwbQTxv7cFt9Qv4HRgmxmwT9TP')  #chave publica da instituicao

        prepared_creation_tx = bdb.transactions.prepare(
            operation='CREATE',
            signers= '8W2F16nh5Rgwg5Pb37ZwbQTxv7cFt9Qv4HRgmxmwT9TP', #chave publica  #chave publica da instituicao
            asset=emr_asset,
            recipients=lista_donos
        )

        fulfilled_creation_tx = bdb.transactions.fulfill(
            prepared_creation_tx,
            private_keys='3nP2Ehmoxj2f9qvmkR4NsQUDF76yCSiUyQjfaGPwGmWe' #chave privada da instituicao
        )
#==================================================================================================        
        now_pront_ini = datetime.now()
#==================================================================================================        
        sent_creation_tx_prot = bdb.transactions.send_commit(fulfilled_creation_tx)
#==================================================================================================        
        now_pront_fim = datetime.now()
#==================================================================================================        

        txid = fulfilled_creation_tx['id']
        txtid_pront = txid
        print('ID')
        print(txid)
        #-------------------------------------------

        doctor_pub_key_rsa="""-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCwkJRtRdKM/Q0L+qpeK4bHs353\nG0IvqTsOfuKaccnpU1I0AuEW+mchb5VosTdemP5UhoGOsu3H5g5Ji6vkM238RA4z\nZ3b5uNquihItz2omPI8S+PSCsxgMaYL9GUlkSbBs9PXuxT/yevoZ0DKvYLsuywqv\nYQ8rCBCKMYUlxzVwaQIDAQAB\n-----END PUBLIC KEY-----"""

        recipient_key = RSA.import_key(doctor_pub_key_rsa)
        cipher_rsa = PKCS1_OAEP.new(recipient_key)
        enc_session_key_doctor = cipher_rsa.encrypt(session_key)
        #---------------------------------------------
        patient_pub_key_rsa="""-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCcjisAOmXLZO+QfBBjNJXPHAun\nkpdvNSAOGiGx6vc8YwnN9FmabLCpovqawjNxagSZD2tK/erUaxOdQeBCoojvrOOS\nkDoRgiTpX4ar0JlFEbfmdkBgjaGUZ5mSzi6o67i2MyyuR/ixxAWHDJZ5pS6k1cWh\nn/cQpOMGfiTMJgGfYQIDAQAB\n-----END PUBLIC KEY-----"""

        recipient_key = RSA.import_key(patient_pub_key_rsa)
        cipher_rsa = PKCS1_OAEP.new(recipient_key)
        enc_session_key_patient = cipher_rsa.encrypt(session_key)

        #-------------------------------------------
        chaves = [
	        {
		        'pub'     : '39cZEBPRN7XvSiz8NtxxB8wf9WzmqtcHbaj187bf5ShJ',   #chave publica do paciente
		        'session' : enc_session_key_doctor.decode("ISO-8859-1")
	        },
	        {
		        'pub'     : '8W2F16nh5Rgwg5Pb37ZwbQTxv7cFt9Qv4HRgmxmwT9TP',  #chave publica da instituicao
		        'session' : enc_session_key_patient.decode("ISO-8859-1")
	        }
	        
        ]

        #------criar o ativo do prontuario
        access_asset = {
	        'data' : {
            		'type'   : '#88',
                	'id_emr' : txid,
                    'chaves' : chaves
	        }
        }

        # chaves publicas dos donos do ativo
        # paciente dos responsaveis e do doutor
        lista_donos = ('8W2F16nh5Rgwg5Pb37ZwbQTxv7cFt9Qv4HRgmxmwT9TP', #chave publica da instituicao
		        '39cZEBPRN7XvSiz8NtxxB8wf9WzmqtcHbaj187bf5ShJ') #chave publica do paciente) 

        prepared_creation_tx = bdb.transactions.prepare(
            operation='CREATE',
            signers='8W2F16nh5Rgwg5Pb37ZwbQTxv7cFt9Qv4HRgmxmwT9TP', #chave publica a instituicao
            asset=access_asset,
            recipients=lista_donos
        )

        fulfilled_creation_tx = bdb.transactions.fulfill(
            prepared_creation_tx,
            private_keys='3nP2Ehmoxj2f9qvmkR4NsQUDF76yCSiUyQjfaGPwGmWe' #chave privada da instituicao
        )

#==================================================================================================        
        now_acesso_ini = datetime.now()
#==================================================================================================                
        sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)
#==================================================================================================        
        now_acesso_fim = datetime.now()
#==================================================================================================        

        txid = fulfilled_creation_tx['id']
        #------------------------------------------------------------------------
        transfer_asset = {
	        'id': txtid_pront,
        }

        output_index = 0

        output = sent_creation_tx_prot['outputs'][output_index]

        transfer_input = {
	        'fulfillment': output['condition']['details'],
	        'fulfills': {
		        'output_index': output_index,
		        'transaction_id': sent_creation_tx_prot['id'],
	        },
	        'owners_before': output['public_keys'],
        }
		        
        prepared_transfer_tx = bdb.transactions.prepare(
	        operation='TRANSFER',
	        asset=transfer_asset,
	        inputs=transfer_input,
	        recipients='39cZEBPRN7XvSiz8NtxxB8wf9WzmqtcHbaj187bf5ShJ',   #chave publica do paciente,
        )

        fulfilled_transfer_tx = bdb.transactions.fulfill(
	        prepared_transfer_tx,
	        private_keys='3nP2Ehmoxj2f9qvmkR4NsQUDF76yCSiUyQjfaGPwGmWe' #chave privada da instituicao,
        )
		        
#==================================================================================================        
        now_trans_ini = datetime.now()        
#==================================================================================================        
        sent_transfer_tx = bdb.transactions.send_commit(fulfilled_transfer_tx)
#==================================================================================================        
        now_trans_fim = datetime.now()
        
        now_fim = datetime.now()    
        
        linha = 'Prontuario' + str(tentativa) +';'
        linha = linha + str(now_fim - now_ini)+';'
        linha = linha + str(now_acesso_fim - now_acesso_ini)+';'
        linha = linha + str(now_pront_fim - now_pront_ini)+';'
        linha = linha + str(now_trans_fim - now_trans_ini)+'\n'
        
        file_out.write(linha)
#==================================================================================================                
file_out.write(str(datetime.now()))
file_out.close()








