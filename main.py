"""
pip install mysql-connector-python
For zbar(qrcode) https://pyseek.blogspot.com/2021/08/create-your-own-qr-code-scanner-using-python.html
pip install pycryptodome
"""

from database import Database
from medbot import Medbot

if __name__ == "__main__":
    database = Database('localhost','medbot','clarence','admin')
    medbot = Medbot(database)
    user = medbot.login()
    print(user.get_info())