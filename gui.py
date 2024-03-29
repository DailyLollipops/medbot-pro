from tkinter import Image, messagebox
from PIL import ImageTk,Image
from threading import Thread
from datetime import datetime
from tkinter import ttk
from itertools import count, cycle
import urllib.request
import medical_robot
import tkinter
import time
import yaml
import os

dirname = os.path.dirname(__file__)
medbot = None

def show_message(window, title, message, timeout = 0):
    messagebox_container = tkinter.Toplevel(window)
    messagebox_container.withdraw()
    if(timeout > 0):
        messagebox_container.after(timeout, messagebox_container.destroy)
    messagebox.showinfo(title, message, parent = messagebox_container)

class MedbotGUIStartScreen:
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.geometry('300x120')
        self.window.title('Starting Medbot')
        self.internet_connected = False
        self.configuration_checked = False
        self.medbot_initialized = False
        self.progressbar = ttk.Progressbar(
            self.window,
            orient='horizontal',
            mode='determinate',
            length=280
        )
        self.progressbar.grid(column=0, row=0, columnspan=2, padx=10, pady=20)

        self.message_label = ttk.Label(self.window, text='Medbot Starting...')
        self.message_label.grid(column=0, row=1, columnspan=2)

        self.update()
        self.window.mainloop()

    def update(self):
        if(not self.internet_connected):
            if(self.check_internet()):
                self.progressbar['value'] += 33
                self.internet_connected = True
                self.message_label.config(text='Checking configurations...')
            else:
                messagebox.askretrycancel('No internet connection','No internet connection detected!')
        elif(self.internet_connected and not self.configuration_checked):
            self.progressbar['value'] += 33
            self.message_label.config(text='Medbot Initializing...')
            self.configuration_checked = True
        elif(self.configuration_checked and not self.medbot_initialized):
            self.initialize_medbot()
            self.progressbar['value'] += 33
            self.message_label.config(text='Finishing Startup...')
        elif(self.medbot_initialized):
            #MedbotGUI()
            self.window.destroy()
            SplashScreen()
        self.window.after(15, self.update)

    def check_internet(self):
        try:
            urllib.request.urlopen('http://google.com')
            return True
        except:
            return False

    def initialize_medbot(self):
        global medbot
        while(not self.medbot_initialized):
            try:
                with open(os.path.join(dirname, 'config.yml'), 'r') as file:
                    config = yaml.safe_load(file)
                database_host = config['medbot']['database']['host']
                database = config['medbot']['database']['database']
                database_user = config['medbot']['database']['user']
                database_password = config['medbot']['database']['password']
                database = medical_robot.Database(database_host,database,database_user,database_password)
                medbot = medical_robot.Medbot(database, microphone_index=1)
                medbot.load_config(os.path.join(dirname, 'config.yml'))
                medbot.pulse_rate_from_bpm = True
                self.medbot_initialized = True
            except:
                self.message_label.config(text='Retrying')

class SplashScreen():
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title('Splash Screen')
        self.splash = Splash(self.window)
        self.splash.pack()
        self.splash.load(os.path.join(dirname, 'images/splash.gif'))
        self.window.mainloop()

class Splash(tkinter.Label):
    """
    A Label that displays images, and plays them if they are gifs
    :im: A PIL Image instance or a string filename
    """
    def load(self, im):
        if isinstance(im, str):
            im = Image.open(im)
        frames = []
 
        try:
            for i in count(1):
                frames.append(ImageTk.PhotoImage(im.copy()))
                im.seek(i)
        except EOFError:
            pass
        self.frames = cycle(frames)
        self.counter = 1
        try:
            self.delay = im.info['duration']
        except:
            self.delay = 100
 
        if len(frames) == 1:
            self.config(image=next(self.frames))
        else:
            self.next_frame()
 
    def unload(self):
        self.config(image=None)
        self.frames = None
 
    def next_frame(self):
        if self.frames:
            self.counter += 1
            if self.counter >= 80:
                global medbot
                self.master.destroy()
                MedbotGUI(medbot)
            else:
                self.config(image=next(self.frames))
                self.after(self.delay, self.next_frame)

class MedbotGUI:
    def __init__(self, medbot: medical_robot.Medbot):
        self.window = tkinter.Tk()
        self.window.title('Login Window')
        self.window.geometry('800x440')
        logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/logo.png')))
        self.window.iconphoto(False, logo)
        self.window.configure(background = 'white')
        self.medbot = medbot
        self.logged_in = False
        self.just_logged_out = False
        self.first_time = True

        self.placeholder = tkinter.Canvas(self.window, width = 380, height = 400)
        self.qrcode = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/qrcode.png')).resize((256,260)))
        self.placeholder.create_text(190, 65, text = 'Med-bot: Pulse Rate\nand\nBlood Pressure Monitor',
                            anchor = tkinter.CENTER, font = ('Lucida',14,'bold'), justify = 'center')
        self.placeholder.create_image(65, 90, image = self.qrcode, anchor = tkinter.NW)
        self.placeholder.create_text(180, 380, text = 'Place your QR Code\nwithin the frame to Login',
                            anchor = tkinter.CENTER, font = ('Lucida',14,'bold'), justify = 'center')
        self.placeholder.configure(background = 'white', highlightbackground = 'white' )
        self.placeholder.place(x = 0, y = 0)

        self.settings_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/settings.png')).resize((20,20)))
        self.settings_button = tkinter.Button(self.window, text = ' Settings', image = self.settings_logo,
                            compound = tkinter.LEFT, command = self.open_settings, background = 'white',
                            borderwidth = 0, activebackground = '#abdbe3', activeforeground = 'white',
                            font = ('Lucida', 10))
        self.settings_button.place(x = 5, y = 5)

        self.qrcode_scanner_frame = tkinter.Canvas(self.window, width = 400, height = 400)
        self.qrcode_scanner_frame.place(x = 390, y = 10)
        self.update()
        self.window.mainloop()

    def update(self):
        if(not self.logged_in):
            ret, self.frame = self.medbot.get_qrcode_scanner_frame()
            if ret:
                self.photo = ImageTk.PhotoImage(image = Image.fromarray(self.frame))
                self.qrcode_scanner_frame.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
                try:
                    self.logged_in = self.medbot.login_tk(self.frame)
                except Exception as e:
                    show_message(self.window, 'Login Failed', 'Invalid Credentials', timeout = 1500)
                    print(e)
                if(self.logged_in):
                    show_message(self.window, 'Login Successfully', 
                                        'Welcome back, ' + self.medbot.current_user.name + ' !',
                                        timeout = 2000)
                    MedbotGUIMain(self, self.window, self.medbot)
                    # self.qrcode_scanner_frame.create_image(0, 0, image = self.blank_image, anchor = tkinter.NW)
        else:
            ret, self.frame = self.medbot.get_qrcode_scanner_frame()
        if(self.just_logged_out):
            self.logged_in = False
            self.just_logged_out = False
        self.window.after(15, self.update)

    def open_settings(self):
        MedbotGUISettings(self.window, self.medbot)

class MedbotGUISettings:
    def __init__(self, window: tkinter.Tk, medbot: medical_robot.Medbot):
        self.medbot = medbot
        self.window = tkinter.Toplevel(window)
        self.window.title('Settings')
        self.window.geometry('400x300')
        self.window.configure(background = 'white')
        self.window.grab_set()

        self.settings_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/settings.png')).resize((24,24)))
        self.title_label = tkinter.Label(self.window, text = ' Settings', image = self.settings_logo,
                            compound = tkinter.LEFT, font = ('Lucida', 16), justify = 'center',
                            background = 'white')
        self.title_label.place(x = 150, y = 10)

        self.voice_prompt_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/speaker.png')).resize((16,16)))
        self.voice_prompt_label = tkinter.Label(self.window, text = ' Voice Prompt', font = ('Lucida', 11),
                            background = 'white', image = self.voice_prompt_logo, compound = tkinter. LEFT)
        self.voice_prompt_label.place(x = 50, y = 65)

        self.voice_prompt_enabled = tkinter.StringVar()
        self.voice_prompt_enabled.set("Enabled")
        self.voice_prompt_dropdown = ttk.Combobox(self.window, textvariable = self.voice_prompt_enabled)
        self.voice_prompt_dropdown['values'] = ['Enabled', 'Disabled']
        self.voice_prompt_dropdown['state'] = 'readonly'
        self.voice_prompt_dropdown.place(x = 225, y = 65)

        self.voice_language_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/language.png')).resize((16,16)))
        self.voice_language_label = tkinter.Label(self.window, text = ' Language', font = ('Lucida',11),
                            background = 'white', image = self.voice_language_logo, compound = tkinter.LEFT)
        self.voice_language_label.place(x = 50, y = 95)

        self.voice_language = tkinter.StringVar()
        self.voice_language.set('english')
        self.voice_language_dropdown = ttk.Combobox(self.window, textvariable = self.voice_language)
        self.voice_language_dropdown['values'] = ['English', 'Filipino']
        self.voice_language_dropdown['state'] = 'readonly'
        self.voice_language_dropdown.place(x = 225, y = 95)

        self.voice_gender_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/gender.png')).resize((16,16)))
        self.voice_gender_label = tkinter.Label(self.window, text = ' Gender', font = ('Lucida',11),
                            background = 'white', image = self.voice_gender_logo, compound = tkinter.LEFT)
        self.voice_gender_label.place(x = 50, y = 125)

        self.voice_gender = tkinter.StringVar()
        self.voice_gender.set('male')
        self.voice_gender_dropdown = ttk.Combobox(self.window, textvariable = self.voice_gender)
        self.voice_gender_dropdown['values'] = ['Male', 'Female']
        self.voice_gender_dropdown['state'] = 'readonly'
        self.voice_gender_dropdown.place(x = 225, y = 125)

        self.voice_volume_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/volume.png')).resize((16,16)))
        self.voice_volume_label = tkinter.Label(self.window, text = ' Volume', font = ('Lucida',11),
                            background = 'white', image = self.voice_volume_logo, compound = tkinter.LEFT)
        self.voice_volume_label.place(x = 50, y = 160)

        self.voice_volume = tkinter.IntVar()
        self.voice_volume_slider = tkinter.Scale(self.window, from_ = 0, to = 100, orient = 'horizontal', 
                            variable = self.voice_volume, background = 'white', troughcolor = 'white',
                            length = 135, highlightbackground= 'white', width = 10,
                            command = self.set_voice_volume)
        self.voice_volume_slider.place(x = 225, y = 150)

        self.voice_rate_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/rate.png')).resize((16,16)))
        self.voice_rate_label = tkinter.Label(self.window, text = ' Voice Rate', font = ('Lucida',11),
                            background = 'white', image = self.voice_rate_logo, compound = tkinter.LEFT)
        self.voice_rate_label.place(x = 50, y = 200)

        self.voice_rate = tkinter.IntVar()
        self.voice_rate_slider = tkinter.Scale(self.window, from_ = 0, to = 150, orient = 'horizontal', 
                            variable = self.voice_rate, background = 'white', troughcolor = 'white',
                            length = 135, highlightbackground= 'white', width = 10,
                            command = self.set_voice_rate)
        self.voice_rate_slider.place(x = 225, y = 190)

        self.voice_command_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/microphone.png')).resize((16,16)))
        self.voice_command_label = tkinter.Label(self.window, text = ' Voice Command', font = ('Lucida', 11),
                            background = 'white', image = self.voice_command_logo, compound = tkinter.LEFT)  
        self.voice_command_label.place(x = 50, y = 240)

        self.voice_command_enabled = tkinter.StringVar()
        self.voice_command_enabled.set("Enabled")
        self.voice_command_dropdown = ttk.Combobox(self.window, textvariable = self.voice_command_enabled)
        self.voice_command_dropdown['values'] = ['Enabled', 'Disabled']
        self.voice_command_dropdown['state'] = 'readonly'
        self.voice_command_dropdown.place(x = 225, y = 240)

        self.microphone_device_logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/microphone2.png')).resize((16,16)))
        self.microphone_device_label = tkinter.Label(self.window, text = ' Microphone Device', font = ('Lucida',11),
                            background = 'white', image = self.microphone_device_logo, compound = tkinter.LEFT)
        self.microphone_device_label.place(x = 50, y = 270)

        self.microphone_device = tkinter.IntVar()
        self.microphone_device_dropdown = ttk.Combobox(self.window, textvariable = self.microphone_device)
        self.microphone_device_dropdown['values'] = [device for device in self.medbot.get_available_microphones()]
        self.microphone_device_dropdown['state'] = 'readonly'
        self.microphone_device_dropdown.place(x = 225, y = 270)

        self.load_config()
        self.voice_prompt_dropdown.bind('<<ComboboxSelected>>', self.set_voice_prompt)
        self.voice_language_dropdown.bind('<<ComboboxSelected>>', self.set_voice_language)
        self.voice_gender_dropdown.bind('<<ComboboxSelected>>', self.set_voice_gender)
        self.voice_command_dropdown.bind('<<ComboboxSelected>>', self.set_voice_command)
        self.microphone_device_dropdown.bind('<<ComboboxSelected>>', self.set_microphone_index)

    def load_config(self):
        with open(os.path.join(dirname, 'config.yml'), 'r') as file:
            config = yaml.safe_load(file)
        voice_command_enabled = config['medbot']['settings']['voice_command']
        voice_prompt_enabled = config['medbot']['settings']['voice_prompt']
        speaker_language = config['medbot']['speaker']['language']
        speaker_rate = config['medbot']['speaker']['rate']
        speaker_volume = config['medbot']['speaker']['volume']
        speaker_gender = config['medbot']['speaker']['gender']
        microphone_index = config['medbot']['microphone']['index']
        if(type(voice_command_enabled) != bool):
            raise Exception('Voice command setting value error. Must be boolean')
        if(type(voice_prompt_enabled) != bool):
            raise Exception('Voice prompt setting value error. Must be boolean')
        if(voice_prompt_enabled):
            voice_prompt = 'Enabled'
        else:
            voice_prompt = 'Disabled'
        self.voice_command_enabled.set(voice_prompt)
        self.voice_language.set(speaker_language.upper())
        self.voice_gender.set(speaker_gender.upper())
        self.voice_rate.set(speaker_rate)
        self.voice_volume.set(speaker_volume)
        if(voice_command_enabled):
            voice_command = 'Enabled'
        else:
            voice_command = 'Disabled'
        self.voice_command_enabled.set(voice_command)
        self.microphone_device.set(microphone_index)

    def set_voice_prompt(self):
        temp = self.voice_prompt_enabled.get()
        if(temp == 'Enabled'):
            value = True
            self.voice_language_dropdown['state'] = 'readonly'
            self.voice_gender_dropdown['state'] = 'readonly'
            self.voice_rate_slider['state'] = 'normal'
            self.voice_volume_slider['state'] = 'normal'
        else:
            value = False
            self.voice_language_dropdown['state'] = 'disabled'
            self.voice_gender_dropdown['state'] = 'disabled'
            self.voice_rate_slider['state'] = 'disabled'
            self.voice_volume_slider['state'] = 'disabled'
        self.medbot.set_voice_prompt_enabled(value)
        self.save_config('settings', 'voice_prompt', value)
        print('Voice prompt set to ' + str(value))

    def set_voice_language(self):
        language = self.voice_language.get().lower()
        self.medbot.set_voice_language(language)
        self.save_config('speaker', 'language', language)

    def set_voice_gender(self):
        gender = self.voice_gender.get().lower()
        self.medbot.set_voice_gender(gender)
        self.save_config('speaker', 'gender', gender)

    def set_voice_rate(self, event):
        rate = self.voice_rate.get()
        self.medbot.set_voice_rate(rate)
        self.save_config('speaker', 'rate', rate)

    def set_voice_volume(self, event):
        volume = self.voice_volume.get()
        self.medbot.set_voice_volume(volume)
        self.save_config('speaker', 'volume', volume)
        
    def set_voice_command(self):
        temp = self.voice_command_enabled.get()
        if(temp == 'Enabled'):
            value = True
            self.microphone_device_dropdown['state'] = 'readonly'
        else:
            value = False
            self.microphone_device_dropdown['state'] = 'disabled'
        self.medbot.set_voice_command_enabled(value)
        self.save_config('settings', 'voice_command', value)
        print('Voice command set to ' + str(value))

    def set_microphone_index(self):
        index = self.microphone_device.get()
        self.medbot.set_microphone(index)
        self.save_config('microphone', 'index', index)

    def save_config(self, parent, key, value):
        with open(os.path.join(dirname, 'config.yml'), 'r') as file:
            config = yaml.safe_load(file)
        config['medbot'][parent][key] = value
        with open(os.path.join(dirname, 'config.yml'), 'w') as file:
            yaml.dump(config, file)

class MedbotGUIMain():
    def __init__(self, root: MedbotGUI, master: tkinter.Tk, medbot: medical_robot.Medbot):
        self.root = root
        self.master = master
        self.master.withdraw()
        self.window = tkinter.Toplevel(self.master)
        self.medbot = medbot
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.title('Main Window')
        self.window.geometry('800x440')
        logo = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/logo.png')))
        self.window.iconphoto(False, logo)
        self.window.configure(background = 'white')

        self.window_launched = False
        self.wait_thread_started = False
        self.operation_started = False
        self.operation_completed = False
        self.animation_timer = 1
        self.sanitizer_finished = False
        self.finger_detected = False
        self.arm_detected = False
        self.detection_started = False
        self.detection_finished = False
        self.body_locked = False
        self.waiting_thread = Thread(target=self.medbot.wait_body_check)
        self.oximeter_thread = Thread(target = self.medbot.start_oximeter)
        self.bp_finished = False
        self.bp_thread = Thread(target = self.medbot.start_blood_pressure_monitor)
        self.bp_logged = False
        self.voice_prompt_started = False
        self.oximeter_thread_started = False
        self.bp_thread_started = False
        self.readings_saved = False
        self.printer_prompted = False
        self.printer_responded = False
        self.printer_choice_displayed = False
        self.printer_choice_thread_started = False
        self.window_completed = False
        self.speaker_refreshed = False

        self.transparent_icon = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/transparent.png')).resize((16,16)))

        self.finger_notification_holder = tkinter.Canvas(self.window, width = 24, height = 24)
        self.finger_notification_holder.configure(background = 'white')
        self.finger_icon = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/finger.png')).resize((16,16)))
        self.finger_notification_holder.create_image(4, 4, image = self.finger_icon, anchor = tkinter.NW)
        self.finger_notification_holder.place(x = 695, y = 2.5)

        self.arm_notification_holder = tkinter.Canvas(self.window, width = 24, height = 24)
        self.arm_notification_holder.configure(background = 'white')
        self.arm_icon = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/arm.png')).resize((16,16)))
        self.arm_notification_holder.create_image(4, 4, image = self.arm_icon, anchor = tkinter.NW)
        self.arm_notification_holder.place(x = 725, y = 2.5)

        self.display = tkinter.Canvas(self.window, width = 700, height = 220)
        self.display_text = self.display.create_text(350, 110, text = 'Initializing Please Wait',
                            anchor = tkinter.CENTER, font = ('Lucida', 20), justify = 'center')
        self.display.place(x = 50, y = 30)

        self.pulse_rate_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.pulse_rate_icon = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/pulse_rate.png')).resize((64,64)))
        self.pulse_rate_holder.create_image(10, 18, image = self.pulse_rate_icon, anchor = tkinter.NW)
        self.pulse_rate_holder.create_text(140, 40, text = 'Pulse Rate', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.pulse_rate_text = self.pulse_rate_holder.create_text(135, 65, text = '-- bpm',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.pulse_rate_holder.configure(background = '#f5f7fa')
        self.pulse_rate_holder.place(x = 50, y = 255)

        self.blood_pressure_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.blood_pressure_icon = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/blood_pressure.png')).resize((64,64)))
        self.blood_pressure_holder.create_image(10, 18, image = self.blood_pressure_icon, anchor = tkinter.NW)
        self.blood_pressure_holder.create_text(145, 40, text = 'Blood Pressure', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.blood_pressure_text = self.blood_pressure_holder.create_text(140, 65, text = '--/-- mmHg',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.blood_pressure_holder.configure(background = '#f5f7fa')
        self.blood_pressure_holder.place(x = 290, y = 255)

        self.blood_saturation_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.blood_saturation_icon = ImageTk.PhotoImage(Image.open(os.path.join(dirname, 'images/finger.png')).resize((64,64)))
        self.blood_saturation_holder.create_image(5, 18, image = self.blood_saturation_icon, anchor = tkinter.NW)
        self.blood_saturation_holder.create_text(140, 40, text = 'Blood Saturation', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.blood_saturation_text = self.blood_saturation_holder.create_text(130, 65, text = '-- %',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.blood_saturation_holder.configure(background = '#f5f7fa')
        self.blood_saturation_holder.place(x = 530, y = 255)

        self.log_holder = tkinter.Text(self.window, height = 3, width = 85)
        self.log('Loginned Successfully')
        self.log_holder.place(x = 57.5, y = 360)

        self.load_config()
        self.window.after(3000, self.update)

    def update(self):
        # Check if sanitizer hasn't start (initialize)
        if(not self.sanitizer_finished and not self.window_completed and self.window_launched):
            self.display.itemconfigure(self.display_text, text = 'Sanitizing...')
            if(not self.voice_prompt_started and self.speaker_refreshed):
                self.voice_prompt_started = True
                self.medbot.speak('Sanitizing. Place your hand in front the sanitizer')
                self.speaker_refreshed = False
                # voice_prompt = Thread(target=self.medbot.speak, args=(self.body_check_prompt_voice,))
                # voice_prompt.start()
                # self.medbot.start_body_check()
                # self.medbot.body_check_complete()
                self.log('Sanitizing...')
                self.medbot.start_sanitizer()
                self.sanitizer_finished = True
                self.speaker_refreshed = False
            else:
                self.speaker_refreshed = True

        # Check if sanitizing has finished
        elif(self.sanitizer_finished and not self.detection_started):
            time.sleep(2)
            self.display.itemconfigure(self.display_text, text = 'Starting Body Check')
            if(self.speaker_refreshed):
                self.medbot.speak(self.body_check_prompt_voice)
                self.detection_started = True
                self.speaker_refreshed = False
            else:
                self.speaker_refreshed = True
        
        # Check if arm and finger detection is in progress
        # Continously detect arm and finger
        elif(self.detection_started and not self.detection_finished and self.voice_prompt_started):
            if(not self.medbot.arm_detected):
                time.sleep(0.5)
                if(self.medbot.detect_arm()):
                    self.log('Arm Detected')
            elif(not self.medbot.finger_detected):
                time.sleep(0.5)
                if(self.medbot.detect_finger()):
                    self.log('Finger Detected')
            if(self.medbot.finger_detected and self.medbot.arm_detected):
                self.log('Body Check Complete')
                self.detection_finished = True
            if(self.animation_timer == 1):
                self.display.itemconfigure(self.display_text, text = self.body_check_prompt_text + ' .')
                self.animation_timer = 2
            elif(self.animation_timer == 2):
                self.display.itemconfigure(self.display_text, text = self.body_check_prompt_text + '  .')
                self.animation_timer = 3
            elif(self.animation_timer == 3):
                self.display.itemconfigure(self.display_text, text = self.body_check_prompt_text + '   .')
                self.animation_timer = 0
            elif(self.animation_timer == 0):
                self.display.itemconfigure(self.display_text, text = self.body_check_prompt_text + '.')
                self.animation_timer = 1
            if(not self.wait_thread_started):
                self.wait_thread_started = True
                # self.waiting_thread.start()
            # if(not self.medbot.finger_detected and self.animation_timer <= 1):
            #     self.finger_notification_holder.create_image(4, 4, image = self.finger_icon, anchor = tkinter.NW)
            # elif(not self.medbot.finger_detected and self.animation_timer > 1):
            #     self.finger_notification_holder.create_image(4, 4, image = self.transparent_icon, anchor = tkinter.NW)
            # elif(self.medbot.finger_detected and not self.finger_notification_fixed):
            #     self.finger_notification_holder.create_image(4, 4, image = self.finger_icon, anchor = tkinter.NW)
            # if(not self.medbot.arm_detected and self.animation_timer <= 1):
            #     self.arm_notification_holder.create_image(4, 4, image = self.arm_icon, anchor = tkinter.NW)
            # elif(not self.medbot.arm_detected and self.animation_timer > 1):
            #     self.arm_notification_holder.create_image(4, 4, image = self.transparent_icon, anchor = tkinter.NW)
            # elif(self.medbot.arm_detected and not self.arm_notification_fixed):
            #     self.arm_notification_holder.create_image(4, 4, image = self.arm_icon, anchor = tkinter.NW)
            time.sleep(0.5)

        # Check if arm and finger detection is complete
        # Lock arm and finger
        elif(self.detection_finished and not self.body_locked):
            self.log('Locking Oximeter...')
            self.medbot.lock_oximeter()
            self.log('Oximeter Locked')
            self.log('Locking Arm Cuff...')
            try:
                self.medbot.lock_cuff()
                self.log('Arm Cuff Locked')
            except:
                self.log('Operation Interrupted, Restarting...')
                self.reset()
            self.body_locked = True

        # Check if body is locked
        # Starts the oximeter and bp thread
        elif(self.body_locked and not self.operation_started and not self.operation_completed):
            self.display.itemconfigure(self.display_text, text = self.in_progress_prompt_text)
            if(self.speaker_refreshed):
                self.medbot.speak(self.in_progress_prompt_voice)
                # voice_prompt = Thread(target=self.medbot.speak, args=(self.in_progress_prompt_voice,))
                # voice_prompt.start()
                self.operation_started = True
                if(not self.oximeter_thread_started):
                    self.oximeter_thread.start()
                    self.oximeter_thread_started = True
                    self.log('Oximeter Started')
                    self.bp_thread_started = True
                    self.log('Blood Pressure Monitor Started')
                    self.medbot.start_blood_pressure_monitor(retry_on_fail=True)
                    self.bp_finished = True
                if(self.oximeter_thread_started and not self.oximeter_thread.is_alive() \
                    and self.bp_thread_started and self.bp_finished):
                    self.log(f'Got Pulse Rate: {self.medbot.get_current_pulse_rate()}')
                    self.log(f'Got BP: {self.medbot.get_current_systolic()}/{self.medbot.get_current_diastolic()}')
                    self.log(f'Got SP02: {self.medbot.get_current_blood_saturation()}')
                    self.log('Releasing....')
                    self.medbot.release_oximeter()
                    self.medbot.release_cuff()
                    self.operation_completed = True
                self.speaker_refreshed = False
            else:
                self.speaker_refreshed = True

        # Check if blood pressure is finished but oximeter is not
        elif(self.operation_started and not self.operation_completed):
            if(not self.bp_logged):
                self.log(f'Got BP: {self.medbot.get_current_systolic()}/{self.medbot.get_current_diastolic()}')
                self.log('Waiting for oximeter...')
                self.bp_logged = True
            if(not self.oximeter_thread.is_alive()):
                self.log(f'Got Pulse Rate: {self.medbot.get_current_pulse_rate()}')
                self.log(f'Got SP02: {self.medbot.get_current_blood_saturation()}')
                self.log('Releasing...')
                self.medbot.release_oximeter()
                self.medbot.release_cuff()
                self.operation_completed = True

        # Check if the measuring operation thread has finished
        # Does some variable resets for finalizing operation completion
        # elif-(self.oximeter_thread_started and not self.oximeter_thread.is_alive() and self.bp_thread_started and self.bp_finished and self.operation_started):
        #     self.operation_completed = True
        #     self.operation_started = False
            
        # Check if operation has completed
        # Flash the readings on to the screen and prompt user to use thermal printer or not
        # Save reading to database
        elif(self.operation_completed and not self.printer_prompted):
            self.display.itemconfigure(self.display_text, text = 'Saving....')
            pulse_rate = self.medbot.get_current_pulse_rate()
            systolic = self.medbot.get_current_systolic()
            diastolic = self.medbot.get_current_diastolic()
            blood_saturation = self.medbot.get_current_blood_saturation()
            self.pulse_rate_holder.itemconfigure(self.pulse_rate_text, text = str(pulse_rate) + ' bpm')
            self.blood_pressure_holder.itemconfigure(self.blood_pressure_text, text = str(systolic) + '/' + str(diastolic) + ' mmHg')
            self.blood_saturation_holder.itemconfigure(self.blood_saturation_text, text = str(blood_saturation) + ' %')
            self.log(f'Pulse Rate: {pulse_rate} bpm : {self.medbot.interpret_pulse_rate(self.medbot.current_user.age, self.medbot.get_current_pulse_rate())}')
            self.log(f'Blood Pressure: {systolic}/{diastolic} mmHg : {self.medbot.interpret_blood_pressure(self.medbot.get_current_systolic(), self.medbot.get_current_diastolic())}')
            self.log(f'Blood Saturation: {blood_saturation} % : {self.medbot.interpret_blood_saturation(self.medbot.get_current_blood_saturation())}')
            if(self.speaker_refreshed):
                pulse_rate_rating = self.medbot.interpret_pulse_rate(self.medbot.current_user.age,self.medbot.get_current_pulse_rate())
                blood_pressure_rating = self.medbot.interpret_blood_pressure(self.medbot.get_current_systolic(), self.medbot.get_current_diastolic())
                blood_saturation_rating = self.medbot.interpret_blood_saturation(self.medbot.get_current_blood_saturation())
                self.medbot.speak(f'Your pulse rate is {pulse_rate_rating}')
                time.sleep(0.5)
                self.medbot.speak(f'Your blood pressure rating is {blood_pressure_rating}')
                time.sleep(0.5)
                self.medbot.speak(f'Your blood saturation is {blood_saturation_rating}')
                # rating = self.medbot.interpret_current_readings()
                # if(rating == 'Low'):
                #     self.medbot.speak(self.low_vital_sign_voice_message)
                # elif(rating == 'Normal'):
                #     self.medbot.speak(self.normal_vital_sign_voice_message)
                # elif(rating == 'High'):
                #     self.medbot.speak(self.high_vital_sign_voice_message)
                if(not self.readings_saved):
                    self.log('Saving Readings....')
                    if(medbot.save_current_reading()):
                        self.log('Readings Saved')
                        self.readings_saved = True
                self.speaker_refreshed = False
                self.printer_prompted = True 
            else:
                self.speaker_refreshed = True

        # Check if readings is saved
        # Invoke printer command and logout
        elif(self.printer_prompted):
            if(not self.printer_choice_displayed):
                self.display.itemconfigure(self.display_text, text = self.printer_prompt_text + '\n')
                self.yes_button = tkinter.Button(self.display, text = 'Yes', width = 15, height = 2, 
                                    font = ('Lucida', 14, 'bold'), command = lambda:self.printer_response(True))
                self.yes_button.place(x = 130, y = 150)
                self.no_button = tkinter.Button(self.display, text = 'No', width = 15, height = 2, 
                                    font = ('Lucida', 14, 'bold'), command = lambda:self.printer_response(False))
                self.no_button.place(x = 355, y = 150)
                self.printer_choice_displayed = True
                self.speaker_refreshed = True
            if(self.speaker_refreshed):
                self.medbot.speak('Do you want to print the results?')
                self.speaker_refreshed = False
            if(not self.printer_responded):
                if(not self.printer_choice_thread_started):
                    self.printer_choice_thread_started = True
                    self.voice_command = Thread(target = self.medbot.get_voice_input, args=(['yes','no'],))
                    self.voice_command.start()
                if(self.medbot.voice_response == 'yes'):
                    self.printer_response(True)
                elif(self.medbot.voice_response == 'no'):
                    self.printer_response(False)
            else:
                self.medbot.listening = False
        elif(not self.window_launched):
            self.window_launched = True
        self.window.after(15, self.update)

    def on_close(self):
        self.log('Logging out...')
        show_message(self.window, 'Logout Successfully', 
                            'See you later, ' + self.medbot.current_user.name + ' !',
                            timeout = 3000)
        self.medbot.logout()
        self.medbot.database.connection.reconnect()
        self.root.just_logged_out = True
        self.master.deiconify()
        self.window.destroy()

    def reset(self):
        self.medbot.speak('Operation Interrupted. Restarting')
        self.window_launched = False
        self.wait_thread_started = False
        self.operation_started = False
        self.operation_completed = False
        self.animation_timer = 1
        self.finger_notification_fixed = False
        self.arm_notification_fixed = False
        self.finger_detected = False
        self.arm_detected = False
        self.detection_started = False
        self.detection_finished = False
        self.body_locked = False
        self.bp_finished = False
        self.voice_prompt_started = False
        self.oximeter_thread_started = False
        self.bp_thread_started = False
        self.readings_saved = False
        self.printer_prompted = False
        self.printer_responded = False
        self.printer_choice_displayed = False
        self.printer_choice_thread_started = False
        self.window_completed = False
        self.speaker_refreshed = False
        self.medbot.reset()

    def log(self, log: str):
        self.log_holder.insert(tkinter.END, f'\n{log}')
        self.log_holder.see(tkinter.END)

    def printer_response(self, agreed: bool):
        if(agreed):
            self.log('Printing Results...')
            date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            pulse_rate = self.medbot.get_current_pulse_rate()
            systolic = self.medbot.get_current_systolic()
            diastolic = self.medbot.get_current_diastolic()
            blood_saturation = self.medbot.get_current_blood_saturation()
            pulse_rate_rating = self.medbot.interpret_pulse_rate(self.medbot.current_user.age, pulse_rate)
            blood_pressure_rating = self.medbot.interpret_blood_pressure(systolic, diastolic)
            blood_saturation_rating = self.medbot.interpret_blood_saturation(blood_saturation)
            content = f"""
            Medbot

Name:   {self.medbot.current_user.name}
Id:     {self.medbot.current_user.id}
Date:   {date_now}

    Reading      Rating
--------------------------------
PR     {pulse_rate} bpm      {pulse_rate_rating}
BP     {systolic}/{diastolic} mmHg   {blood_pressure_rating}
Sp02   {blood_saturation} %         {blood_saturation_rating}
        
        
        """
            self.medbot.print(content)
        self.printer_responded = True
        self.medbot.listening = False
        self.window_completed = True
        self.log('Results Printed')
        self.on_close()

    def on_failure_voice_command(self):
        self.medbot.speak(self.voice_command_fail_message)
        
    def load_config(self):
        with open(os.path.join(dirname, 'config.yml'), 'r') as file:
            config = yaml.safe_load(file)
        self.body_check_prompt_text = config['medbot']['gui']['body_check_prompt']['text']
        self.body_check_prompt_voice = config['medbot']['gui']['body_check_prompt']['voice']
        self.in_progress_prompt_text = config['medbot']['gui']['in_progress_prompt']['text']
        self.in_progress_prompt_voice = config['medbot']['gui']['in_progress_prompt']['voice']
        self.low_vital_sign_voice_message = config['medbot']['gui']['vital_signs_indicator']['low']
        self.normal_vital_sign_voice_message = config['medbot']['gui']['vital_signs_indicator']['normal']
        self.high_vital_sign_voice_message = config['medbot']['gui']['vital_signs_indicator']['high']
        self.printer_prompt_text = config['medbot']['gui']['printer_prompt']['text']
        self.printer_prompt_answers = config['medbot']['gui']['printer_prompt']['accepted_answers']
        self.voice_command_fail_message = config['medbot']['gui']['printer_prompt']['on_failure_message'] 

if __name__ == '__main__':
    # with open(os.path.join(dirname, 'config.yml'), 'r') as file:
    #     config = yaml.safe_load(file)
    # database_host = config['medbot']['database']['host']
    # database = config['medbot']['database']['database']
    # database_user = config['medbot']['database']['user']
    # database_password = config['medbot']['database']['password']

    # database = medical_robot.Database(database_host,database,database_user,database_password)
    # medbot = medical_robot.Medbot(database, microphone_index=1)
    # medbot.load_config(os.path.join(dirname, 'config.yml'))
    # medbot.pulse_rate_from_bpm = True
    # MedbotGUI(medbot)
    MedbotGUIStartScreen()
    