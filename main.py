import numpy as np
from utils.util import the_line, load_midi
from os.path import exists, join
from utils.matize import midiMatrix
from utils.melody import melodyKernel, convolutionMap, findPeak, gather_subject
import utils.util as util

class midi():
    def __init__(self, index):
        self.index = index
        self.name = load_midi(index)
        self.prelude_stop = the_line(index)
        self.keyboard = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
        self.path = join('midi', self.name)
        self.subject = None
        self.layered_mat = None
        self.mat = None
        self.note_hit_list = None
        self.note_hit_in_scale = None
        self.peak_threshold = None
        self.conMap = None
        self.theme = None
        self.subject_list = None
        np.set_printoptions(threshold=np.inf)
        np.set_printoptions(linewidth=np.inf)

    def to_mat(self):
        self.layered_mat, self.mat, self.note_hit_list = midiMatrix(join('midi', self.name))
        np.save(join('midi', self.name.replace('.mid', '.npy')), self.layered_mat)
        self.note_hit_in_scale = [0 for _ in range(12)]
        for index, num in enumerate(self.note_hit_list):
            self.note_hit_in_scale[(index-21)%12] += num
        


    def load_mat(self):
        if exists(self.path.replace('.mid', '.npy')):
            self.layered_mat = np.load(self.path.replace('.mid', '.npy'))
        else:
            print('no {} found in the midi folder'.format(self.name))
            quit()

    def find_subject(self):
        self.theme, self.peak_threshold = melodyKernel(self.layered_mat, util.the_line(self.index))
        self.peak_threshold = 2*self.peak_threshold / 3
        self.conMap = convolutionMap(self.layered_mat, self.theme)
        peaks = findPeak(self.conMap, self.peak_threshold)
        self.subject_list = gather_subject(peaks, self.layered_mat, self.theme)

