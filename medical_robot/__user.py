__all__ = ['User']

class User:
    def __init__(self, id, password):
        self.id = id
        self.password = password
        self.authenticated = False
        self.name = None
        self.age = None
        self.gender = None

    def is_registered(self, database):
        check = database.user_exists(self.id)
        if(check):
            return True
        else:
            return False
    
    def login(self, database):
        success = database.verify(self.id, self.password)
        if(success):
            self.authenticated = True
            info = self.retrieve_info_from_database()
            self.name = info['name']
            self.age = self.__get_age(info['birthday'])
            self.gender = info['gender']
            return True
        else:
            raise Exception('Wrong Credentials')

    def get_id(self):
        return self.id

    def get_info(self):
        info = {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'authenticated': self.authenticated
        }
        return info

    def is_authenticated(self):
        return self.authenticated