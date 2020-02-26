import numpy as np
import matplotlib.pyplot as plt

def cuenta_de_boxes(filename):
    file = open(filename, 'r')
    time_step =[]
    number_of_boxes = []
    for line in file.readlines():
        if not (line[:1] == '#'):
            tokens = line.split(",")
            time_step.append(int(tokens[0])/1440)
            number_of_boxes.append(int(tokens[1]))

    print(time_step)

    trimmed_ts = time_step[::1]
    trimmed_nb = number_of_boxes[::1]
    plt.figure()
    plt.plot(trimmed_ts, trimmed_nb)
    plt.show()

cuenta_de_boxes('output_files\export_box_counter.txt')