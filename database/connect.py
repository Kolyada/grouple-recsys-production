from mysql.connector import connect

class Connect:

    def __init__(self, user, password, database):
        self.user = user
        self.password = password
        self.database = database

    def get_con(self):
        return connect(
            user = self.user, 
            password = self.password, 
            database = self.database
            )