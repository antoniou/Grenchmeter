from sqlite3 import dbapi2 as sqlite

class CMySQLConnection:

    def __init__(self, DBName):
        self.connection = sqlite.connect( DBName )

    def getCursor(self):
        return self.connection.cursor()
    
    def commit(self):
        self.connection.commit()
        
    def close(self):
        self.connection.close()
        
