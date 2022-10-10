# Medbot: Pulse Rate and Blood Pressure Monitor

The Medbot functionalities
- Measure pulse rate, blood pressure and blood saturation
- Print results in thermal paper
- Voice commands and voice prompts
- Arm and finger placement detection
- Sanitize

## Run
To use the Medbot class, we first need to create a Database class instance to store users and readings information

### Database Class 
To create an instance of database class, pass in the `host,database,user,password` as args
```python
from database import Database
database = Database(host,database,user,password)
```
The database class uses python MySQL connector

#### Users table
| id | name | birthday | gender | phone_number | address | email | bio | profile_picture_path | email_verified_at | password | type | remember_token | created_at | updated_at |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|unique-auto increment| string | datetime | string | string | string | string-unique | string | string | string | hash | string | string | datetime | datetime |

#### Readings table
| id | user_id| pulse_rate | blood_saturation | blood_pressure | systolic | diastolic | created_at | updated_at |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|unique-auto increment| foreign key - users table | int | int | int | int | int | datetime | datetime |

### Medbot Class
#### Initialize
The Medbot class uses database to store readings. To initialze the Medbot class, an instance of Database class is required.
```python
from medbot import Medbot
medbot = Medbot(database)
```

#### Login
It is required to use the `login` method before doing anything else. The `login` uses the Pi Camera to scan for the user qrcode. Upon success it returns an instance of User class that contains the user's information found in the database.
```python
user = medbot.login()
```

#### Measure pulse rate and blood saturation
To measure pulse rate and blood saturation, simple call the `start_oximeter` method. This method gets 10 valid measurement and calculates and return its respective average.
```python
pulse_rate, blood_saturation = medbot.start_oximeter()
```

#### Saving readings to database
The `save` method inserts a row at the readings table of the `medbot.database` attribute. To use `save` method, simply pass in `pulse_rate, systolic, diastolic, blood_saturation` as arguments. The `blood_pressure` value in the readings table is calculated based on the `systolic` and `diastolic` value by `blood_pressure = diastolic + ((systolic - diastolic)/3)`.
```python
medbot.save_reading(self,pulse_rate, systolic, diastolic, blood_saturation)
```

#### Printing results
The `print_results` method uses the thermal printer connected via USB and uses the [python-ecspos](https://pypi.org/project/python-escpos/) library to do this. You may want to configure the printer port before using. By default, the thermal printer is set `Usb(0x28e9, 0x0289, 0, 0x81, 0x01)`, however you may change this to suit your needs. Simply modify the `medbot.printer` attribute to do this. You may again refer to the [python-ecspos](https://python-escpos.readthedocs.io/en/latest/user/printers.html) docs for this.
```python
from escpos.printer import Usb
medbot.printer = Usb(idVendor, idProduct, iInterface, ep_in, ep_out)
```
To actually print result, call the `print_results(content, **settings)` method where in the content arg is the string you want to print and the settings kwargs is the text properties of the printer you wish to use. You can refer to the [python-ecspos](https://python-escpos.readthedocs.io/en/latest/user/methods.html) `set` method for all the possible properties
```python
medbot.print_results(content, **settings)
```

#### Getting voice inputs
In order to use the voice recognition method, you may need to select the microphone device you wish to use. You can get the list of devices you may wish to use by running. By default, the device index is set to 2.
```python
import speech_recognition
speech_recognition.Microphone.list_microphone_names()
```
After selecting which device you need to use simple, modify the `medbot.microphone` attribute passing in the index of your device
```python
import speech_recognition
medbot.microphone = speech_recognition.Microphone(device_index=2)
```
The medbot utilizes the [speech_recognition](https://pypi.org/project/SpeechRecognition/) library to get voice inputs. The `get_voice_input` method returns the converted text from speech. Optionally, you can also include an array as argument to filter the accepted answer you only wish to use
```python
voice_input = medbot.get_voice_input(*accepted_answers)
```

<!--
#### Using voice prompt
The voice prompt uses the [pyttsx3](https://pypi.org/project/pyttsx3/) library to convert text to audio. To use this, simply call the `speak(text)` method, passing in the the string you wish to be converted to speech
```python
medbot.speak(text)
```
You may also set the voice property of the `medbot.speaker` attribute. By default the properties are set to `rate=100, volume=1.0, voice='male'`, however you may change it with the `set_speaker_properties` method.
```python
medbot.set_speaker_properties(rate=125, volume=90, voice='female')
```
>Note: the you can only use 'male' or 'female' as value for the voice property. Any other value will use the default male value. Simply calling the said method will revert the speaker's property to default

#### Arm and finger placement check
The medbot's Arduino is interfaced via USB and you may need to configure the path before using it. By default the Arduino port is set to `/dev/ttyACM0` you can check your Arduino's port by running
```
dmesg | grep "tty"
```
You may also need to add your user to the dialout group incase of permission denied error
```
sudo adduser your_username dialout
```
Then change the `medbot.arduino` attribute to your port. You may refer to the [pyserial](https://pypi.org/project/pyserial/) docs for the possible arguments for the Serial class
```python
import serial
medbot.arduino = serial.Serial('/dev/ttyACM0', 9600, timeout = 1)
```
The medbot's Arduino mainly handles this operation but you can also communicate with the Arduino to send commands to commence the body position check. To start the operation, call the `start_body_position_check` method. The Pi will send command to the Arduino to start the operation. Then listen for the Arduino's response that the operation is complete
```python
medbot.start_body_position_check()
body_check_completed = wait_body_position_check()
```
It is possible to stop the operation by calling `stop_body_position_check()` method. You can also get the operation status by using the `get_body_position_check_status()` which returns `True` if the operation is in progress otherwise `False` if not
-->

#### Sanitize
The `sanitize` method tells the Arduino to commence the operation. Simply call the `sanitize()` method to do this
```python
medbot.sanitize()
```

## To-do
- [ ] Add method for measuring blood pressure
- [ ] Add communication to Arduino
- [ ] Add GUI

## Components
The medbot uses different components to achieve its functionality such as:
- Raspberry Pi 4B
- Arduino
- MAX30102 for measuring pulse rate and blood saturation, based on [vrano714/max30102-tutorial-raspberrypi](https://github.com/vrano714/max30102-tutorial-raspberrypi)
- Pi Camera
- Thermal printer
- Microphone
- Speaker
- Sanitizer
