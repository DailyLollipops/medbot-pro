from database import Database
from medbot import Medbot

if __name__ == "__main__":
    database = Database('localhost','medbot','clarence','admin')
    medbot = Medbot(database)
    user = medbot.login()
    print(user.get_info())