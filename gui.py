from database import Database
from medbot import Medbot
from tkinter import messagebox
import tkinter
import PIL.Image, PIL.ImageTk

class PopupMessage:
    def show_message(window, title, message, timeout = 0):
        messagebox_container = tkinter.Toplevel(window)
        messagebox_container.withdraw()
        if(timeout > 0):
            messagebox_container.after(timeout, messagebox_container.destroy)
        else:
            pass
        messagebox.showinfo(title, message, parent = messagebox_container)

class MedbotGUI:
    def __init__(self, window_title, medbot):
        self.window = tkinter.Tk()
        self.window.title(window_title)
        self.medbot = medbot
        self.canvas = tkinter.Canvas(self.window, width = 600, height = 400)
        self.canvas.pack()
        self.update()
        self.window.mainloop()

    def update(self):
        if(not self.medbot.has_user):
            ret, frame = self.medbot.get_qrcode_scanner_frame()
            if ret:
                self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
                self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
                logged_in = self.medbot.login_tk(frame)
                if(logged_in):
                    PopupMessage.show_message(self.window, 'Login Successfully', 
                                        'Welcome Back ' + self.medbot.current_user.name + ' !',
                                        timeout = 3000)
                    self.window.withdraw()
                    GUIWindow(self.window, self.medbot)
        self.window.after(15, self.update)

class GUIWindow():
    def __init__(self, root, medbot):
        self.root = root
        self.window = tkinter.Toplevel(self.root)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update()

    def update(self):
        self.window.after(15, self.update)

    def on_close(self):
        PopupMessage.show_message(self.window, 'Logout Successfully', 
                    'See you later ' + medbot.current_user.name + ' !',
                    timeout = 3000)
        self.root.deiconify()
        self.window.destroy()

database = Database('sql.freedb.tech','freedb_medbot','freedb_medbot','ct9xVSS$$2g35s7')
medbot = Medbot(database)
MedbotGUI("Tkinter and OpenCV",medbot)
