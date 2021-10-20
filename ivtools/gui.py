#!/usr/bin/env python3.6

import tkinter as tk

if __name__ == "__main__":
    import sys
    sys.path.append("..")

from ivtools.editor import IVEditor

PX = 5
PY = 2


class IVToolsGUI(tk.Frame):

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.editor = IVEditor()
        self.entries = {
            "read": tk.Entry(master),
            "load_template": tk.Entry(master),
            "write_nodes": tk.Entry(master),
            "load_nodes": tk.Entry(master),
            "delete": tk.Entry(master),
            "write": tk.Entry(master)
        }
        self.buttons = {
            "read": tk.Button(master, text="Read", command=self.read),
            "load_template": tk.Button(master, text="Load Template", command=self.load_template),
            "write_nodes": tk.Button(master, text="Write Nodes File", command=self.write_nodes),
            "load_nodes": tk.Button(master, text="Load Nodes File", command=self.load_nodes),
            "delete": tk.Button(master, text="Delete", command=self.delete),
            "write": tk.Button(master, text="Write", command=self.write)
        }
        self.feedback = tk.Label(self.master, text="Ready...")
        self.init_window()

    @staticmethod
    def __process_file_path(file_path):
        file_path = file_path.replace("\\", "/")
        file_path = file_path.replace('"', "")
        return file_path

    def init_window(self):
        self.master.title("IVTools")
        for row, ((_, entry), (_, button)) in enumerate(zip(self.entries.items(), self.buttons.items())):
            entry.grid(row=row, column=0, padx=PX, pady=PY, sticky=tk.EW, columnspan=3)
            button.grid(row=row, column=3, padx=PX, pady=PY, sticky=tk.EW)
        tk.Button(self.master, text="Convert to IV", command=lambda: self.convert("iv")).grid(row=row + 1, column=0, padx=PX, pady=PY, sticky=tk.EW)
        tk.Button(self.master, text="Convert to VRML", command=lambda: self.convert("wrl")).grid(row=row + 1, column=1, padx=PX, pady=PY, sticky=tk.EW)
        tk.Button(self.master, text="Apply Nodes", command=self.apply_nodes).grid(row=row + 1, column=2, padx=PX, pady=PY, sticky=tk.EW)
        tk.Button(self.master, text="Quit", command=quit).grid(row=row + 1, column=3, padx=PX, pady=PY, sticky=tk.EW)
        self.feedback.grid(row=row + 2, column=0, padx=PX, pady=PY, columnspan=4, sticky=tk.W)

    def read(self):
        try:
            file_path = self.entries["read"].get()
            file_path = self.__process_file_path(file_path)
            self.feedback.config(text="Loading data from %s ..." % file_path)
            self.editor.read(file_path)
            self.feedback.config(text="Success : Loaded data from %s" % file_path)
        except FileNotFoundError:
            self.feedback.config(text="Error : File not found")
        except OSError as e:
            self.feedback.config(text="Error : %s" % e)

    def write(self):
        if self.editor.data is None:
            self.feedback.config(text="Error : No data to write")
        else:
            try:
                self.feedback.config(text="Writing data to %s ..." % self.entries["write"].get())
                self.editor.write(self.entries["write"].get())
                self.feedback.config(text="Success : Wrote data to %s" % self.entries["write"].get())
            except FileNotFoundError:
                self.feedback.config(text="Error : File not found")

    def load_template(self):
        file_path = self.entries["load_template"].get()
        file_path = self.__process_file_path(file_path)
        try:
            self.feedback.config(text="Loading template nodes from %s ..." % file_path)
            self.editor.load_template_file(file_path)
            self.feedback.config(text="Success : Loaded template nodes from %s" % file_path)
        except FileNotFoundError:
            self.feedback.config(text="Error : File not found")
        self.editor.template_nodes.print()

    def write_nodes(self):
        # try:
        file_path = self.entries["write_nodes"].get()
        file_path = self.__process_file_path(file_path)
        self.feedback.config(text="Writing nodes to %s ..." % file_path)
        self.editor.write_nodes_file(file_path)
        self.feedback.config(text="Success : Written nodes to %s" % file_path)
        # except FileNotFoundError:
        #     self.feedback.config(text="Error : File not found")
        # except AttributeError:
        #     self.feedback.config(text="Error : Invalid data or template")

    def load_nodes(self):
        try:
            self.feedback.config(text="Loading nodes from %s ..." % self.entries["load_nodes"].get())
            self.editor.load_nodes_file(self.entries["load_nodes"].get())
            self.feedback.config(text="Success : Loaded nodes from %s" % self.entries["load_nodes"].get())
        except FileNotFoundError:
            self.feedback.config(text="Error : File not found")

    def delete(self):
        if self.entries["delete"].get():
            #try:
            self.feedback.config(text="Deleting all %s nodes ..." % self.entries["delete"].get())
            self.editor.delete(self.entries["delete"].get())
            self.feedback.config(text="Success : Deleted all %s nodes" % self.entries["delete"].get())
            #except AttributeError:
            #    self.feedback.config(text="Error : Invalid data")
        else:
            self.feedback.config(text="Error : Nothing to delete")

    def convert(self, ext):
        if ext == "iv":
            #try:
            self.feedback.config(text="Converting data to OpenInventor format ...")
            self.editor.convert(ext)
            self.feedback.config(text="Success : Converted data to OpenInventor format")
            #except AttributeError:
            #    self.feedback.config(text="Error : Invalid data to convert")
        else:
            self.feedback.config(text="NotImplementedError : Cannot convert to %s format" % ext)

    def apply_nodes(self):
        #try:
        self.feedback.config(text="Applying new nodes to data ...")
        self.editor.apply_nodes()
        self.feedback.config(text="Success : New nodes applied to data")
        #except AttributeError:
        # self.feedback.config(text="Error : Invalid data or nodes")


if __name__ == "__main__":
    root = tk.Tk()
    app = IVToolsGUI(root)
    app.mainloop()
