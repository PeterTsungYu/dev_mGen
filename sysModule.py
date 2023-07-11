class sysModule:
    def __init__(self, lst_servers:list):
        self.lst_servers = lst_servers
        self.data_factory = {}
    
    def collect_server_data_silos(self,):
        for server in self.lst_servers:
            self.data_factory[server.id] = server.data_silo

