from abc import abstractmethod

from gensound import Gain, Sine, Triangle, Sawtooth, Square, Silence, Raw, Shift
from typing import Union

from . import Instrument
from .. import Note, Chord, Pause
from ..wav import WAVWrapper
from ..pitch_shift import pitch_shift


class BasicSynth(Instrument):
    def __init__(self, midi: list[Union[Note, Chord, Pause]], sample_rate: int = 44100):
        super().__init__(midi, sample_rate)
        self.__build_internal_representation()

    @abstractmethod
    def instrument_builder(self, note: Note):
        pass

    def play(self):
        self.__internal.play(sample_rate=self.sample_rate)

    def __build_internal_representation(self):
        self.__internal = Silence() * 0
        current_timestamp = 0.00

        for item in self.midi:
            if isinstance(item, Note):
                self.__internal[current_timestamp + item.shift:] += self.instrument_builder(item)
            elif isinstance(item, Chord):
                chord = self.instrument_builder(item.root_note)
                for note in item.notes[1:]:
                    chord += self.instrument_builder(note)

                self.__internal[current_timestamp + item.shift:] += chord
                self.__internal = self.__internal.mixdown(sample_rate=self.sample_rate)
                self.__internal = Raw(self.__internal)

            current_timestamp += (item.duration + item.shift)

        self.__internal *= Gain(-12)


class SineSynth(BasicSynth):
    def instrument_builder(self, note: Note):
        return Sine(str(note), note.duration)


class SquareSynth(BasicSynth):
    def instrument_builder(self, note: Note):
        return Square(str(note), note.duration)


class SawtoothSynth(BasicSynth):
    def instrument_builder(self, note: Note):
        return Sawtooth(str(note), note.duration)


class TriangleSynth(BasicSynth):
    def instrument_builder(self, note: Note):
        return Triangle(str(note), note.duration)

class Sampler(BasicSynth):
    def __init__(self, filename: str, note: Note):
        self.filename = filename
        self.note = note
        self.wav = WAVWrapper(filename)
    
    def instrument_builder(self, note: Note):
        g=lambda q:[0,2,3,5,7,8,10][ord(q[0])-65]+" #".find(q.ljust(2)[1])
        f=lambda a,b:(g(b)+~g(a))%12+2
        original_note = str(self.note)
        new_note = str(note)
        original_octave = 3
        new_octave = 3
        octaves = {str(i) for i in range(0, 10)}
        if original_note[-1] in octaves:
            original_octave = int(original_note[-1])
            original_note = original_note[:-1]
        if new_note[-1] in octaves:
            new_octave = int(new_note[-1])
            new_note = new_note[:-1]
        
        print(str(original_note), str(new_note))
        print(str(original_octave), str(new_octave))
        
        difference = f(str(original_note), str(new_note)) + ((new_octave - original_octave) * 12)
        return pitch_shift(self.wav, difference)