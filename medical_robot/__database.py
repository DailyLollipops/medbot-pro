from .__user import User
from datetime import datetime
from datetime import date
import mysql.connector
import bcrypt

__all__ = ['Database']

########################################################
#                      Main Class                      #
########################################################

# This class creates a database object that is used by the
# medbot to read and store data
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

    # Get user info using an User object
    def get_user_info(self, user):
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

    # Get user info using user id(int)
    def get_user_info_by_id(self, user_id):
        query = "select * from users where id =%s"
        id = (user_id,)
        cursor = self.connection.cursor()
        cursor.execute(query, id)
        record = cursor.fetchone()
        cursor.close()
        if(len(record) > 0):
            return record
        else:
            raise Exception('User does not exist in the current database')

    # Parse birthday to age now
    # Returns an int
    def __get_age(self, birthday):
        birthday = datetime.strptime(str(birthday), "%Y-%m-%d").date()
        today = date.today()  
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        return age

    # Returns available insertable columns
    def __get_columns_name(self, table):
        cursor = self.connection.cursor(dictionary = True, buffered = True)
        cursor.execute('SELECT * FROM ' + table)
        sample = cursor.fetchone()
        columns_name = ''
        for column in sample:
            columns_name += ','+ column
        columns_name = columns_name.replace(',id,', "")
        cursor.close()
        return columns_name

    # Verify and change user authenticated property to true
    def verify(self, user):
        password_bytes = user.password.encode('utf-8')
        record = self.get_user_info(user)
        stored_password = record[10].encode('utf-8')
        result = bcrypt.checkpw(password_bytes, stored_password)
        if(result):
            user.authenticated = True
            user.name = record[1]
            user.age = self.__get_age(record[2])
            user.gender = record[3]
            return True
        else:
            return False
        
    # Returns an authenticated User object
    def verify_by_credentials(self, user_id, user_password):
        password_bytes = user_password.encode('utf-8')
        record = self.get_user_info_by_id(user_id)
        stored_password = record[10].encode('utf-8')
        result = bcrypt.checkpw(password_bytes, stored_password)
        if(result):
            user = User(user_id, user_password)
            user.authenticated = True
            user.name = record[1]
            user.age = self.__get_age(record[2])
            user.gender = record[3]
            return user
        else:
            return False

    # Insert record to a table in the database
    def insert_record(self, table, values):
        columns = self.__get_columns_name(table)
        cursor = self.connection.cursor()
        query = 'INSERT INTO readings (' + columns + ') VALUES ('+ '%s' * columns.count(',')+1 +')'
        cursor.execute(query, values)
        self.connection.commit()