import numpy as np


def the_line(index):
    list_line = [1780, 1780, 1880, 2820, 1830, 1250, 3340, 2870, 2770, 3220]
    return list_line[index - 1]

def intervals(a_list):
    interval_dict=[]
    interval_list = []
    for index, element in enumerate(a_list):
        pass

def scale_feature():
    keyboard =['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
    cminor = [1, 3, 5, 6, 8, 10, 11] 
        

def load_midi(index):
    list_dir = ['IMSLP172781-WIMA.cb18-wtc01.mid', 'IMSLP172782-WIMA.4be2-wtc02.mid', 'IMSLP172783-WIMA.6463-wtc03.mid', 'IMSLP172784-WIMA.abfc-wtc04.mid', 'IMSLP172785-WIMA.ef02-wtc05.mid', 'IMSLP172786-WIMA.0ba4-wtc06.mid', 'IMSLP172787-WIMA.8225-wtc07.mid', 'IMSLP172788-WIMA.3304-wtc08.mid', 'IMSLP172789-WIMA.31e9-wtc09.mid', 'IMSLP172790-WIMA.bdf9-wtc10.mid', 'IMSLP172791-WIMA.5655-wtc11.mid', 'IMSLP172792-WIMA.d23a-wtc12.mid', 'IMSLP172795-WIMA.a1b8-wtc13.mid', 'IMSLP172796-WIMA.2054-wtc14.mid', 'IMSLP172797-WIMA.94b4-wtc15.mid', 'IMSLP172798-WIMA.307d-wtc16.mid', 'IMSLP172799-WIMA.9023-wtc17.mid', 'IMSLP172800-WIMA.0bc8-wtc18.mid', 'IMSLP172801-WIMA.416d-wtc19.mid', 'IMSLP172802-WIMA.b066-wtc20.mid', 'IMSLP172803-WIMA.4300-wtc21.mid', 'IMSLP172804-WIMA.3f80-wtc22.mid', 'IMSLP172805-WIMA.6bc3-wtc23.mid', 'IMSLP172806-WIMA.68b1-wtc24.mid']
    if index < 25:
        print('you are on {}'.format(list_dir[index-1]))
        return list_dir[index-1]
    else:
        print('out of range!')
        quit() 
