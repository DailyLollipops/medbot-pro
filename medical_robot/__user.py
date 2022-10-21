__all__ = ['User']

########################################################
#                      Main Class                      #
########################################################

# A user object that a Medbot and Database object returns after successful login
class User:

    def __init__(self, id, password):
        self.id = id
        self.password = password
        self.authenticated = False
        self.name = None
        self.age = None
        self.gender = None

    # Returns an int(ID)
    def get_id(self):
        return self.id

    # Returns a dictionary of user info
    def get_info(self):
        info = {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'authenticated': self.authenticated
        }
        return info

    # Returns true if authenticated
    def is_authenticated(self):
        return self.authenticated