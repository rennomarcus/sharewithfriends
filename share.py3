'''
Project made by Marcus Renno
October, 5th 2015
Share files with your friends 
'''

import tkinter as tk
import socket
import tkinter.messagebox as ms
import tkinter.filedialog as fd
import tkinter.simpledialog as sd
import tkinter.ttk as ttk
import logging
import sqlite3
import threading

conn = sqlite3.connect('share.db', check_same_thread=False)
c = conn.cursor()

logging.basicConfig(format='%(levelname)s %(asctime)s %(funcName)s %(lineno)d %(message)s', level=logging.INFO)

class Application(tk.Frame):
    def __init__(self, master=None):
        logging.info('Opening application')
        thread = threading.Thread(target=self.initiate_server)
        thread.start()
        tk.Frame.__init__(self, master)
        self.create_ui(master)
        master.update_idletasks()
        w = master.winfo_screenwidth()
        h = master.winfo_screenheight()
        size = tuple(int(_) for _ in master.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        master.geometry("%dx%d+%d+%d" % (size + (x, y)))
        master.title("Share with friends")
    
    def change_port(self):
        self.port = sd.askinteger('Change port','What port would you like to use?')
        if self.port:
            c.execute ('UPDATE people SET port=? WHERE ID=1',  (self.port, ))
            conn.commit()

    def check_port(self,  port):
        self.my_port = c.execute ('SELECT * FROM people WHERE ID=1')
        self.info = self.my_port.fetchone()
        if self.info:
            port['text'] = self.info[3]

    def create_ui(self,  app):
        """
        Create the UI, load DB values, and initialize some text
        """
        self.menubar = tk.Menu(app)
        
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="My port",  command=self.change_port)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=app.quit)
        self.menubar.add_cascade(label="Config", menu=self.filemenu)
        
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About")
        self.menubar.add_cascade(label="Help",  menu=self.helpmenu)
        
        app.config(menu=self.menubar)
        
        logging.info('Creating top part')
        self.text_my_ip = tk.Label(app, text="My ip")
        self.text_my_ip.grid(row=0,  sticky="W")
        self.text_ip = tk.Label(app, text='127.0.0.1')
        self.text_ip.grid(row=0,  column=1,  sticky="W")
        self.add_ip(self.text_ip)
        self.text_my_port = tk.Label(app, text="My port")
        self.text_my_port.grid(row=1,  sticky="W")
        self.text_port= tk.Label(app, text="4000")
        self.check_port(self.text_port)
        self.text_port.grid(row=1,  column=1,  sticky="W")
        

        self.text_friend_name = tk.Label(app, text="Friend name")
        self.text_friend_name.grid(row=0,  column=2, sticky="W")
        self.text_friendname = tk.Label(app, text="")
        self.text_friendname.grid(row=0,  column=3, sticky="W")
        self.text_friend_address = tk.Label(app, text="Friend address")
        self.text_friend_address.grid(row=1,  column=2, sticky="W")
        self.text_friendaddress = tk.Label(app, text='')
        self.text_friendaddress.grid(row=1,  column=3,  sticky="W")
        
        
        logging.info('Creating bot part')
        self.list = tk.Listbox(app)
        self.list.grid(row=3,  columnspan=2)
        self.show_people(self.list)

        self.list_files = ttk.Treeview(app,  columns=("File","Size"),   height=7)
        self.list_files.height = 20
        self.list_files['show'] = 'headings'
        self.list_files.heading('#1', text='File')
        self.list_files.heading('#2', text='Size')
        self.list_files.column('#1', width=200)
        self.list_files.column('#2', width=100)
        self.list_files.grid(row=3,  column=2,  columnspan=3) 

        self.list.bind('<<ListboxSelect>>',  lambda x: self.show_files(self.list_files))
                
        self.bt_add_people = tk.Button(app,  text="add",  command=lambda: self.add_person(self.list))
        self.bt_add_people .grid(row=4, sticky="W")
        
        self.bt_del_people = tk.Button(app,  text="del",  command= lambda: self.del_person(self.list))
        self.bt_del_people.grid(row=4, column=1, sticky="W")
        
        self.bt_download= tk.Button(app,  text="download",  command= lambda: self.download(self.text_friendname['text'],  self.list_files))
        self.bt_download.grid(row=4, column=2, sticky="W")
        
        self.bt_add_file = tk.Button(app,  text="add",  command=lambda: self.add_file(self.text_friendname['text'],  self.list_files))
        self.bt_add_file.grid(row=4, column=3, sticky="E")
        
        self.del_file= tk.Button(app,  text="del")
        self.del_file.grid(row=4, column=4, sticky="E")
        
        # create a popup menu for the list
        self.menu_list = tk.Menu(self, tearoff=0)
        self.menu_list.add_command(label="Refresh list",  command= self.refresh_file_list)

        self.list_files.bind('<Button-3>',  self.popup)
    
    def popup(self, event):
        self.menu_list.post(event.x_root, event.y_root)
        
    def download(self, person,   list_files):
        if person == 'myself':
            return
        elif list_files.focus():
            self.selected = list_files.item(list_files.focus())['values'][0]
            self.find_server = c.execute("SELECT * FROM people WHERE name=?",  (person, ) )
            self.info = self.find_server.fetchone()
            if self.info and self.selected:
                logging.info('Downloading...')
                self.thread = threading.Thread(target=self.connect_client,  args=(self.info[2], self.info[3], self.selected))
                self.thread.start()

    def connect_client(self,  ip,  port,  file):
        '''
        Function that is used in the thread to download the file from the server (friend)
        '''
        s = socket.socket()

        s.connect((ip,  port))
        s.send(str.encode('command: download\n'))
        s.send(str.encode(file) + str.encode('\n'))
        f = open(file,'wb')
        l = 1
        while (l):
            l = s.recv(1024)
            f.write(l)
        logging.info('Download completed')
        ms.showwarning('Download completed', '{0} has been downloaded'.format(file))
        f.close()
        s.close()
    def show_files(self,  list_files):
        """
        Show the files in the Treeview when user have clicked in the name list
        """
        logging.info('Showing files and display info of selected person')
        self.person = self.list.get(self.list.curselection())
        
        if self.person:
            #DB files (name, location, size, person)
            #DB people (name, ip, port)
            
            self.findperson = c.execute("SELECT * FROM people WHERE name=? ",  (self.person, ) )
            self.text_friendname['text'] = self.person
            self.info = self.findperson.fetchone()
            self.text_friendaddress['text'] = "{0}:{1}".format(self.info[2] , self.info[3])
            for i in list_files.get_children():
                list_files.delete(i)
                
            
            for  row in c.execute("SELECT * FROM files WHERE person=? ",  (self.person, ) ):
                list_files.insert('', 'end','',   values=(row[1], row[3]) )
        else:
             logging.warning('No person selected')
        

    
    
    def add_person(self, list):
        """
        Dialog box to ask/add person to the database/list
        """
        logging.info('Adding person')
        self.name = sd.askstring('Add person','Type your friend\'s name')
        self.ip = sd.askstring('Add person','Type your friend\'s ip')
        self.port = sd.askinteger('Add person', 'Type your friend\'s port')
        if self.name and self.ip and self.port:
            logging.info('Adding person to DB')
            c.execute("INSERT INTO people (name, ip, port) VALUES (?,?,?)",  (self.name,  self.ip,  self.port))
            list.insert(list.size(), self.name)
            conn.commit()
        else:
            logging.info('Person not added. Missing one argument')
            
    def del_person(self, list):
        """
        Delete a person within the database/list
        """
        self.person = list.get(list.curselection())
        if self.person == 'myself':
            ms.showwarning('error', 'You cannot remove yourself from the list')
            return
        
        self.answer = ms.askquestion("Delete", "Are You Sure?", icon='warning')
        if self.answer == 'yes':
            self.remove_person(list)
            
        
    def add_file(self,  friend,  list_files):
        self.name =  fd.askopenfilename()
        if self.name:
            print(self.name)
            self.filename = self.name.split('/')[-1]
            c.execute("INSERT INTO files (name, location, size, person) VALUES (?, ?, 0, 'myself')",  (self.filename,  self.name))
            conn.commit()
            
            if friend == 'myself':
                list_files.insert('', 'end','',   values=(self.filename, 0 ))
        
    def add_ip(self, ip):
        self.error = ''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as msg:
            self.error = msg
            s = None
        try:
             s.connect(('8.8.8.8', 0)) # connecting to a UDP address doesn't send packets
        except socket.error as msg:
            self.error = msg
            s.close()
            s = None
        if s is None:
            logging.warning(self.error)  #[Errno 101] Network is unreachable
        else:
            self.local_ip_address = s.getsockname()[0]
            ip['text'] = self.local_ip_address

    def show_people(self, list):
        """
        List the people in the DB in the dialogbox
        """
        logging.info('Adding people to listbox')
        for i,  row in enumerate(c.execute('SELECT * FROM people ORDER BY id')):
            list.insert(i,row[1])
            
        #print('done')
    def remove_person(self, list):
        """
        Remove someone selected in the list from itself and  in the DB 
        """
        logging.info('Removing person')
        self.cursor = list.curselection()
        self.person = self.list.get(self.list.curselection())
        if self.person:
            c.execute("DELETE FROM people WHERE name=?",  (self.person, ))
            conn.commit()
            list.delete(self.cursor)    
            
    
        
    def refresh_file_list(self):
        self.address = self.text_friendaddress['text'].split(':') 
        self.person = self.text_friendname['text']
        if not self.person == 'myself':
            s = socket.socket()
            ip = self.address[0]
            port = int(self.address[1])
            s.connect((ip, port))
            s.send(str.encode('command: get_list\n'))
            self.read_files = readlines(self,  s)
            c.execute("DELETE FROM files WHERE person=?", (self.person, ))
            for item in self.read_files:
                if item:
                    self.filename = item.split(': ')[1].split()[0]
                    c.execute("INSERT INTO files (name, size, person) VALUES (?,?,?)", (self.filename, 0, self.person))
            conn.commit()


            s.close()
    def initiate_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.findperson = c.execute("SELECT * FROM people WHERE ID=1")
        self.info = self.findperson.fetchone()
        server.bind(('',self.info[3]))
        server.listen(10)
        
        logging.info('Server initiated')
        while True:
            sc, address = server.accept()
            print(address)
            self.read_data = readlines(self,  sc)
            self.command = next(self.read_data).split("command: ")[1]
            
            if (self.command.split()[0] == "get_list"):
                logging.info('Command get_list requested')
                self.arg = self.command[-1]
                for rows in c.execute("SELECT * FROM files WHERE person='myself'"):
                    self.str = "file: {0} {1}\n".format(rows[2].split('/')[-1], self.arg)
                    sc.send(str.encode(self.str))
                
            
            if (self.command.split()[0] == "download"):
                logging.info('Command download requested')
                self.filename = next(self.read_data)
                logging.info('Looking for file {0}...'.format(self.filename))
                self.findfile = c.execute("SELECT * FROM files WHERE name=?", (self.filename, ) )
                self.file = self.findfile.fetchone()
                if self.file:
                    logging.info('Sending file {0} to {1}'.format(self.filename, address))
                    self.f=open (self.file[2], "rb") 
            
                    self.buffer = self.f.read(1024)
                    while (self.buffer):
                        sc.send(self.buffer)
                        self.buffer = self.f.read(1024)
                    self.f.close()
                
            sc.close()

        server.close()

def readlines(self, sock, recv_buffer=1024, delim='\n'):
    buffer = ''
    data = True

    while data:
        data = sock.recv(recv_buffer)
        if not data:
            break
        buffer = data.decode('utf-8')
        while buffer.find(delim) != -1:
            line, buffer = buffer.split('\n', 1)
            yield line
        yield buffer
        
    

def table_create():
    """
    Create the DB to save the data persistently
    """
    c.execute("CREATE TABLE IF NOT EXISTS people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, ip TEXT, port INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER, name TEXT, location TEXT, size INTEGER, person TEXT, FOREIGN KEY(person) REFERENCES people(name))")
    conn.commit()

def data_entry():
    findme = c.execute("SELECT * FROM people WHERE id=1" )
    info = findme.fetchone()
    if not info:
        c.execute("INSERT INTO people (name, ip, port) VALUES ('myself','localhost','4000')")
        conn.commit()
    
def on_close(window):
    window.destroy()
    #TODO kill connections
    
def main():
    table_create()
    data_entry()

    root = tk.Tk()
    #root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    app = Application(master=root)
    
    app.mainloop()
    
    
    conn.close()

  

if __name__ == '__main__':
    main()


