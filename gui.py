from tkinter import Image, messagebox
from PIL import ImageTk,Image
from threading import Thread
from datetime import datetime
import medical_robot
import tkinter
import time
import yaml

def show_message(window, title, message, timeout = 0):
    messagebox_container = tkinter.Toplevel(window)
    messagebox_container.withdraw()
    if(timeout > 0):
        messagebox_container.after(timeout, messagebox_container.destroy)
    messagebox.showinfo(title, message, parent = messagebox_container)

class MedbotGUI:
    def __init__(self, medbot: medical_robot.Medbot):
        self.window = tkinter.Tk()
        self.window.title('Login Window')
        self.window.geometry('800x440')
        logo = ImageTk.PhotoImage(Image.open('images/logo.png'))
        self.window.iconphoto(False, logo)
        self.window.configure(background = 'white')
        self.medbot = medbot
        self.logged_in = False

        self.placeholder = tkinter.Canvas(self.window, width = 380, height = 400)
        self.qrcode = ImageTk.PhotoImage(Image.open('images/qrcode.png').resize((128,166)))
        self.placeholder.create_text(190, 65, text = 'Med-bot: Pulse Rate\nand\nBlood Pressure Monitor',
                            anchor = tkinter.CENTER, font = ('Lucida',14), justify = 'center')
        self.placeholder.create_image(125, 130, image = self.qrcode, anchor = tkinter.NW)
        self.placeholder.create_text(180, 355, text = 'Place your QR Code\nwithin the frame to Login',
                            anchor = tkinter.CENTER, font = ('Lucida',14), justify = 'center')
        self.placeholder.configure(background = 'white', highlightbackground = 'white' )
        self.placeholder.place(x = 0, y = 0)

        self.settings_logo = ImageTk.PhotoImage(Image.open('images/settings.png').resize((20,20)))
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
        if(not self.medbot.has_user):
            ret, frame = self.medbot.get_qrcode_scanner_frame()
            if ret:
                self.photo = ImageTk.PhotoImage(image = Image.fromarray(frame))
                self.scanner_image = self.qrcode_scanner_frame.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
                try:
                    self.logged_in = self.medbot.login_tk(frame)
                except Exception as e:
                    show_message(self.window, 'Login Failed', 'Invalid Credentials', timeout = 1500)
                    print(e)
                if(self.logged_in):
                    show_message(self.window, 'Login Successfully', 
                                        'Welcome back, ' + self.medbot.current_user.name + ' !',
                                        timeout = 2000)
                    self.qrcode_scanner_frame.delete(self.scanner_image)
                    MedbotGUIMain(self)
        self.window.after(15, self.update)

    def open_settings(self):
        self.MedbotGUISettings(self)

    class MedbotGUISettings:
        def __init__(self, master: tkinter.Tk, medbot: medical_robot.Medbot):
            self.root = root
            self.window = tkinter.Toplevel(self.root.window)
            self.window.title('Settings')
            self.window.geometry('400x300')
            self.window.configure(background = 'white')
            self.window.grab_set()

            self.settings_logo = ImageTk.PhotoImage(Image.open('images/settings.png').resize((24,24)))
            self.title_label = tkinter.Label(self.window, text = ' Settings', image = self.settings_logo,
                                compound = tkinter.LEFT, font = ('Lucida', 16), justify = 'center',
                                background = 'white')
            self.title_label.place(x = 150, y = 10)

            self.voice_prompt_logo = ImageTk.PhotoImage(Image.open('images/speaker.png').resize((16,16)))
            self.voice_prompt_label = tkinter.Label(self.window, text = ' Voice Prompt', font = ('Lucida', 11),
                                background = 'white', image = self.voice_prompt_logo, compound = tkinter. LEFT)
            self.voice_prompt_label.place(x = 50, y = 75)
            self.voice_prompt_value = tkinter.StringVar(self.window,
                                'enabled' if self.root.medbot.voice_prompt_enabled == True else 'disabled')
            tkinter.Radiobutton(self.window, text = 'Enable', variable = self.voice_prompt_value,
                                value = 'enabled', command = self.set_voice_prompt,
                                background = 'white').place(x = 80, y = 100)
            tkinter.Radiobutton(self.window, text = 'Disable', variable = self.voice_prompt_value,
                                value = 'disabled', command = self.set_voice_prompt,
                                background = 'white').place(x = 160, y = 100)

            self.voice_command_logo = ImageTk.PhotoImage(Image.open('images/microphone.png').resize((16,16)))
            self.voice_command_label = tkinter.Label(self.window, text = ' Voice Command', font = ('Lucida', 11),
                                background = 'white', image = self.voice_command_logo, compound = tkinter.LEFT)  
            self.voice_command_label.place(x = 50, y = 150)
            self.voice_command_value = tkinter.StringVar(self.window,
                                'enabled' if self.root.medbot.voice_command_enabled == True else 'disabled')
            tkinter.Radiobutton(self.window, text = 'Enable', variable = self.voice_command_value,
                                value = 'enabled', command = self.set_voice_command,
                                background = 'white').place(x = 80, y = 175)
            tkinter.Radiobutton(self.window, text = 'Disable', variable = self.voice_command_value,
                                value = 'disabled', command = self.set_voice_command,
                                background = 'white').place(x = 160, y = 175)

        def set_voice_prompt(self):
            temp = self.voice_prompt_value.get()
            if(temp == 'disabled'):
                value = False
            else:
                value = True
            self.root.medbot.set_voice_prompt_enabled(value)
            self.save_config('voice_prompt', value)
            print('Voice prompt set to ' + str(value))

        def set_voice_command(self):
            temp = self.voice_command_value.get()
            if(temp == 'disabled'):
                value = False
            else:
                value = True
            self.root.medbot.set_voice_command_enabled(value)
            self.save_config('voice_command', value)
            print('Voice command set to ' + str(value))

        def save_config(self, key, value):
            with open('config.yml', 'r') as file:
                config = yaml.safe_load(file)
            config['medbot']['settings'][key] = value
            with open('config.yml', 'w') as file:
                yaml.dump(config, file)

class MedbotGUIMain():
    def __init__(self, root: MedbotGUI):
        self.root = root
        self.root.window.withdraw()
        self.window = tkinter.Toplevel(self.root.window)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.title('Main Window')
        self.window.geometry('800x440')
        logo = ImageTk.PhotoImage(Image.open('images/logo.png'))
        self.window.iconphoto(False, logo)
        self.window.configure(background = 'white')

        self.window_launched = False
        self.display_refreshed = False
        self.operation_started = False
        self.operation_completed = False
        self.animation_timer = 1
        self.oximeter_thread = Thread(target = self.root.medbot.start_oximeter)
        self.bp_thread = Thread(target = self.root.medbot.start_blood_pressure_monitor)
        self.voice_prompt_started = False
        self.oximeter_thread_started = False
        self.bp_thread_started = False
        self.printer_prompted = False
        self.printer_responded = False
        self.printer_choice_displayed = False
        self.printer_choice_thread_started = False
        self.window_completed = False

        self.display = tkinter.Canvas(self.window, width = 700, height = 270)
        self.display_text = self.display.create_text(350, 140, text = 'Initializing Please Wait',
                            anchor = tkinter.CENTER, font = ('Lucida', 20), justify = 'center')
        self.display.place(x = 50, y = 30)

        self.pulse_rate_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.pulse_rate_icon = ImageTk.PhotoImage(Image.open('images/pulse_rate.png').resize((64,64)))
        self.pulse_rate_holder.create_image(10, 18, image = self.pulse_rate_icon, anchor = tkinter.NW)
        self.pulse_rate_holder.create_text(140, 40, text = 'Pulse Rate', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.pulse_rate_text = self.pulse_rate_holder.create_text(135, 65, text = '-- bpm',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.pulse_rate_holder.configure(background = '#f5f7fa')
        self.pulse_rate_holder.place(x = 50, y = 320)

        self.blood_pressure_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.blood_pressure_icon = ImageTk.PhotoImage(Image.open('images/blood_pressure.png').resize((64,64)))
        self.blood_pressure_holder.create_image(10, 18, image = self.blood_pressure_icon, anchor = tkinter.NW)
        self.blood_pressure_holder.create_text(145, 40, text = 'Blood Pressure', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.blood_pressure_text = self.blood_pressure_holder.create_text(140, 65, text = '--/-- mmHg',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.blood_pressure_holder.configure(background = '#f5f7fa')
        self.blood_pressure_holder.place(x = 290, y = 320)

        self.blood_saturation_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.blood_saturation_icon = ImageTk.PhotoImage(Image.open('images/blood_saturation.png').resize((64,64)))
        self.blood_saturation_holder.create_image(5, 18, image = self.blood_saturation_icon, anchor = tkinter.NW)
        self.blood_saturation_holder.create_text(140, 40, text = 'Blood Saturation', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.blood_saturation_text = self.blood_saturation_holder.create_text(130, 65, text = '-- %',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.blood_saturation_holder.configure(background = '#f5f7fa')
        self.blood_saturation_holder.place(x = 530, y = 320)
        self.load_config()
        self.update()

    def update(self):
        # Check if body check operation hasn't start (initialize)
        if(not self.root.medbot.body_check_started and not self.window_completed and self.window_launched):
            self.display.itemconfigure(self.display_text, text = 'Starting Body Check')
            if(not self.voice_prompt_started):
                self.voice_prompt_started = True
                self.root.medbot.speak(self.body_check_prompt_voice)
                # voice_prompt = Thread(target=self.root.medbot.speak, args=(self.body_check_prompt_voice,))
                # voice_prompt.start()
                self.root.medbot.start_body_check()
            

        # Check if body check operation is in progress
        elif(self.root.medbot.body_check_in_progress and self.voice_prompt_started):
            if(self.animation_timer == 1):
                self.display.itemconfigure(self.display_text, text = self.body_check_prompt_text + ' .')
                self.animation_timer = 2
            elif(self.animation_timer == 2):
                self.display.itemconfigure(self.display_text, text = self.body_check_prompt_text + '  .')
                self.animation_timer = 0
            elif(self.animation_timer == 0):
                self.display.itemconfigure(self.display_text, text = self.body_check_prompt_text + '.')
                self.animation_timer = 1
                # For testing only, use the communication with Arduino instead
                self.root.medbot.body_check_complete() 
            time.sleep(0.5)

        # Check if body check operation is completed but the measuring operation has not started
        # Starts the oximeter and bp thread
        elif(self.root.medbot.body_check_completed and not self.operation_started):
            self.display.itemconfigure(self.display_text, text = self.in_progress_prompt_text)
            if(self.display_refreshed):
                if(self.root.medbot.voice_prompt_enabled):
                    self.root.medbot.speak(self.in_progress_prompt_voice)
                    # voice_prompt = Thread(target=self.root.medbot.speak, args=(self.in_progress_prompt_voice,))
                    # voice_prompt.start()
                self.operation_started = True
                if(not self.oximeter_thread_started):
                    self.oximeter_thread.start()
                    self.oximeter_thread_started = True
                if(not self.bp_thread_started):
                    self.root.medbot.start_blood_pressure_monitor()
                    self.oximeter_thread_started = True
            self.display_refreshed = True

        # Check if the measuring operation threads are still alive
        # Do some animation
        elif(self.oximeter_thread_started and self.oximeter_thread.is_alive() and self.bp_thread_started and self.bp_thread.is_alive() and self.operation_started):
            pass

        # Check if the measuring operation thread has finished
        # Does some variable resets for finalizing operation completion
        elif(self.oximeter_thread_started and not self.oximeter_thread.is_alive() and self.bp_thread_started and not self.bp_thread.is_alive() and self.operation_started):
            self.operation_completed = True
            self.operation_started = False
            
        # Check if operation has completed
        # Flash the readings on to the screen and prompt user to use thermal printer or not
        # Save reading to database
        elif(not self.oximeter_thread.is_alive() and not self.bp_thread.is_alive() and self.operation_started and not self.printer_prompted):
            pulse_rate = self.root.medbot.get_current_pulse_rate()
            systolic = self.root.medbot.get_current_systolic()
            diastolic = self.root.medbot.get_current_diastolic()
            blood_saturation = self.root.medbot.get_current_blood_saturation()
            self.pulse_rate_holder.itemconfigure(self.pulse_rate_text, text = str(pulse_rate) + ' bpm')
            self.blood_pressure_holder.itemconfigure(self.blood_pressure_text, text = str(systolic) + '/' + str(diastolic) + ' mmHg')
            self.blood_saturation_holder.itemconfigure(self.blood_saturation_text, text = str(blood_saturation) + ' %')
            # self.root.medbot.save_current_reading()
            rating = self.root.medbot.interpret_current_readings()
            if(rating == 'Low'):
                self.root.medbot.speak(self.low_vital_sign_voice_message)
            elif(rating == 'Normal'):
                self.root.medbot.speak(self.normal_vital_sign_voice_message)
            elif(rating == 'High'):
                self.root.medbot.speak(self.high_vital_sign_voice_message)
            self.printer_prompted = True

        # Invoke printer command and logout
        elif(self.printer_prompted):
            if(not self.printer_choice_displayed):
                self.display.itemconfigure(self.display_text, text = self.printer_prompt_text + '\n')
                self.yes_button = tkinter.Button(self.display, text = 'Yes', width = 15, height = 2, 
                                    font = ('Lucida', 14, 'bold'), command = lambda:self.printer_response(True))
                self.yes_button.place(x = 130, y = 200)
                self.no_button = tkinter.Button(self.display, text = 'No', width = 15, height = 2, 
                                    font = ('Lucida', 14, 'bold'), command = lambda:self.printer_response(False))
                self.no_button.place(x = 355, y = 200)
                self.printer_choice_displayed = True
            if(not self.printer_responded):
                if(not self.printer_choice_thread_started):
                    self.printer_choice_thread_started = True
                    self.voice_command = Thread(target = self.root.medbot.get_voice_input, args=(['yes','no'],))
                    self.voice_command.start()
                if(self.root.medbot.voice_response == 'yes'):
                    self.printer_response(True)
                elif(self.root.medbot.voice_response == 'no'):
                    self.printer_response(False)
        elif(not self.window_launched):
            self.window_launched = True
        self.window.after(15, self.update)

    def on_close(self):
        show_message(self.window, 'Logout Successfully', 
                            'See you later, ' + self.root.medbot.current_user.name + ' !',
                            timeout = 3000)
        time.sleep(3)
        self.root.medbot.logout()
        self.root.medbot.database.connection.reconnect()
        self.root.window.deiconify()
        self.window.destroy()

    def printer_response(self, agreed: bool):
        if(agreed):
            date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            pulse_rate = self.root.medbot.get_current_pulse_rate()
            systolic = self.root.medbot.get_current_systolic()
            diastolic = self.root.medbot.get_current_diastolic()
            blood_saturation = self.root.medbot.get_current_blood_saturation()
            pulse_rate_rating = self.root.medbot.interpret_pulse_rate(self.root.medbot.current_user.age, pulse_rate)
            blood_pressure_rating = self.root.medbot.interpret_blood_pressure(systolic, diastolic)
            blood_saturation_rating = self.root.medbot.interpret_blood_saturation(blood_saturation)
            content = f"""
            Medbot

Name:   {self.root.medbot.current_user.name}
Id:     {self.root.medbot.current_user.id}
Date:   {date_now}

       Reading      Rating
--------------------------------
PR     {pulse_rate} bpm      {pulse_rate_rating}
BP     {systolic}/{diastolic} mmHg   {blood_pressure_rating}
Sp02   {blood_saturation} %         {blood_saturation_rating}
        """
            self.root.medbot.print(content)
        self.printer_responded = True
        self.root.medbot.listening = False
        self.window_completed = True
        self.on_close()

    def on_failure_voice_command(self):
        self.root.medbot.speak(self.voice_command_fail_message)
        
    def load_config(self):
        with open('config.yml', 'r') as file:
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
    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)
    database_host = config['medbot']['database']['host']
    database = config['medbot']['database']['database']
    database_user = config['medbot']['database']['user']
    database_password = config['medbot']['database']['password']

    database = medical_robot.Database(database_host,database,database_user,database_password)
    medbot = medical_robot.Medbot(database)
    medbot.load_config('config.yml')
    MedbotGUI(medbot)
