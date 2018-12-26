import mido
import matplotlib.pyplot as plt
import cv2
import re
import os
import argparse
import subprocess
import numpy as np
from PIL import Image

# extract information from midi file
def getTempo(MetaMsg):
    for track in MetaMsg:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
    try: tempo
    except NameError: tempo = 500000
    return tempo


def getScale(mid):
    numTracks = len(mid.tracks)
    durations = [0] * numTracks
    numChannel = set({})
    for index, track in enumerate(mid.tracks):
            for msg in track:
                    durations[index] += msg.time
                    if msg.type == 'note_on':
                        numChannel.add(msg.channel)
    # print(len(numChannel))
    return list(numChannel), max(durations), 128


def getMetaMessage(mid):
    numTracks = len(mid.tracks)
    MetaMessage = [[]] * numTracks
    for index, track in enumerate(mid.tracks):
        for msg in track:
            if type(msg) == mido.midifiles.meta.MetaMessage:
                MetaMessage[index].append(msg)
    return MetaMessage


def midiMatrix(filepath):
    mid = mido.MidiFile(filepath)
    MetaMsg = getMetaMessage(mid)
    tempo = getTempo(MetaMsg)
    numChannel, length, width = getScale(mid)
    print('\n\n####The size of the midi matrix is   {0}, {1}, {2}####\n\n'.format(numChannel, length, width))
    midiMat = np.zeros((len(numChannel), length, width), dtype = 'int8')
    for trackIndex, track in enumerate(mid.tracks):
        noteRegister = [-1] * 128
        currentTime = 0
        for msg in track:
            # print(msg)
            currentTime += msg.time
            if msg.type == 'note_on':
                if  msg.velocity == 0:
                    if noteRegister[msg.note] != -1:
                        # print(currentTime - noteRegister[msg.note])
                        for slot in [currentTime-x for x in range(currentTime-noteRegister[msg.note])]:
                            midiMat[numChannel.index(msg.channel), slot-1, msg.note] = 1
                        noteRegister[msg.note] = -1
                else:
                    if noteRegister[msg.note] == -1:
                        noteRegister[msg.note] = currentTime
                    else:
                        print(noteRegister[msg.note] == -1)
                        for slot in [currentTime-x for x in range(currentTime-noteRegister[msg.note])]:
                            midiMat[numChannel.index(msg.channel), slot-1, msg.note] = 1
                        noteRegister[msg.note] = currentTime

            if msg.type == 'note_off':
                if noteRegister[msg.note] != -1:
                    for slot in [currentTime-x for x in range(currentTime-noteRegister[msg.note])]:
                        midiMat[numChannel.index(msg.channel), slot-1, msg.note] = 1
                    noteRegister[msg.note] = -1

    print('the non-zero elements count {0} in the midi matrax\n\n'.format(np.count_nonzero(midiMat)))
    return midiMat, tempo, mid.ticks_per_beat


def printFrame(midiMat,filepath):
    im = Image.fromarray(np.flipud(np.transpose(midiMat))*25, mode ='L')
    im.save(filepath.replace('.mid', '.bmp'), 'bmp')


def melodyKernel(midiMat):
    melodyStart = 1784
    # melodyStart = 0
    while midiMat[:,melodyStart,:].sum()==0:
        melodyStart += 1
    melodyEnd = melodyStart
    print('melody starts at {}'.format(melodyEnd))
    while midiMat[:,melodyEnd,:].sum()<=10:
        melodyEnd += 1
    print('melody ends at {}'.format(melodyEnd))
    melodyBlock = midiMat[:,melodyStart: melodyEnd,:]
    # print(melodyBlock.amax)
    for chann in melodyBlock:
        if chann.sum() > 100:
            melody = chann
    if_note = melody.sum(axis=0)
    top = 0
    bottom = 127
    while if_note[top] == 0:
        top += 1
    while if_note[bottom] == 0:
        bottom -= 1
    # get the index of 1 so the upper limit and the botton limit can be set
    kernel = melody[:,top:bottom+1 ]
    print(kernel)
    print('bottom is {}, top is {}'.format(bottom, top))
    bias = np.ones((np.size(kernel,0),np.size(kernel,1)),dtype = 'int8')
    melody = kernel *2 - bias*10
    return melody, (melody*kernel).sum()


def convolutionMap(midiMat, melodyKernel):
    width_midimat = np.size(midiMat, 2)
    width_kernel = np.size(melodyKernel, 1)
    print(width_kernel)
    length_midimat = np.size(midiMat, 1)
    length_kernel = np.size(melodyKernel, 0)
    conMap = np.empty((np.size(midiMat,0), length_midimat-length_kernel, width_midimat-width_kernel), dtype = 'int32')
    for i in range(np.size(conMap,0)):
        for j in range(np.size(conMap,1)):
            for k in range(np.size(conMap,2)):
                # if j == 0 and k ==15:
                    # print(np.size(midiMat[j:j+length_kernel,k:k+width_kernel],1))
                    # print((melodyKernel*midiMat[j:j+length_kernel,k:k+width_kernel]).sum())
                conMap[i,j,k] = (melodyKernel*midiMat[i,j:j+length_kernel,k:k+width_kernel]).sum()
    return conMap


def findPeak(map, threshold):
    peakIndex = []
    for i in range(np.size(map,0)):
        for j in range(np.size(map,1)-1):
            for k in range(np.size(map,2)):
                if map[i,j,k] > 2000:
                    if map[i,j,k]>map[i,j,k-1] and map[i,j,k]>map[i,j,k+1] and map[i,j,k]>map[i,j-1,k] and map[i,j,k]>map[i,j+1,k]:
                        peakIndex.append([i, j, k, map[i,j,k]])
    return peakIndex


def showfoundmelody(peakindex, midiMat, melodyKernel):
    labeledMat = np.amax(midiMat, axis=0)
    Ashape = np.array([[1,1,0,0,0],[0,1,1,0,0],[0,1,0,1,0],[1,1,1,1,1],[0,0,0,0,0]])
    Bshape = np.array([[1,1,1,1,1],[1,0,1,0,1],[1,0,1,0,1],[0,1,0,1,0],[0,0,0,0,0]])
    Cshape = np.array([[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,0,0,0,0],[0,0,0,0,0]])
    Dshape = np.array([[1,1,1,1,1],[1,0,0,0,1],[0,1,1,1,0],[0,0,0,0,0],[0,0,0,0,0]])
    Eshape = np.array([[1,1,1,1,1],[1,0,1,0,1],[1,0,1,0,1],[1,0,1,0,1],[0,0,0,0,0]])
    Fshape = np.array([[1,1,1,1,1],[0,0,1,0,1],[0,0,1,0,1],[0,0,1,0,1],[0,0,0,0,0]])
    Gshape = np.array([[1,1,1,1,1],[1,0,0,0,1],[1,1,1,0,1],[0,0,0,0,1],[0,0,0,0,0]])
    Asshape = np.array([[1,1,0,0,0],[0,1,1,0,0],[0,1,0,1,0],[1,1,1,1,1],[0,0,0,1,1]])
    Bsshape = np.array([[1,1,1,1,1],[1,0,1,0,1],[1,0,1,0,1],[0,1,0,1,0],[0,0,0,1,1]])
    Csshape = np.array([[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,0,0,1,0],[0,0,0,1,1]])
    Dsshape = np.array([[1,1,1,1,1],[1,0,0,0,1],[0,1,1,1,0],[0,0,0,0,0],[0,0,0,1,1]])
    Esshape = np.array([[1,1,1,1,1],[1,0,1,0,1],[1,0,1,0,1],[1,0,1,0,1],[0,0,0,1,1]])
    Fsshape = np.array([[1,1,1,1,1],[0,0,1,0,1],[0,0,1,0,1],[0,0,1,0,1],[0,0,0,1,1]])
    Gsshape = np.array([[1,1,1,1,1],[1,0,0,0,1],[1,1,1,0,1],[0,0,0,0,1],[0,0,0,1,1]])
    notes_translator=[Ashape,Asshape,Bshape,Cshape,Csshape,Dshape,Dsshape,Eshape,Fshape,Fsshape,Gshape,Gsshape]
    for peak in peakindex:
        notes = peak[2]+np.nonzero(midiMat[peak[0], peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]:peak[2]+np.size(melodyKernel, 1)])[1]
        notes = np.sort(np.array(list(set(notes))))
        the_note = (notes[0]-21) % 12
        major_or_minor = notes[2]- notes[1]
        # 1 -> minor, 2 -> major
        labeledMat[peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]-1] = 5
        labeledMat[peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]+np.size(melodyKernel, 1)] = 5
        labeledMat[peak[1], 0:peak[2]+np.size(melodyKernel, 1)] = 5
        labeledMat[peak[1]+np.size(melodyKernel, 0), peak[2]:peak[2]+np.size(melodyKernel, 1)] = 5
        the_label = notes_translator[the_note]
        if major_or_minor == 1:
            the_label[4,0:2] = 1
        labeledMat[peak[1]:peak[1]+5, 0:5] = the_label*5
    return labeledMat

def showplausiblemelody(peakindex, midiMat, melodyKernel):
    labeledMat = np.amax(midiMat, axis=0)
    Ashape = np.array([[1,1,0,0,0],[0,1,1,0,0],[0,1,0,1,0],[1,1,1,1,1],[0,0,0,0,0]])
    Bshape = np.array([[1,1,1,1,1],[1,0,1,0,1],[1,0,1,0,1],[0,1,0,1,0],[0,0,0,0,0]])
    Cshape = np.array([[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,0,0,0,0],[0,0,0,0,0]])
    Dshape = np.array([[1,1,1,1,1],[1,0,0,0,1],[0,1,1,1,0],[0,0,0,0,0],[0,0,0,0,0]])
    Eshape = np.array([[1,1,1,1,1],[1,0,1,0,1],[1,0,1,0,1],[1,0,1,0,1],[0,0,0,0,0]])
    Fshape = np.array([[1,1,1,1,1],[0,0,1,0,1],[0,0,1,0,1],[0,0,1,0,1],[0,0,0,0,0]])
    Gshape = np.array([[1,1,1,1,1],[1,0,0,0,1],[1,1,1,0,1],[0,0,0,0,1],[0,0,0,0,0]])
    Asshape = np.array([[1,1,0,0,0],[0,1,1,0,0],[0,1,0,1,0],[1,1,1,1,1],[0,0,0,1,1]])
    Bsshape = np.array([[1,1,1,1,1],[1,0,1,0,1],[1,0,1,0,1],[0,1,0,1,0],[0,0,0,1,1]])
    Csshape = np.array([[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,0,0,1,0],[0,0,0,1,1]])
    Dsshape = np.array([[1,1,1,1,1],[1,0,0,0,1],[0,1,1,1,0],[0,0,0,0,0],[0,0,0,1,1]])
    Esshape = np.array([[1,1,1,1,1],[1,0,1,0,1],[1,0,1,0,1],[1,0,1,0,1],[0,0,0,1,1]])
    Fsshape = np.array([[1,1,1,1,1],[0,0,1,0,1],[0,0,1,0,1],[0,0,1,0,1],[0,0,0,1,1]])
    Gsshape = np.array([[1,1,1,1,1],[1,0,0,0,1],[1,1,1,0,1],[0,0,0,0,1],[0,0,0,1,1]])
    notes_translator=[Ashape,Asshape,Bshape,Cshape,Csshape,Dshape,Dsshape,Eshape,Fshape,Fsshape,Gshape,Gsshape]
    for peak in peakindex:
        notes = peak[2]+np.nonzero(midiMat[peak[0], peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]:peak[2]+np.size(melodyKernel, 1)])[1]
        # notes = np.array(list(set(notes)))
        the_note = (notes[0]-21) % 12
        major_or_minor = 1
        # 1 -> minor, 2 -> major
        labeledMat[peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]-1] = 5
        labeledMat[peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]+np.size(melodyKernel, 1)] = 5
        labeledMat[peak[1], 0:peak[2]+np.size(melodyKernel, 1)] = 5
        labeledMat[peak[1]+np.size(melodyKernel, 0), peak[2]:peak[2]+np.size(melodyKernel, 1)] = 5
        the_label = notes_translator[the_note]
        if major_or_minor == 1:
            the_label[4,0:2] = 1
        labeledMat[peak[1]:peak[1]+5, 0:5] = the_label*5
    return labeledMat


def matWithLabel(peakindex, midiMat, melodyKernel):
    labeledMat = np.amax(midiMat, axis=0)
    for peak in peakindex:
        # threshold
        # print(np.size(melodyKernel,1))
        labeledMat[peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]-1] = 5
        labeledMat[peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]+np.size(melodyKernel, 1)] = 5
        labeledMat[peak[1], peak[2]:peak[2]+np.size(melodyKernel, 1)] = 5
        labeledMat[peak[1]+np.size(melodyKernel, 0), peak[2]:peak[2]+np.size(melodyKernel, 1)] = 5
    return labeledMat


def tenTimesShorter(mat):
    numChannel = np.size(mat, 0)
    length = np.size(mat, 1)
    width = np.size(mat, 2)
    newMat = np.empty((numChannel, length//10+1, width), dtype = 'int8')
    for i in range(np.size(newMat,0)):
        for j in range(np.size(newMat,1)):
            for k in range(np.size(newMat,2)):
                newMat[i,j,k] = mat[i,10*j:10*j+10, k].sum()
    return newMat


# def translateNote(melodyKernel, peaks):
#     notes = []
#     note = np.nonzero(melodyKernel > 0)
#     print(note[1])
#     for peak in peaks:
#         if peak[2] > 2000:
#             melodyNote = set({})
#             for key in note[1]:
#                 melodyNote.add(peak[1]+key)
#             notes.append(list(melodyNote))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='turn a midi file in to a graph')
    parser.add_argument('midi_file', nargs='?', help = 'path to midi file', default = 'IMSLP211238-WIMA.3540-1047(I)Sco.mid')
    parser.add_argument('whether_video', nargs='?', help = 'whether to output video', default = 'No')
    args = parser.parse_args()
    # end of -- listening to the parameters

    np.set_printoptions(threshold=np.inf)
    np.set_printoptions(linewidth=np.inf)
    # end of -- set print options for matrix

    spf = 1
    # this is second per frame

    try:
        midiMat = np.load(args.midi_file.replace('.mid', '.npy'))
        with open(args.midi_file.replace('.mid', '.txt'), 'r') as file:
            content = file.readlines()
            tempo = int(content[0].strip())
            ticks_per_beat = int(content[1])
    except FileNotFoundError:
        midiMat, tempo, ticks_per_beat = midiMatrix(args.midi_file)
        with open(args.midi_file.replace('.mid', '.txt'), 'w') as file:
            file.write(str(tempo))
            file.write('\n')
            file.write(str(ticks_per_beat))
        np.save(args.midi_file.replace('.mid', '.npy'), midiMat)

    midiMat = tenTimesShorter(midiMat)
    # for chann in midiMat:
        # print(chann)
    print(np.size(midiMat,1))
    print(np.size(midiMat,1))
    midikernel, threshold = melodyKernel(midiMat)
    print(threshold)
    threshold = 2*threshold/3
    # print(midikernel)
    # print(midiMat.sum(axis=0))
    try:
        conMap = np.load(args.midi_file.replace('.mid', '_con.npy'))
    except FileNotFoundError:
        conMap = convolutionMap(midiMat,midikernel)
        np.save(args.midi_file.replace('.mid', '_con.npy'), conMap)
    # print(conMap[0])
    # # print(conMap)
    # # print(conMap)
    peaks = findPeak(conMap, threshold)
    print(peaks)
    # print(np.size(midiMat.sum(axis=0),1))
    labeledMat = showplausiblemelody(peaks, midiMat, midikernel)
    printFrame(labeledMat, args.midi_file)
    # print(labeledMat)
    # showfoundmelody(peaks, midiMat, midikernel)
