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
    
    def __init__(self, host: str, database: str, user: str, password: str):
        '''
            Initialize a Database object using the supplied credentials \n
            Throws an Exception if connection to the database is unsuccessfull
        '''
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

    def reconnect(self):
                    self.connection = mysql.connector.connect(host = self.host,
                                        database = self.database,
                                        user = self.user,
                                        password = self.password)

    def get_user_info(self, user: User):
        '''
            Get user info from a User object \n
            Querries the `user.id` in the database and return the user's info
        '''
        query = "select * from users where id =%s"
        id = (user.id,)
        cursor = self.connection.cursor(dictionary = True)
        cursor.execute(query, id)
        record = cursor.fetchone()
        cursor.close()
        if(len(record) > 0):
            return record
        else:
            raise Exception('User does not exist in the current database')

    # Get user info using user id(int)
    def get_user_info_by_id(self, user_id: int):
        '''
            Get user info using `user_id` from the database
        '''
        query = "select * from users where id =%s"
        id = (user_id,)
        cursor = self.connection.cursor(dictionary = True)
        cursor.execute(query, id)
        record = cursor.fetchone()
        cursor.close()
        if(len(record) > 0):
            return record
        else:
            raise Exception('User does not exist in the current database')

    def __get_age(self, birthday):
        '''
            Parse `birthday` and returns the `age` now
        '''
        birthday = datetime.strptime(str(birthday), "%Y-%m-%d").date()
        today = date.today()  
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        return age

    def __get_columns_name(self, table):
        '''
            Returns available editable columns from a `table`
        '''
        cursor = self.connection.cursor(dictionary = True, buffered = True)
        cursor.execute('SELECT * FROM ' + table)
        sample = cursor.fetchone()
        columns_name = ''
        for column in sample:
            columns_name += ','+ column
        columns_name = columns_name.replace(',id,', "")
        cursor.close()
        return columns_name

    def verify(self, user: User):
        '''
            Verify and change user authenticated property to true
        '''
        self.reconnect()
        password_bytes = user.password.encode('utf-8')
        record = self.get_user_info(user)
        stored_password = record['password'].encode('utf-8')
        result = bcrypt.checkpw(password_bytes, stored_password)
        if(result):
            user.authenticated = True
            user.name = record['name']
            user.age = self.__get_age(record['birthday'])
            user.gender = record['gender']
            return True
        else:
            return False
        
    # Returns an authenticated User object
    def verify_by_credentials(self, user_id: int, user_password: str):
        '''
            Create and return an authenticated User object if credential
            supplied is valid \n
            Returns `False` if credentials are not valid
        '''
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

    def insert_record(self, table: str, values: tuple or list):
        '''
            Insert record to a table in the database
        '''
        self.reconnect()
        columns = self.__get_columns_name(table)
        cursor = self.connection.cursor()
        query = f'''INSERT INTO {table}({columns}) VALUES ({'%s, ' * (len(values)-1)}%s)'''
        cursor.execute(query, values)
        cursor.close()
        self.connection.commit()

    def insert_reading(self, id: int, pulse_rate: int, blood_saturation: int, blood_pressure: int, systolic: int, diastolic: int):
        '''
            ### Medbot table specific
            Insert values to readings table
        '''
        self.reconnect()
        cursor = self.connection.cursor()
        now = datetime.now()
        date_now = now.strftime('%Y-%m-%d %H:%M:%S')
        query = '''INSERT INTO readings(user_id,pulse_rate,blood_saturation,blood_pressure,systolic,diastolic,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
        values = (id, pulse_rate,blood_saturation,blood_pressure,systolic,diastolic,date_now,date_now)
        cursor.execute(query, values)
        self.connection.commit()
        cursor.close()