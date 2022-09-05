import web3
import json
import binascii



class ContractReader:
    
    def __init__(self, _contractAddress, _networkRPC, _chainID, _abiFile):
        self.w3 = web3.Web3(web3.HTTPProvider(_networkRPC))
        self.chain_id = _chainID
        self.abi = json.load(open(_abiFile))
        self.contract = self.w3.eth.contract(address=_contractAddress, abi=self.abi["abi"])
        self.create_class_methods()
        
    
    def create_class_methods(self):
        functions = self.get_all_functions()
        for function in functions:
            name = function["name"]
            _parameters = [x["name"] for x in function["inputs"]]
            if len(_parameters)>0:
                parameters = str(tuple(_parameters)).replace("'","")
                if len(parameters) < 4: parameters = "( _input)"
                exec(f"def {name}(self, {parameters[1:]}: return self.contract.functions.{name}{parameters}.call()")
                exec(f"setattr(self.__class__, {name}.__name__, {name})")
            else:
                exec(f"def {name}(self,): return self.contract.functions.{name}().call()\nsetattr(self.__class__, {name}.__name__, {name})")
                #exec(f"setattr(self.__class__, {name}.__name__, {name})")
        
    def get_all_function_names(self):
        return [x["name"] for x in self.abi["abi"] if  x["type"]=="function" and x["stateMutability"] == "view" ]
        
    def get_all_functions(self):
        return [x for x in self.abi["abi"] if  x["type"]=="function" and x["stateMutability"] == "view" ]
    
    def get_function_inputs(self, name):
        return [x["inputs"] for x in self.abi["abi"] if  x["type"]=="function" and x["name"] ==  name][0]