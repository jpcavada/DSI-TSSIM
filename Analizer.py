import sys, getopt, os
import numpy
import numpy as np
import matplotlib.pyplot as plt

'''
Calcula estadisticas
Promedio de Relocaciones
Promedio de Relocaciones Cortas
Promedio de Relocaciones Medias
Promedio de Relocaciones Largas

Para el intervalo
1 meses = 43200
2 meses = 86400
180 dias = 259200
'''

#START_RECOUNT_TS = 43200
#END_RECOUNT_TS = 86400
END_RECOUNT_TS = 259200
START_RECOUNT_TS = 0

MOV_COST = [1, 3, 7]
DIRPATH = r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\INSTANCES_180D_F17\Salidas\MM"


def getRelocationStatistics(graph=True):
    total_reloc = []
    c_reloc = []
    m_reloc = []
    l_reloc = []

    box_n = []
    # Read all files on 1 go
    iter = 0
    for root, dirs, files in os.walk(DIRPATH, topdown=False):
        for name in files:

            # Get relocations info
            if name.endswith("relocations.txt"):
                total_reloc.append(0)
                c_reloc.append(0)
                m_reloc.append(0)
                l_reloc.append(0)
                print("Mirando {}".format(name))
                fopen = open(os.path.join(root, name))
                for line in fopen.readlines():
                    if line[:1] != "#":
                        # Example line #BOX_NAME,CALL_TIME,EXECUTION_TIME,CALLER_BOX,MOVCOST,
                        line_split = line.split(",")
                        if START_RECOUNT_TS <= int(line_split[1]) <= END_RECOUNT_TS:
                            mov_cost = int(line_split[4])
                            total_reloc[-1] += 1
                            if mov_cost == MOV_COST[0]: c_reloc[-1] += 1
                            if mov_cost == MOV_COST[1]: m_reloc[-1] += 1
                            if mov_cost == MOV_COST[2]: l_reloc[-1] += 1

            # Get Ocuppation info
            elif name.endswith("counter_day.txt"):
                print("Mirando {}".format(name))
                aux_box_n = []
                fopen = open(os.path.join(root, name))
                for line in fopen.readlines():
                    if line[:1] != "#":
                        # Example line #TIME; BOXN,
                        line_split = line.split(",")
                        if START_RECOUNT_TS <= int(line_split[0]) <= END_RECOUNT_TS:
                                aux_box_n.append(int(line_split[1]))
                box_n.append(aux_box_n)


    #for i in range(len(box_n)):
    #    print(i, box_n[i])
    #for day in range(len(box_n[0])):
    #    print(day)
    #IMPRIME RELOC STATS
    fopen2 = open(DIRPATH+"\\_Relocations_Stat.txt","w+")
    fopen2.write("Relocaciones\n")
    fopen2.write("Total, {}\n".format(total_reloc))
    fopen2.write("Close, {}\n".format(c_reloc))
    fopen2.write("Med, {}\n".format(m_reloc))
    fopen2.write("Long, {}\n".format(l_reloc))
    fopen2.close()

    double_array = np.array(box_n)
    #AXIS 1 : Escenarios, AXIS 2: DIAS
    promedio_por_dia = np.average(double_array, axis=0)
    std_por_dia = np.std(double_array, axis=0)


    plt.figure()
    plt.title("N de Contenedores en el patio")
    plt.axhline(y=768, color='r', linestyle='-')
    plt.plot(promedio_por_dia)
    plt.show()


def main(argv):
    getRelocationStatistics(graph=True)


if __name__ == '__main__':
    main(sys.argv[1:])
