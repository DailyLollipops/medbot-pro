# medbot-pro
Raspberry Pi program for the Medbot: Pulse Rate and Blood Pressure Monitor

### Setup
The program is intended for Raspberry Pi OS and has been tested only for Raspberry Pi 4B with the following configuration
- [x] I2C communication enabled
- [x] Legacy Camera enabled
 
 The program is also dependent on the several libraries. To install required library run:
 - `pip install mysql-connector-python==8.0.29`
 - `pip install bcrypt`
 - `pip install pyzbar`
 - `pip install pycryptodome`
 - `pip install python-printer-ecspos`
 - `pip install SpeechRecognition`
 - `pip install bleak`
 - `pip install pyaudio`
 - `sudo apt-get install flac`
 - `sudo apt install espeak`
 - `sudo apt install libespeak-dev`
 
The Arduino code is located on `/medical_robot/arduino/arduino.ino` and should be uploaded

A MYSQL database should also be set up
Users Table
| id | name | birthday | gender | phone_number | baranggay | municipality | email | bio | profile_picture_path | password | type | remember_token | created_ at | updated_at |
| -- | ---- | -------- | ------ | ------------ | --------- | ------------ | ----- | --- | -------------------- | -------- | ---- | -------------- | ----------- | ---------- |
| id  | varchar(255) | date | varchar(255) | varchar(255) | varchar(255) | varchar(255) | varchar(255) | varchar(255) | varchar(255) | varchar(255) | varchar(255) | varchar(255) | timestamp | timestamp |

Readings Table
| id | user_id | pulse_rate | blood_saturation | blood_pressure | systolic | diastolic | created_at | updated_at |
| -- | ------- | ---------- | ---------------- | -------------- | -------- | --------- | ---------- | ---------- |
| id | int | int | int | int | int | int | timestamp | timestamp |

Or you can use the migrate option from the [Med-bot's Website](https://github.com/DailyLollipops/medbot) by running `php artisan migrate`

### Running
The `medbot` class provides functions to interface with the hardware. First, initialize a `medical_robot.Database` class
and pass the database object when creating a `medical_robot.medbot` object.
```python
import medical_robot
database = medical_robot.Database('host', 'database', 'user', 'password')
medbot = medical_robot.Medbot(database)
```

It is required to login first to use several user related functions such as taking measurement and saving to the database.
To login, simply call the `login` method
```python
medbot.login()
```
The User class holds the currently logged in user's info. <br/>
You can read more about other available functions by reading the in-line documentation on the source codes

#### Available Arduino Commands
The Raspberry Pi and Arduino communicates on request-response mode. 
*Commands with debug flags doesn't return any response*
 * 0 - Start body check 
 * 1 - Stop body check
 * 2 - Stop body check
 * 3 - Start sanitizer
 * 4 - Start BPM
 * 5 - Detect arm
 * 6 - Detect arm loop
 * 7 - Detect finger
 * 8 - Detect finger loop
 * 9 - Reset
 * 10 - Forward oximeter stepper (DEBUG)
 * 11 - Backward oximeter stepper (DEBUG)
 * 12 - Forward cuff stepper (DEBUG)
 * 13 - Backward cuff stepper (DEBUG)
 * 14 - Oximeter lock
 * 15 - Oximeter release
 * 16 - Cuff lock
 * 17 - cuff release

### Acknowledgement
Special thanks to: <br/>
@vrano714 - For the MAX30102 to Raspberry Pi communication <br/>
@joergmlpts - For the Blood Pressure Monitor Bluetooth Communication
 
