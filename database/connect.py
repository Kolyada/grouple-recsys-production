from mysql.connector import connect

class Connect:

    def __init__(self, user, password, host, database):
        self.user = user
        self.password = password
        self.host = host
        self.database = database

    def get_con(self):
        return connect(
            user = self.user, 
            password = self.password, 
            host = self.host,
            database = self.database
            auth_plugin='mysql_native_password'
            )