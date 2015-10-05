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
        thread = threading.Thread(target=self.initiateServer)
        thread.start()
        app = tk.Frame.__init__(self, master)
        self.createUI(app)
        master.update_idletasks()
        w = master.winfo_screenwidth()
        h = master.winfo_screenheight()
        size = tuple(int(_) for _ in master.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        master.geometry("%dx%d+%d+%d" % (size + (x, y)))
        master.title("Share with friends")
        #self.delete()
    

    def createUI(self,  app):
        """
        Create the UI, load DB values, and initialize some text
        """
        logging.info('Creating top part')
        self.text_my_ip = tk.Label(app, text="My ip")
        self.text_my_ip.grid(row=0,  sticky="W")
        self.text_ip = tk.Label(app, text='127.0.0.1')
        self.text_ip.grid(row=0,  column=1,  sticky="W")
        self.add_ip(self.text_ip)
        self.text_my_port = tk.Label(app, text="My port")
        self.text_my_port.grid(row=1,  sticky="W")
        self.text_port= tk.Label(app, text="4000")
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
        self.showPeople(self.list)

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
        
        self.bt_download= tk.Button(app,  text="download",  command= lambda: self.download(self.list,  self.list_files))
        self.bt_download.grid(row=4, column=2, sticky="W")
        
        self.bt_add_file = tk.Button(app,  text="add",  command=lambda: self.add_file(self.list,  self.list_files))
        self.bt_add_file.grid(row=4, column=3, sticky="E")
        
        self.del_file= tk.Button(app,  text="del")
        self.del_file.grid(row=4, column=4, sticky="E")



    def download(self,  list,  list_files):
        #threading.Thread(target=self.initiateServer)
        self.person = list.get(list.curselection())
        if self.person == 'myself':
            return
        elif list_files.focus():
            self.selected = list_files.item(list_files.focus())['values'][0]
            self.find_server = c.execute("SELECT * FROM people WHERE name=?",  (self.person, ) )
            self.info = self.find_server.fetchone()
            if self.info and self.selected:
                logging.info('Downloading...')
                s = socket.socket()

                s.connect((self.info[2],self.info[3]))
                s.send(self.selected)
                f = open(self.selected,'wb')
                l = 1
                while (l):
                    l = s.recv(1024)
                    f.write(l)
                
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
            
        
    def add_file(self,  list,  list_files):
        self.name =  fd.askopenfilename()
        if self.name:
            print(self.name)
            self.filename = self.name.split('/')[-1]
            c.execute("INSERT INTO files (name, location, size, person) VALUES (?, ?, 0, 'myself')",  (self.filename,  self.name))
            conn.commit()
            self.person = list.get(list.curselection())
            
            if self.person == 'myself':
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

    def showPeople(self, list):
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
    def initiateServer(self):
        server = socket.socket()
        server.bind(("localhost",4001))
        server.listen(10)
        
        logging.info('Server initiated')
        while True:
            sc, address = server.accept()
            print(address)
            self.readfile = readlines(self,  sc)
            self.filename = next(self.readfile)
            
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

def readlines(self, sock, recv_buffer=4096, delim='\n'):
    buffer = ''
    data = True

    while data:
        data = sock.recv(recv_buffer)
        buffer = data.decode('utf-8')
        while buffer.find(delim) != -1:
            line, buffer = buffer.split('\n', 1)
            yield line
        yield buffer
        
    

def tableCreate():
    """
    Create the DB to save the data persistently
    """
    c.execute("CREATE TABLE IF NOT EXISTS people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, ip TEXT, port INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER, name TEXT, location TEXT, size INTEGER, person TEXT, FOREIGN KEY(person) REFERENCES people(name))")
    conn.commit()

def dataEntry():
    findme = c.execute("SELECT * FROM people WHERE id=1" )
    info = findme.fetchone()
    if not info:
        c.execute("INSERT INTO people (name, ip, port) VALUES ('myself','localhost','3333')")
        conn.commit()
            
        
def droptable():
    c.execute("DROP TABLE people")
    c.execute("DROP TABLE files")
    conn.commit()

def main():
    tableCreate()
    dataEntry()

    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
    
    
    conn.close()

  

if __name__ == '__main__':
    main()


