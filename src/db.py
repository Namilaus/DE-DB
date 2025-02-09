import mysql.connector


class db:
    def __init__(self, host: str, username: str, password: str, database: str):
        self.host = host
        self.username = username
        self.password = password
        self.database = database

    def connect(self):
        try:
            mydb = mysql.connector.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database,
            )
            print("Connected to the database successfully")
            return mydb
        except Exception as err:
            print(err)
            return Null
