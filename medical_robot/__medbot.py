from array import array
from .__user import User
from .__database import Database
from pyzbar.pyzbar import decode
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad
from Crypto.Cipher import AES
from base64 import b64encode
from base64 import b64decode
from escpos.printer import Usb
from datetime import datetime
from .__max30102 import MAX30102
from .__bp3gy12n import Microlife_BTLE
from serial import Serial
from .__utility import calc_hr_and_spo2, determine_pulse_rate_rating, determine_blood_pressure_rating, determine_blood_saturation_rating
from types import FunctionType
import cv2
import numpy
import speech_recognition
import pyttsx3
import time
import yaml

__all__ = ['Medbot']

########################################################
#                      Main Class                      #
########################################################

# This class requires a Database object to be initialized
# Commented lines is due to this code is being tested on a Windows Machine
# Would later remove if ported on Raspberry Pi
class Medbot:

    def __init__(self, database: Database, microphone_index: int = 2, camera_index: int = 0):
        '''
            Initialize a Medbot object \n
            Must pass in a `medical_robot.Database` object. Throws an Exception otherwise \n
            The `microphone_index` parameter can be overriden to select the microphone you
            want in case your system has multiple microphone source Default to `2` \n
            The `camera` index can also be set if multiple cameras are present. 
            Default to `0`
        '''
        try:
            self.database = database
        except:
            raise Exception('Initialization Error: parameter must be of type Database')
        self.__password = bytes('MedbotPRBPM' + '\0\0\0\0\0', 'utf-8')
        self.qrcode_scanner = cv2.VideoCapture(camera_index)
        self.oximeter = MAX30102()
        self.recognizer = speech_recognition.Recognizer()
        self.microphone_index = microphone_index
        self.microphone = speech_recognition.Microphone(device_index = self.microphone_index)
        self.voice_language = 'english'
        self.voice_gender = 'male'
        self.voice_rate = '100'
        self.voice_volume = 100
        self.speaker = pyttsx3.init()
        self.printer = Usb(0x28e9, 0x0289, 0, 0x81, 0x01)
        try:
            self.arduino = Serial('/dev/ttyACM0', 9600, timeout = 1)
        except:
            self.arduino = Serial('/dev/ttyACM1', 9600, timeout = 1)
        self.oximeter_samples = 1
        self.start_blood_pressure_monitor_delay = 45
        self.pulse_rate_from_bpm = False
        self.current_user = None,
        self.has_user = False
        self.finger_detected = False
        self.arm_detected = False
        self.body_check_started = False
        self.body_check_in_progress = False
        self.body_check_completed = False
        self.listening = False
        self.voice_prompt_enabled = True
        self.voice_command_enabled = True
        self.voice_response = ''
        self.current_reading = {
            'pulse_rate': None,
            'systolic': None,
            'diastolic': None,
            'blood_saturation': None
        }

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        voice_command_enabled = config['medbot']['settings']['voice_command']
        voice_prompt_enabled = config['medbot']['settings']['voice_prompt']
        speaker_id = config['medbot']['speaker']['id']
        speaker_language = config['medbot']['speaker']['language']
        speaker_rate = config['medbot']['speaker']['rate']
        speaker_volume = config['medbot']['speaker']['volume']
        speaker_gender = config['medbot']['speaker']['voice']
        microphone_index = config['medbot']['microphone']['index']
        if(type(voice_command_enabled) != bool):
            raise Exception('Voice command setting value error. Must be boolean')
        if(type(voice_prompt_enabled) != bool):
            raise Exception('Voice prompt setting value error. Must be boolean')
        self.voice_command_enabled = voice_command_enabled
        self.voice_prompt_enabled = voice_prompt_enabled
        self.set_speaker_properties(id = speaker_id, language = speaker_language, rate = speaker_rate, volume = speaker_volume, gender = speaker_gender)
        self.set_microphone(microphone_index)

    def reconnect(self):
        self.database.reconnect()

    def __decodeframe(self, image):
        '''
            Returns the decoded QR Code message
        '''
        trans_img = cv2.cvtColor(image,0)
        qrcode = decode(trans_img)
        for obj in qrcode:
            points = obj.polygon
            (x,y,w,h) = obj.rect
            pts = numpy.array(points, numpy.int32)
            pts = pts.reshape((-1, 1, 2))
            thickness = 2
            isClosed = True
            line_color = (0, 0, 255)
            cv2.polylines(image, [pts], isClosed, line_color, thickness)
            data = obj.data.decode("utf-8")
            return data

    def __encrypt(self, decrypted):
        '''
            Generates an encrypted text from the user's ID and password
        '''
        cipher = AES.new(self.__password,AES.MODE_ECB)
        encrypted = b64encode(cipher.encrypt(pad(decrypted.encode(),16))).decode()
        return encrypted

    def __decrypt(self, encrypted):
        '''
           Decrypts the decoded QR Code text that includes user's ID and password 
        '''
        cipher = AES.new(self.__password, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(b64decode(encrypted.encode())),16).decode()
        return decrypted

    def __verify_qrcode(self, qrdata):
        '''
            Check if QR Code is a valid Medbot QR Code
        '''
        if('Medbot' in qrdata):
            credentials = qrdata.split(':')
            id = credentials[1]
            password = credentials[2]
            return id, password
        else:
            raise Exception('QRCode is not a valid one')
 
    def __scan_qrcode(self):
        '''
            Opens an OpenCV window and scans QR Code   
        '''
        while True:
            ret, frame = self.qrcode_scanner.read()
            encrypted_data = self.__decodeframe(frame)
            cv2.imshow('Image', frame)
            cv2.waitKey(1)
            if(encrypted_data != None):
                decrypted_data = self.__decrypt(encrypted_data)
                break
        cv2.destroyAllWindows()
        return decrypted_data

    def login(self):
        '''
            Sets the current user based on the credentials found on database \n
            Return a User object upon success otherwise throws an Exception if
            credentials are incorrect \n
            Credential checkings are based on the database of the object
        '''
        qrdata = self.__scan_qrcode()
        id, password = self.__verify_qrcode(qrdata)
        user = User(id, password)
        success = self.database.verify(user)
        if(success):
            self.current_user = user
            self.has_user = True
            return user
        else:
            del user
            raise Exception('Invalid Credentials')

    def logout(self):
        '''
            Clears the current user and reset the object
        '''
        self.current_user.authenticated = False
        self.current_user = None
        self.has_user = False
        self.reset()

    def reset(self):
        '''
            Clears all body checks history and the cached current readings
        '''
        self.finger_detected = False
        self.arm_detected = False
        self.body_check_completed = False
        self.body_check_started = False
        self.body_check_in_progress = False
        self.voice_response = ''
        self.current_reading = {
            'pulse_rate': None,
            'systolic': None,
            'diastolic': None,
            'blood_saturation': None
        }

    def start_body_check(self):
        '''
            Send command to the Arduino to start body check. \n
            Also includes the body lock operation invoked in the Arduino
        '''
        # self.send_command(0)
        self.body_check_started = True
        self.body_check_in_progress = True

    def wait_body_check(self):
        '''
            Constantly listen to Arduino to send a body check completed response \n
            Returns `True` if body check is completed \n
            Throws an Exception if body check is not started
        '''
        if(self.body_check_in_progress):
            while(self.body_check_in_progress):
                response = self.get_arduino_response()
                if(response == '0'):
                    self.body_check_started = False
                    self.body_check_in_progress = False
                    self.body_check_completed = True
                    return True
                elif(response == '9'):
                    self.finger_detected = True
                elif(response == '8'):
                    self.arm_detected = True
        else:
            raise Exception('Body check is not started')

    def stop_body_check(self):
        '''
            Send command to the Arduino to immediately stop the body check
        '''
        self.send_command(1)
        self.body_check_in_progress = False
    
    def get_body_check_status(self):
        '''
            Returns a string indicating the body check status \n
            Possible returns:
            - `Not started`
            - `Ongoing`
            - `Completed`
        '''
        if(not self.body_check_started and not self.body_check_completed):
            return 'Not started'
        elif(self.body_check_in_progress):
            return 'Ongoing'
        elif(self.body_check_completed):
            return 'Completed'

    def body_release(self):
        '''
            Send command to the Arduino to commence body release operation \n
            Only available if body check is completed
        '''
        if(self.body_check_completed):
            self.send_command(2)
        else:
            raise Exception('Body check is not completed or not started yet')

    def get_arduino_response(self, return_string: bool = False, timeout: float = 0):
        '''
            Get the Arduino response if available \n
            If `return_string` is `true`, returns a
            formatted string, otherwise returns the raw
            arduino string response \n
            Timeout could be set to listen for response
            within the timeout duration. If `timeout` is
            set to 0, function will execute one time.
            Setting `timeout` to 0 may return empty string
            and recommended to call in a loop \n
            Possible response:
            - `0` Body Check Completed
            - `1` Sanitize Completed
        '''
        if(timeout <= 0):
            response = self.arduino.readline().decode('utf-8').rstrip()
        else:
            start_time = datetime.timestamp(datetime.now())
            now_time = datetime.timestamp(datetime.now())
            while((now_time - start_time) < timeout + 0.1):
                response = self.arduino.readline().decode('utf-8').rstrip()
                if(response != ''):
                    break
                now_time = datetime.timestamp(datetime.now())
            if((start_time - now_time) > timeout and response == ''):
                raise Exception('Timeout reached')
        if(return_string):
            if(response == '0'):
                return 'Body Check Completed'
            elif(response == '1'):
                return 'Sanitize Completed'
            else:
                return 'Ok'
        else:
            return response
    def send_command(self, command: int):
        '''
            Send command to arduino. 
            Can be used to explicitly invoke Arduino operation without calling specific functions \n
            Possible commands:
            - `0` Start Body Check
            - `1` Stop Body Check
            - `2` Body Release
            - `3` Start Sanitize
        '''
        commands = [0, 1, 2, 3, 9]
        if(command in commands):
            while True:
                self.arduino.write(bytes(str(command)+'\n','utf-8'))
                response = self.get_arduino_response()
                if(response == 'ok'):
                    break
                else:
                    print(response)
        else:
            raise Exception('Unknown command')

    def start_oximeter(self):
        '''
            Start the MAX30102 oximeter and gets 5 valid measurements and returns it's average \n
            Returns and cache pulse rate and blood saturation on default. If `pulse_rate_from_bpm
            is set to `True` returns only blood saturation
        '''
        pulse_rate_samples = []
        blood_saturation_samples = []
        sample_count = 1
        if(self.oximeter_samples == 1):
            while(len(pulse_rate_samples) == 0):
                red, ir = self.oximeter.read_sequential()
                pulse_rate, pulse_rate_valid, blood_saturation, blood_saturation_valid = calc_hr_and_spo2(ir[:100], red[:100])
                if(pulse_rate_valid and blood_saturation_valid):
                    pulse_rate_samples.append(pulse_rate)
                    blood_saturation_samples.append(blood_saturation)
                    print(str(pulse_rate) + str(blood_saturation))
        else:
            while(sample_count < self.oximeter_samples):
                red, ir = self.oximeter.read_sequential()
                pulse_rate, pulse_rate_valid, blood_saturation, blood_saturation_valid = calc_hr_and_spo2(ir[:100], red[:100])
                if(pulse_rate_valid and blood_saturation_valid and sample_count <= 10):
                    pulse_rate_samples.append(pulse_rate)
                    blood_saturation_samples.append(blood_saturation)
                    sample_count = sample_count + 1
                    print(str(pulse_rate) + str(blood_saturation))
        average_blood_saturation = round(sum(blood_saturation_samples)/len(blood_saturation_samples))
        self.current_reading['blood_saturation'] = average_blood_saturation
        print('Finished')
        if(not self.pulse_rate_from_bpm):
            average_pulse_rate = round(sum(pulse_rate_samples)/len(pulse_rate_samples))
            self.current_reading['pulse_rate'] = average_pulse_rate
            return average_pulse_rate, average_blood_saturation
        else:
            return average_blood_saturation

    def start_blood_pressure_monitor(self, retry_on_fail: bool = False):
        '''
            Send command to the Arduino to press the start button on the blood pressure monitor
            and fetches the last measurement \n
            Returns and cache systolic and diastolic if `pulse_rate_from_bpm` is `False
            otherwise returns and cache systolic, diastolic and pulse rate\n
            If `retry_on_fail` is `True`, the medbot will restart getting data
            from the bpm unit until a measurement is secured \n
            `Note:` if the you wants to get the pulse rate from the bpm, you need to set the
            `pulse_rate_from_bpm` property to true by direct or by calling
            `set_pulse_rate_from_bpm(True)`.
        '''
        print('starting')
        self.send_command(9)
        time.sleep(self.start_blood_pressure_monitor_delay)
        if(retry_on_fail):
            while True:
                try:
                    blood_pressure_monitor = Microlife_BTLE()
                    blood_pressure_monitor.bluetooth_communication(blood_pressure_monitor.patient_id_callback)                          
                    latest_measurement = blood_pressure_monitor.get_measurements()[-1]
                    break
                except:
                    print('Retrying')
        else:            
            blood_pressure_monitor = Microlife_BTLE()
            blood_pressure_monitor.bluetooth_communication(blood_pressure_monitor.patient_id_callback)                          
            latest_measurement = blood_pressure_monitor.get_measurements()[-1]
        systolic = latest_measurement[1]
        diastolic = latest_measurement[2]
        self.current_reading['systolic'] = systolic
        self.current_reading['diastolic'] = diastolic
        if(self.pulse_rate_from_bpm):
            pulse_rate = latest_measurement[3]
            self.current_reading['pulse_rate'] = pulse_rate
            return systolic, diastolic, pulse_rate
        else:
            return systolic, diastolic
    
    def interpret_pulse_rate(self, age, pulse_rate):
        '''
            Interpret the given pulse rate \n
            Possible return values: \n
            - `Low`
            - `Normal`
            - `High`
        '''
        pulse_rate_rating = determine_pulse_rate_rating(age, pulse_rate)
        return pulse_rate_rating

    def interpret_blood_pressure(self, systolic, diastolic):
        '''
            Interpret the blood pressure with the given systolic and diastolic \n
            Possible return values: \n
            - `Low`
            - `Normal`
            - `Elevated`
            - `High Stage 1`
            - `High Stage 2`
            - `Hypertensive Crisis`
        '''
        blood_pressure_rating = determine_blood_pressure_rating(systolic, diastolic)
        return blood_pressure_rating

    def interpret_blood_saturation(self, blood_saturation):
        '''
            Interpret the given blood_saturation \n
            Possible return values: \n
            - `Low`
            - `Normal`
            - `High`
        '''
        blood_saturation_rating = determine_blood_saturation_rating(blood_saturation)
        return blood_saturation_rating

    def interpret_readings(self, pulse_rate, systolic, diastolic, blood_saturation):
        '''
            Interpret the overall rating using the given parameters \n
            Possible return values: \n
            - `Low`
            - `Normal`
            - `High`
        '''
        pulse_rate_rating = determine_pulse_rate_rating(self.current_user.get_info()['age'],
                            pulse_rate, return_int = True)
        blood_pressure_rating = determine_blood_pressure_rating(systolic, diastolic,
                            return_int = True)
        blood_saturation_rating = determine_blood_saturation_rating(blood_saturation,
                            return_int = True)
        overall_rating = (pulse_rate_rating + blood_pressure_rating + blood_saturation_rating)/3
        if(overall_rating <= 1):
            rating = 'Low'
        elif(overall_rating <= 2):
            rating = 'Normal'
        elif(overall_rating <= 3):
            rating = 'High'
        return rating

    def interpret_current_readings(self):
        '''
            Interpret the overall rating using the cached reading \n
            Possible return values: \n
            - `Low`
            - `Normal`
            - `High`
        '''
        pulse_rate_rating = determine_pulse_rate_rating(self.current_user.get_info()['age'],
                            self.get_current_pulse_rate(), return_int = True)
        blood_pressure_rating = determine_blood_pressure_rating(self.get_current_systolic(),
                            self.get_current_diastolic(), return_int = True)
        blood_saturation_rating = determine_blood_saturation_rating(self.get_current_blood_saturation(),
                            return_int = True)
        overall_rating = (pulse_rate_rating + blood_pressure_rating + blood_saturation_rating)/3
        if(overall_rating <= 1):
            rating = 'Low'
        elif(overall_rating <= 2):
            rating = 'Normal'
        elif(overall_rating <= 3):
            rating = 'High'
        return rating

    def save_reading(self, pulse_rate: int, systolic: int, diastolic: int, blood_saturation: int, admin: bool = False, id: int = -1):
        '''
            Save readings to the database \n
            Can be used to directly store specific readings to the database \n
            Requires a logged user if `admin` is `False`, otherwise `id` should
            should be specified
        '''
        blood_pressure = diastolic + ((systolic - diastolic)/3)
        if(admin):
            user_id = id
        else:
            user_id = self.current_user.id
        try:
            self.database.insert_reading(user_id,pulse_rate, blood_saturation, blood_pressure, systolic, diastolic)
            return True
        except:
            return False

    def save_current_reading(self):
        '''
            Save the current cached readings to the database \n
            Does not reset the cached readings so multiple call to this
            function may lead to duplication in the database. \n
            Throws an exception if one of the indicators does not have
            value
        '''
        pulse_rate = self.current_reading['pulse_rate']
        systolic = self.current_reading['systolic']
        diastolic = self.current_reading['diastolic']
        blood_saturation = self.current_reading['blood_saturation']
        blood_pressure = diastolic + ((systolic - diastolic)/3)
        try:
            self.database.insert_reading(self.current_user.id,pulse_rate, blood_saturation, blood_pressure, systolic, diastolic)
            return True
        except:
            return False
        
    def print(self, content: str):
        '''
            Print some text on the thermal printer
        '''
        success = False
        while(not success):
            try:
                self.printer.text(content)
                self.printer.cut()
                success = True
            except:
                break
        return success

    def get_voice_input(self, accepted_answers: array or list = [], on_failure_callback: FunctionType = lambda:print('I cannot understand. Please try again')):
        '''
            Get voice stream from the microphone and tries to decode it\n
            Only process if `voice_command_enabled` property is `True` \n
            The `accepted_answers` parameter can be used to filter out any answers
            and immediately get voice stream if decoded text is not in the list \n
            The `on_failure_callback` will be called in case of Request or Value
            Error Exceptions. If `accepted_answers` was given, this function will
            also be called if the decoded text is not in the list
        '''
        if(not isinstance(on_failure_callback, FunctionType)):
            raise Exception('On Failure Callback must be a function')
        if(self.voice_command_enabled):
            self.listening = True
            text = ''
            while(self.listening):
                try:
                    with self.microphone:
                        self.recognizer.adjust_for_ambient_noise(self.microphone, duration = 1)
                        print('Speak now')
                        audio = self.recognizer.listen(self.microphone)
                        text = self.recognizer.recognize_google(audio)
                        text = text.lower()
                        if(len(accepted_answers) > 0):
                            if(text in accepted_answers):
                                self.listening = False
                                break
                            else:
                                print(text)
                                on_failure_callback()
                        else:
                            self.listening = False
                            break
                except Exception as e:
                    print(e)
            self.listening = False
            self.voice_response = text
            return text

    def speak(self, text: str):
        '''
            Converts text to speech \n
            Only available if `voice_prompt_enabled` property is `True`
        '''
        if(self.voice_prompt_enabled):
            if(self.speaker.isBusy()):
                self.speaker.stop()
            self.speaker.say(text)
            self.speaker.runAndWait()

    def set_speaker_properties(self, id: str = 'default', language: str = 'english', rate: int = 100, volume: float = 1.0, gender: str = 'male'):
        '''
            Set the speaker properties to change voice, rate or volume \n
            Voice option can only be `male` or `female`. Defaults to `male`  
        '''
        self.speaker.setProperty('id', id)
        self.set_voice_language(language)
        self.set_voice_gender(gender)
        self.set_voice_rate(rate)
        self.set_voice_volume(volume)

    def start_sanitizer(self):
        '''
            Send command to the Arduino to start sanitizing operation
        '''
        self.send_command(3)

    def get_current_user(self):
        '''
            Returns the current user as a User object
        '''
        try:
            if(self.current_user[0] is None):
                return None
        except:
            return self.current_user

    def get_current_reading(self):
        '''
            Return a dictionary of current cached readings
        '''
        return self.current_reading

    def get_current_pulse_rate(self):
        '''
            Return the current cached `pulse_rate`
        '''
        return self.current_reading['pulse_rate']
  
    def get_current_systolic(self):
        '''
            Return the current cached `systolic`
        '''
        return self.current_reading['systolic']

    def get_current_diastolic(self):
        '''
            Return the current cached `diastolic`
        '''
        return self.current_reading['diastolic']

    def get_current_blood_saturation(self):
        '''
            Return the current cached `blood_saturation`
        '''
        return self.current_reading['blood_saturation']

    def set_voice_prompt_enabled(self, value: bool):
        '''
            Sets the `voice_prompt_enabled` property \n
            Value can only be `boolean`
        '''
        if(type(value) is bool):
            self.voice_prompt_enabled = value
        else:
            raise Exception('Incorrect value')

    def set_voice_command_enabled(self, value: bool):
        '''
            Sets the `voice_command_enabled` property \n
            Value can only be `boolean`
        '''
        if(type(value) is bool):
            self.voice_command_enabled = value
        else:
            raise Exception('Incorrect value')

    def set_oximeter_sample(self, count: int):
        '''
            Sets the sample size of the oximeter. \n
            `count` parameter determines how many times
            the oximeter will try to get valid measurements
            before averaging the result
        '''
        self.oximeter_samples = count

    def set_pulse_rate_from_bp(self, value: bool):
        '''
            Set to `true` to get pulse rate from the
            blood pressure monitor instead of oximeter
        '''
        self.pulse_rate_from_bpm = value

    def get_voice_language(self):
        '''
            Return current voice prompt language
        '''
        return self.voice_language

    def get_voice_gender(self):
        '''
            Return the gender of the voice prompt
        '''
        return self.voice_gender
    
    def get_voice_volume(self):
        '''
            Return the current volume of the voice prompt
        '''
        return self.voice_volume

    def get_voice_rate(self):
        '''
            Return the current rate of the voice prompt
        '''
        return self.voice_rate
    
    def set_voice_language(self, language: str):
        '''
            Set the voice prompt language \n
            Valid languages: \n
            - `english`
            - `filipino`
        '''
        self.voice_language = language
        self.speaker.setProperty('language', language)
    
    def set_voice_gender(self, gender: str):
        '''
            Set the voice prompt gender \n
            Valid genders: \n
            - `male`
            - `female`
        '''
        self.voice_gender = gender
        voices = self.speaker.getProperty('voices')
        if(gender == 'female'):
            self.speaker.setProperty('voice', voices[1].id)
        else:
            self.speaker.setProperty('voice', voices[0].id)

    def set_voice_rate(self, rate: int):
        '''
            Set the voice prompt rate \n
        '''
        self.voice_rate = rate
        self.speaker.setProperty('rate', rate)

    def set_voice_volume(self, volume: int):
        '''
            Set the voice prompt volume in percentage \n
            `e.g. 90 = 90%`
        '''
        self.voice_volume = volume/100
        self.speaker.setProperty('volume', volume)
        
    def get_available_microphones(self):
        '''
            Returns a list of available microphone devices
        '''
        devices = self.microphone.list_microphone_names()
        return devices
    
    def set_microphone(self, index: int):
        '''
            Switches the current microphone to the given `index` \n
            To get available microphone devices use 
            `get_available_microphones` function
        '''
        self.microphone_index = index
        self.microphone = speech_recognition.Microphone(device_index = self.microphone_index)
    
    def get_microphone_index(self):
        '''
            Return the active microphone device index
        '''
        return self.microphone_index

    ########################################################
    #              Tkinter Support Functions               #
    ########################################################

    # Essential functions that remove the looping to prevent blocking on GUIs

    def get_qrcode_scanner_frame(self):
        '''
            Returns an image frame from an OpenCV instance
        '''
        if self.qrcode_scanner.isOpened():
            ret, frame = self.qrcode_scanner.read()
            if ret:
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    def login_tk(self, frame):
        '''
            Try to verify/login using a QR Code present in the frame object
        '''
        encrypted_data = self.__decodeframe(frame)
        decrypted_data = ''
        if(encrypted_data != None):
            decrypted_data = self.__decrypt(encrypted_data)
            id, password = self.__verify_qrcode(decrypted_data)
            user = User(id, password)
            success = self.database.verify(user)
            if(success):
                self.current_user = user
                self.has_user = True
                return True
            else:
                del user
                raise Exception('Invalid Credentials')

    ########################################################
    #                  Debugging Functions                 #
    ########################################################

    def body_check_complete(self):
        '''
            Forcefully invoke `body_check_completed` as `True`
        '''
        self.body_check_completed = True
        self.body_check_in_progress = False
    
    def debug_write(self, text):
        while True:
            self.arduino.write(bytes(text+'\n','utf-8'))
            response = self.test_read()
            print(response)
            if(response == 'ok'):
                break
        

    def debug_read(self):
        response = self.arduino.read_until('\n').decode('utf-8').rstrip()
        return response

    def debug_bp(self):
        blood_pressure_monitor = Microlife_BTLE()
        blood_pressure_monitor.bluetooth_communication(blood_pressure_monitor.patient_id_callback)
        latest_measurement = blood_pressure_monitor.get_measurements()[-1]
        print(latest_measurement)

    def debug_save(self):
        import mysql.connector
        from datetime import datetime
        connection = mysql.connector.connect(host = 'sql624.main-hosting.eu',
                            database = 'u234071176_medbot',
                            user = 'u234071176_medbot',
                            password = 'Medbot@2022'
                        )
        cursor = connection.cursor()
        now = datetime.now()
        date_now = now.strftime('%Y-%m-%d %H:%M:%S')
        query = '''INSERT INTO readings(user_id,pulse_rate,blood_saturation,blood_pressure,systolic,diastolic,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
        values = (1,100,99,2,120,80,date_now,date_now)
        cursor.execute(query, values)
        connection.commit()