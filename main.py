from database import Database
from medbot import Medbot
from threading import Thread
if __name__ == "__main__":
    database = Database('sql.freedb.tech','freedb_medbot','freedb_medbot','ct9xVSS$$2g35s7')
    medbot = Medbot(database)
    user = medbot.login()
    print(user.get_info())
    medbot.set_speaker_properties(voice = 'jarvis')
    text = 'Please position your arm correctly'
    test = Thread(target=lambda:medbot.speak('test'))
    test.start()
    medbot.logout()
    print(medbot.get_current_user())