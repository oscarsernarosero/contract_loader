import binascii


class Transaction:

    def __init__(self, _w3):
        """
        Constructor.
        
        Arguments:
            _contractAddress: String. The address of the NFT contract.
        """
        w3 = _w3
        self.w3 = w3
        
    def __repr__(cls):
        return f"<SDKUser with address {cls.account.address} for SDK NFT at {cls.smartContractAddress} in network with chain ID: {cls.chainID}>"
        

    def BuildTransaction(self, tx, address, maxFeePerGas, maxPriorityFeePerGas, nonce=None, value=0):
        """
        Builds a raw transaction.
        
        Arguments:
            tx: web3.transaction: the transaction object that needs to be built into a raw transaction.
            address: String. The sender address.
            nonce: (Optional) Int. The nonce of the transaction.
            
        Returns:
            rawTransaction object to be signed.
        """
        gas = tx.estimateGas({'from':address,'value':value})#*gas_fee
        if nonce is None: nonce = self.w3.eth.getTransactionCount(address)
        raw = ""
        #try:
        raw = tx.buildTransaction({
                   'chainId':self.chainID,
                   'nonce': nonce,
                   'from': address,
                   'maxFeePerGas': maxFeePerGas,
                   'maxPriorityFeePerGas': maxPriorityFeePerGas,
                   'gas': int(gas * 1.1),
                   'value': value
                    })
        return raw
            

    # this function uses a wallet that is loaded and a transaction with a smart contract and builds/sends it
    def sendTransaction(self, trans, maxFeePerGas=30000000000, maxPriorityFeePerGas=10000000000, nonce=None, value=0):
        """
        Builds a raw transaction.
        
        Arguments:
            tx: web3.transaction: the transaction object that needs to be converted into a raw transaction.
            address: String. The sender address.
            nonce: (Optional) Int. The nonce of the transaction.
            
        Returns:
            Touple: (success: Bool,tx_hash/error: String). Returns a touple where the first element represents the
            success of the transaction to be broadcastes, and the second element will be the tx hash in the case
            of a successful broadcasting or an error description in the case of failure.
        """
        if maxFeePerGas is None: maxFeePerGas = 1000000000
        if maxPriorityFeePerGas is None: maxPriorityFeePerGas = 500000000 
        #x = self.w3.eth.getTransactionCount(self.account.address)
        built_transaction = self.BuildTransaction(trans,
                                                  self.account.address, 
                                                  maxFeePerGas, 
                                                  maxPriorityFeePerGas, 
                                                  nonce,
                                                  value)
        
        signed_transaction = self.account.sign_transaction(built_transaction)
        result = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        return (True, binascii.hexlify(result).decode('utf-8'))

    
    def sendTransactions(self, trans, nonce):
        """
        Broadcasts a transaction to the network without waiting on the transaction with previous nonce to be mined.
        
        Arguments:
            trans: web3.transaction: the transaction object that needs to be converted into a raw transaction.
            nonce: (Optional) Int. The nonce of the transaction.
            
        Returns:
            String. The transaction hash of the transaction broadcasted.
        """
        built_transaction = self.buildTransaction(trans, self.account.address, nonce)
        signed_transaction = self.account.signTransaction(built_transaction)
        result = self.w3.eth.sendRawTransaction(signed_transaction.rawTransaction)
        return binascii.hexlify(result).decode('utf-8')

    
    def send_tx_batch(self, arg_batch, starting_nonce = None, baseFee = 100):
        """
        send a batch of transactions to the network. 
        
        Arguments:
            self: self object that will sign for the transactions.
            arg_batch: Array: the list of arguments. The format should be:
                [ '<method_name>', [{args_1}, {args_2},...{args_n}] ] where '{args}'
                has the same argument names that the <method_name> receives.
                Example:  
                [ 'makeMetadata', [
                    {"args":{"_tokenId": 2, "_URI": "my/uri/2"},"id":7263, "maxFeePerGas": 43323, "maxPriorityFeePerGas": 64382}, 
                    {"args":{"_tokenId": 3, "_URI": "my/uri/3"},"id":7265, "maxFeePerGas": 43323, "maxPriorityFeePerGas": 64382},
                                            ] 
                            ]
            starting_nonce: (Optional) Int. In case of a costume nonce (not recommended).
            
        Returns:
            Array of strings: list of transaction hashes for each transaction.
        """
        if starting_nonce is None:
            nonce = self.w3.eth.getTransactionCount(self.account.address)
        else:
            nonce = starting_nonce
            
        current_nonce = None
        current_id = None
        tx_hashes = []
        for index,arg_set in enumerate(arg_batch[1]):
            current_id = arg_set["id"]
            current_nonce = nonce+index
            result = ""
            enough_gas = True
            if arg_set["maxFeePerGas"] is None: 
                try: 
                    arg_set["maxFeePerGas"] = config("MAX_GAS_FEE")
                    arg_set["maxPriorityFeePerGas"] = config("MAX_PRIORITY_FEE")
                except: 
                    print("Couldn'd find ENV variable MAX_GAS_FEE or MAX_PRIORITY_FEE. Working with preset values")
                    arg_set["maxFeePerGas"] = 20000000000
                    arg_set["maxPriorityFeePerGas"] = 5000000000
                
                
            counter = 0
            
            while (baseFee >= (arg_set["maxFeePerGas"] + arg_set["maxPriorityFeePerGas"])):
                if counter%20 == 0: logging.info("MAXFEE TOO LOW!. waiting for the next block...")
                time_out = 2 #min
                try   : time_out = config("LOW_GAS_TIME_OUT_MINUTES")
                except: print("Couldn'd find ENV variable LOW_GAS_TIME_OUT_MINUTES. Working with preset values")
                sleep_time = 3
                sleep(sleep_time)
                iterations_time_out = (time_out * 60)/sleep_time
                if(counter > iterations_time_out):
                    tx_hashes.append({"tx_hash": "Tx not sent due to low gas.",
                            "success": False,
                            "id": arg_set["id"],
                            "nonce": nonce+index
                            })
                    enough_gas = False
                    break
                    
                counter+=1
                
            result = (False,"Not started.")
            if enough_gas:
                try:
                    result = self.__class__.__dict__[arg_batch[0]](self,
                                                                **arg_set["args"],
                                                                maxFeePerGas = arg_set["maxFeePerGas"], 
                                                                maxPriorityFeePerGas = arg_set["maxPriorityFeePerGas"],
                                                                nonce = nonce+index)
                except web3.exceptions.ContractLogicError as error:
                    result = (False,error.args[0])
                    #return([{"success": False, "tx_hash": result[1], "id": arg_set["id"] , "nonce": nonce+index}])
                except ValueError as error:
                    #result = (False,error.args[0]["code"])
                    result = (False,"Most likely, gas parameters too low. New/replacement tx. "+json.dumps(error.args[0]))
                    #return([{"success": False, "tx_hash": result[1], "id": arg_set["id"] , "nonce": nonce+index}])
                except Exception as error:
                    result = (False,"Unhandled: "+error.args[0])
                    #return([{"success": False, "tx_hash": result[1], "id": arg_set["id"] , "nonce": nonce+index}])
            else:
                result = ( False, "LOW GAS")
                
            tx_hashes.append({"tx_hash": result[1],
                            "success": result[0],
                            "id": arg_set["id"],
                            "nonce": nonce+index
                            })
            if not result[0]:break
            
        return tx_hashes



    