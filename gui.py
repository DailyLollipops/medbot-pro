from database import Database
from medbot import Medbot
from tkinter import Image, messagebox
from PIL import ImageTk,Image
import tkinter

class PopupMessage:
    def show_message(window, title, message, timeout = 0):
        messagebox_container = tkinter.Toplevel(window)
        messagebox_container.withdraw()
        if(timeout > 0):
            messagebox_container.after(timeout, messagebox_container.destroy)
        else:
            pass
        messagebox.showinfo(title, message, parent = messagebox_container)

class MedbotLoginGui:
    def __init__(self, medbot):
        self.window = tkinter.Tk()
        self.window.title('Login Window')
        self.window.geometry('600x400')
        logo = ImageTk.PhotoImage(Image.open('images/logo.png'))
        self.window.iconphoto(False, logo)
        self.window.configure(background = 'white')
        self.medbot = medbot
 
        placeholder = tkinter.Canvas(self.window, width = 280, height = 390)
        qrcode = ImageTk.PhotoImage(Image.open('images/qrcode.png').resize((128,166)))
        placeholder.create_text(145, 65, text = 'Med-bot: Pulse Rate\nand\nBlood Pressure Monitor',
                                anchor = tkinter.CENTER, font = ('Lucida',14), justify = 'center')
        placeholder.create_image(85, 130, image = qrcode, anchor = tkinter.NW)
        placeholder.create_text(150, 355, text = 'Place your QR Code\nwithin the frame to Login',
                                anchor = tkinter.CENTER, font = ('Lucida',14), justify = 'center')
        placeholder.configure(background = 'white', highlightbackground = 'white' )
        placeholder.place(x = 0, y = 0)

        self.canvas = tkinter.Canvas(self.window, width = 300, height = 380)
        self.canvas.place(x = 290, y = 10)
        self.update()
        self.window.mainloop()

    def update(self):
        if(not self.medbot.has_user):
            ret, frame = self.medbot.get_qrcode_scanner_frame()
            if ret:
                self.photo = ImageTk.PhotoImage(image = Image.fromarray(frame))
                self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
                try:
                    logged_in = self.medbot.login_tk(frame)
                except:
                    PopupMessage.show_message(self.window, 'Login Failed', 'Invalid Credentials', timeout = 1500)
                if(logged_in):
                    PopupMessage.show_message(self.window, 'Login Successfully', 
                                        'Welcome back, ' + self.medbot.current_user.name + ' !',
                                        timeout = 2000)
                    MedbotMainWindow(self)
        self.window.after(15, self.update)

class MedbotMainWindow():
    def __init__(self, root):
        self.root = root
        self.root.window.withdraw()
        self.window = tkinter.Toplevel(self.root.window)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update()

    def update(self):
        self.window.after(15, self.update)

    def on_close(self):
        PopupMessage.show_message(self.window, 'Logout Successfully', 
                    'See you later, ' + self.root.medbot.current_user.name + ' !',
                    timeout = 3000)
        self.root.medbot.logout()
        self.root.window.deiconify()
        self.window.destroy()

database = Database('sql.freedb.tech','freedb_medbot','freedb_medbot','ct9xVSS$$2g35s7')
medbot = Medbot(database)
MedbotLoginGui(medbot)
