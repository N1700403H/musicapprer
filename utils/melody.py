import numpy as np

def melodyKernel(midiMat, melodyStart):
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
                if map[i,j,k] > threshold:
                    if map[i,j,k]>map[i,j,k-1] and map[i,j,k]>map[i,j,k+1] and map[i,j,k]>map[i,j-1,k] and map[i,j,k]>map[i,j+1,k]:
                        peakIndex.append([i, j, k, map[i,j,k]])
    return peakIndex

def gather_subject(peaks, midiMat, melodyKernel):
        subject = []
        for peak in peaks:
            subject.append([peak, midiMat[peak[0], peak[1]:peak[1]+np.size(melodyKernel, 0), peak[2]:peak[2]+np.size(melodyKernel, 1)]])
        return subject

