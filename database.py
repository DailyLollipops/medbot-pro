from datetime import datetime
from datetime import date
import mysql.connector
import bcrypt

class Database:
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        try:
            self.connection = mysql.connector.connect(host = self.host,
                                        database = self.database,
                                        user = self.user,
                                        password = self.password)
        except:
            raise Exception('Error connecting to database')

    def __get_user_info(self, user):
        query = "select * from users where id =%s"
        id = (user.id,)
        cursor = self.connection.cursor()
        cursor.execute(query, id)
        record = cursor.fetchone()
        cursor.close()
        if(len(record) > 0):
            return record
        else:
            raise Exception('User does not exist in the current database')

    def __get_age(self, birthday):
        birthday = datetime.strptime(str(birthday), "%Y-%m-%d").date()
        today = date.today()  
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        return age

    def __get_columns_name(self, table):
        cursor = self.connection.cursor(dictionary = True)
        cursor.execute('SELECT * FROM ' + table)
        sample = cursor.fetchone()
        columns_name = ''
        for column in sample:
            columns_name += ','+ column
        columns_name = columns_name.replace(',id,', "")
        cursor.close()
        return columns_name

    def verify(self, user):
        password_bytes = user.password.encode('utf-8')
        record = self.__get_user_info(user)
        stored_password = record[10].encode('utf-8')
        result = bcrypt.checkpw(password_bytes, stored_password)
        if(result):
            user.name = record[1]
            user.age = self.__get_age(record[2])
            user.gender = record[3]
            return True
        else:
            return False

    def insert_record(self, table, values):
        columns = self.__get_columns_name(table)
        cursor = self.connection.cursor()
        query = 'INSERT INTO readings (' + columns + ') VALUES ('+ '%s' * columns.count(',')+1 +')'
        cursor.execute(query, values)
        self.connection.commit()