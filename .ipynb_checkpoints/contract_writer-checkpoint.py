from transaction import Transaction
from contract_reader import ContractReader
import web3
import json



class ContractWriter(ContractReader, Transaction):
    
    def __init__(self, _contractAddress, _networkRPC, _chainID, _abiFile, priv_key):
        self.w3 = web3.Web3(web3.HTTPProvider(_networkRPC))
        self.chainID = _chainID
        self.abi = json.load(open(_abiFile))
        self.contract = self.w3.eth.contract(address=_contractAddress, abi=self.abi["abi"])
        self.account = self.w3.eth.account.privateKeyToAccount(priv_key)
        Transaction.__init__(self, self.w3)
        self.reader = ContractReader( _contractAddress, _networkRPC, _chainID, _abiFile)
        self.create_class_methods()
        
    
    def create_class_methods(self):
        functions = self.get_all_functions()
        for function in functions:
            name = function["name"]
            _parameters = [x["name"] for x in function["inputs"]]
            if len(_parameters) > 0:
                parameters = str(tuple(_parameters)).replace("'","").replace("from","_from")
                if len(parameters) < 4: parameters = "( _input)"
                line1 = f"def {name}(self, {parameters[1:-1]}, maxFeePerGas = None, maxPriorityFeePerGas = None, nonce=None, value=0): ".replace(",,",",")
                line2 = f"\n    tx = self.contract.functions.{name}{parameters}"
                line3 = f"\n    return self.sendTransaction(tx, maxFeePerGas, maxPriorityFeePerGas, nonce, value)"
                exec(line1 + line2 + line3)
                exec(f"setattr(self.__class__, {name}.__name__, {name})")
            else:
                line1 = f"def {name}(self, maxFeePerGas = None, maxPriorityFeePerGas = None, nonce=None, value=0): "
                line2 = f"\n    tx = self.contract.functions.{name}()"
                line3 = f"\n    return self.sendTransaction(tx, maxFeePerGas, maxPriorityFeePerGas, nonce, value)"
                exec(line1 + line2 + line3)
                exec(f"setattr(self.__class__, {name}.__name__, {name})")
        
    def get_all_function_names(self):
        return [x["name"] for x in self.abi["abi"] if  x["type"]=="function" and (x["stateMutability"] == "payable" or x["stateMutability"] == "nonpayable") ]
        
    def get_all_functions(self):
        return [x for x in self.abi["abi"] if  x["type"]=="function" and (x["stateMutability"] == "payable" or x["stateMutability"] == "nonpayable") ]
    
    def get_function_inputs(self, name):
        return [x["inputs"] for x in self.abi["abi"] if  x["type"]=="function" and x["name"] ==  name][0]