# -*- coding: utf-8 -*-
"""
Created on Mon Apr  5 17:01:34 2021

@author: Vivian Imbriotis
"""
#tkinter for the UI
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

#mingus for the music theory
import mingus.core.notes as notes
import mingus.core.keys as keys
from mingus.containers import Note
import mingus.extra.fft as fft

#numeric operations
import numpy as np

#microphone access
import sounddevice as sd

#python imports
from copy import deepcopy
import queue



class Scale:
    def __init__(self,key):
        '''
        The diatonic major scale in a given key, starting with the 4th octave.

        Parameters
        ----------
        key : string 
            The tonic of the scale.
        '''
        self.scale = keys.get_notes(key)
    def __getitem__(self,index):
        if type(index)!=int or index<0:
            try:
                return [self[i] for i in index]
            except TypeError:
                raise IndexError("invalid indexing method for Scale object")
        return Note(self.scale[index%7],4+index//7)

class AudioListener:
    length = 2000
    sample_rate = 44100
    downsample = 1
    def __init__(self):
        self.q = queue.Queue()
        self.stream = sd.InputStream(
                device=1, channels=2,
                samplerate=44100, callback=self.audio_callback)
    def latest_note(self):
        return None
    def audio_callback(self, indata, frames, time, status):
        '''
        Called for every block of audio read in by mic
        '''
        result = indata[::self.downsample].copy()
        self.q.put(result)

class HarmonicaInterface(tk.Frame):
    blows = [0,2,4,7,9,11,14,16,18,21]
    draws = [1,4,6,8,10,12,13,15,17,19]
    def __init__(self, master=None, key = "C"):
        super().__init__(master)
        self.master = master
        # Instantiating Style class
        self.label_style = ttk.Style(self.master)
      
        # Changing font-size of all the Label Widget
        self.label_style.configure("TLabel", font=('Arial', 20))

        # Instantiating Style class
        self.button_style = ttk.Style(self.master)
      
        # Changing font-size of all the Label Widget
        self.button_style.configure("TButton", font=('Arial', 20))
        self.pack()
        self.key = key
        self.scale = Scale(self.key)
        self.blownotes = self.scale[self.blows]
        self.drawnotes = self.scale[self.draws]
        self.bbnotes = deepcopy(self.blownotes)
        self.dbnotes = deepcopy(self.drawnotes)
        for note in self.bbnotes+self.dbnotes:
            note.diminish()
        self.create_widgets()
        self['borderwidth'] = 10
        self['relief'] = 'flat'
        
    def create_widgets(self):
        self.holes = []
        self.blows = []
        self.draws = []
        self.drawbends = []
        ttk.Label(self,text="Blow Notes").grid(row=0,column=0)
        ttk.Label(self,text="Draw Notes").grid(row=2,column=0)
        ttk.Label(self,text="Draw Bends").grid(row=3,column=0)

        for col in range(10):
            hole = ttk.Label(self,text=f"{col+1}")
            hole.grid(row = 1, column=col+1)
            self.holes.append(hole)
            hole["padding"] = 15
            hole['borderwidth'] = 10
            hole['relief'] = 'sunken'
            
            blow = ttk.Label(self,
                              text = str(self.blownotes[col]).strip("'").replace("-",""))
            blow.grid(row = 0, column=col+1)
            self.blows.append(blow)
            
            draw = ttk.Label(self, text = str(self.drawnotes[col]).strip("'").replace("-",""))
            draw.grid(row = 2, column=col+1)
            self.draws.append(draw)
            
            drawbend = ttk.Label(self, text = str(self.dbnotes[col]).strip("'").replace("-",""))
            drawbend.grid(row = 3, column=col+1)
            self.drawbends.append(drawbend)
        for lbl in self.draws+self.blows+self.drawbends:
            lbl["padding"] = 15
            lbl['borderwidth'] = 10
            lbl['relief'] = 'raised'
            lbl['background'] = "gainsboro"
    def get_widget_corresponding_to(self,note):
        if note in self.blownotes:
            return self.blows[self.blownotes.index(note)]
        elif note in self.drawnotes:
            return self.draws[self.drawnotes.index(note)]
        elif note in self.dbnotes:
            return self.drawbends[self.dbnotes.index(note)]
        else:
            raise ValueError("Note cannot be played on diatonic harmonica")
        

class Application(tk.Frame):
    def __init__(self, master=None):
        self.note = None
        self.listener = AudioListener()
        self.audiodata = np.zeros((self.listener.length,2))
        super().__init__(master,width=1000, height=500)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.harmonica = HarmonicaInterface(self,"A")
        self.harmonica.pack(side="top")
        self.quit = ttk.Button(self, text="Quit Harmonicizer",
                              command=self.master.destroy)
        self.quit.pack(side="bottom")


    def update(self):
        while True:
            try:
                data = self.listener.q.get_nowait()
            except queue.Empty:
                break
            shift = len(data)
            self.audiodata = np.roll(self.audiodata, -shift, axis=0)
            self.audiodata[-shift:, :] = data
        note = fft.find_Note(self.audiodata[:,0],
                                     freq = self.listener.sample_rate,
                                     bits=16)
        self.highlight_note(note)
        self.master.after(100,self.update)
        
    def highlight_note(self,note):
        try:
            widget = self.harmonica.get_widget_corresponding_to(note)
        except ValueError:
            return
        widget.config(background="red")
        if self.note is not None:
            self.note.config(background = "gainsboro")
        self.note = widget
        
root = tk.Tk()
root.title("Harmonicizer")
root.geometry("1800x500")
app = Application(master=root)
root.after(100,app.update())
with app.listener.stream:
    app.mainloop()