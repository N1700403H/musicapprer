import mido
import numpy as np

def getTempo(MetaMsg):
    # further update needed for the midi file with multiple tempo change
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

def midiMatrix(filepath):
    mid = mido.MidiFile(filepath)
    MetaMsg = getMetaMessage(mid)
    tempo = getTempo(MetaMsg)
    numChannel, length, width = getScale(mid)
    print('\n\n####The size of the midi matrix is   {0}, {1}, {2}####\n\n'.format(numChannel, length, width))
    midiMat = np.zeros((len(numChannel), length, width), dtype='int8')
    note_hit_list = [0 for _ in range(128)]
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
                    note_hit_list[msg.note] += 1
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
    shorter = tenTimesShorter(midiMat)
    return shorter, np.amax(shorter, axis=0), note_hit_list

