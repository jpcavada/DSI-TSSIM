from matplotlib import pyplot as plt
import utilidades
from pathlib import Path
import numpy

run_1_p = Path('INSTANCES', 'RESULTADOS', 'CC-Test', 'C_01_relocations.txt')
run_2_p = Path('INSTANCES',  'RESULTADOS', 'MM-S', 'C_01_relocations.txt')


def read_data(path):
    relocaciones = []
    file = open(path, 'r')
    for line in file.readlines():
        if line[0] != '#':
            tokens = line.split(",")
            dia, hora, minuto = utilidades.real_time(int(tokens[1]))
            r = {'dia': dia,
                 'hora': hora,
                 'min': minuto,
                 'cost': 4}
            relocaciones.append(r)
    return relocaciones


rel_1 = read_data(run_1_p)
rel_2 = read_data(run_2_p)

rel_dia_1 = numpy.zeros(68)
rel_dia_2 = numpy.zeros(68)
rel_cost_1 = numpy.zeros(68)
rel_cost_2 = numpy.zeros(68)
for r in rel_1:
    rel_dia_1[r['dia']] += 1
    rel_cost_1[r['dia']] += r['cost']

for r in rel_2:
    rel_dia_2[r['dia']] += 1
    rel_cost_2[r['dia']] += r['cost']

fig, ax = plt.subplots(2)

ax[0].plot(rel_dia_1, label='Controller')
ax[0].plot(rel_dia_2, label='MM-S')
ax[0].legend()

ax[1].plot(rel_cost_1, label='Controller')
ax[1].plot(rel_cost_2, label='MM-S')
ax[1].legend()

plt.show()





