# app_block
A software architecture based on the blockchain–database hybrid for electronic health records

Configure a static IP address for the machine.
Then, installation and configuration of the node that is composed of the BigchainDB, Tendermint e MongoDB.

Through the available tutorial (http://docs.bigchaindb.com/projects/server/en/latest/simple-deployment-template/set-up-node-software.html), make
installation and configuration. BigchainDB requires a version of MongoDB equal to or greater than 3.4. The version of Tendermint used and suggested by BigchainDB is 0.31.5

It is necessary to install:
Flask
Flask-RESTPlus
Flask-WTForms

The main script used for taking time is in the /script directory. The script used the keys created earlier. And the script was executed through 32 threads.

The results obtained and the time files are available in the /results directory
