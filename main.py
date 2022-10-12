from database import Database
from medbot import Medbot

if __name__ == "__main__":
    database = Database('sql.freedb.tech','freedb_medbot','freedb_medbot','ct9xVSS$$2g35s7')
    medbot = Medbot(database)
    user = medbot.login()
    print(user.get_info())