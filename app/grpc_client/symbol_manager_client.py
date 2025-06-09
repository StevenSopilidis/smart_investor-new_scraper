from app.config import settings
import grpc
import api_pb2
import api_pb2_grpc

class SymbolManagerClient:
    def __init__(self):
        channel = grpc.insecure_channel(settings.SYMBOL_MANAGER_SERVICE_ADDR)
        self.stub = api_pb2_grpc.ApiServicer(channel)
        
    def get_active_symbols(self):
        res = self.stub.GetActiveSymbols(api_pb2.GetActiveSymbolsRequest())
        symbols = []
        
        for symbol in res:
            symbols.append(symbol.ticker)
        
        return symbols