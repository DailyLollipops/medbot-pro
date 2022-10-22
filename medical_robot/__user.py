__all__ = ['User']

########################################################
#                      Main Class                      #
########################################################

# A user object that a Medbot and Database object returns after successful login
class User:

    def __init__(self, id: int, password: str):
        '''
            Initialize a User object instance.
        '''
        self.id = id
        self.password = password
        self.authenticated = False
        self.name = None
        self.age = None
        self.gender = None

    def get_id(self):
        '''
            Returns the `id` of the user
        '''
        return self.id

    def get_info(self):
        '''
            Returns a dictionary of user info
        '''
        info = {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'authenticated': self.authenticated
        }
        return info

    def is_authenticated(self):
        '''
            Returns `True` if authenticated otherwise `False`
        '''
        return self.authenticated