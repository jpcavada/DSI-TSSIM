import sys, getopt, os
import numpy
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scipy.stats

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

matplotlib.rcParams.update({'font.size': 12})
plt.ioff()
# START_RECOUNT_TS = 43200
# END_RECOUNT_TS = 86400
END_RECOUNT_TS = 259200
#START_RECOUNT_TS = 86400
START_RECOUNT_TS = 0
MOV_COST = [1, 3, 7]


# DIRPATH = r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\INSTANCES_180D_F17\Salidas\MM"

def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a, ddof=1)
    sd = np.std(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n - 1)
    return m, sd, m - h, m + h


def getRelocationStatistics(DIRPATH):
    total_reloc = []
    c_reloc = []
    m_reloc = []
    l_reloc = []

    avg_n_unique_relocs = []
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
                unique_reloc = []
                # print("Mirando {}".format(name))
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

                            if line_split[3] not in unique_reloc:
                                unique_reloc.append(line_split[3])

                if len(unique_reloc) > 0:
                    avg_n_unique_relocs.append(total_reloc[-1] / len(unique_reloc))
                else:
                    avg_n_unique_relocs.append(0)

            # Get Ocuppation info
    # print(avg_n_unique_relocs)
    return total_reloc, c_reloc, m_reloc, l_reloc


def getOccupationStats(DIRPATH):
    box_n = []
    for root, dirs, files in os.walk(DIRPATH, topdown=False):
        for name in files:
            if name.endswith("counter_day.txt"):
                # print("Mirando {}".format(name))
                aux_box_n = []
                fopen = open(os.path.join(root, name))
                for line in fopen.readlines():
                    if line[:1] != "#":
                        # Example line #TIME; BOXN,
                        line_split = line.split(",")
                        if START_RECOUNT_TS <= int(line_split[0]) <= END_RECOUNT_TS:
                            aux_box_n.append(int(line_split[1]))

                box_n.append(aux_box_n)

    double_array = np.array(box_n)
    # AXIS 1 : Escenarios, AXIS 2: DIAS
    promedio_por_dia = np.average(double_array, axis=0)
    std_por_dia = np.std(double_array, axis=0)

    return promedio_por_dia


def main_ocupacion():
    # CODIGO PARA GENERAR GRAFICOS DE OCUPACION

    f2 = getOccupationStats(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\antigups\MM")
    #f3 = getOccupationStats(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F3\MM")
    f25 = getOccupationStats(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F25\MM")
    #f175 = getOccupationStats(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18_100\MM")
    f18 = getOccupationStats(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18\MM")

    start_point = 90
    ro_f2 = numpy.round(numpy.average(f2[start_point:]) / 768, 2)
    #ro_f3 = numpy.round(numpy.average(f3[start_point:]) / 768, 2)
    ro_f25 = numpy.round(numpy.average(f25[start_point:]) / 768, 2)
    #ro_f175 = numpy.round(numpy.average(f175[start_point:]) / 768, 2)
    ro_f18 = numpy.round(numpy.average(f18[start_point:]) / 768, 2)

    plt.rc('font', size=10)
    plt.rc('axes', titlesize=12)
    plt.figure()
    #plt.title("N de Contenedores en el patio")
    plt.axhline(y=768, color='blue', linestyle='-')
    plt.axvline(x=90, color="grey", linestyle="--")
    plt.plot(f2, label="Medium", color="C1")
    #plt.plot(f3, label="f3", color="C1")
    plt.plot(f25, label="Low", color="C2")
    #plt.plot(f175, label="f175", color="C3")
    plt.plot(f18, color="C3")

    plt.annotate(r"Medium ($\rho$={})".format(ro_f2), xy=(175, f2[-1]), xytext=(0, -8), textcoords='offset points',
                 ha='right', va="top", color="C1")
    #plt.annotate(r"F3 ($\rho$={})".format(ro_f3), xy=(175, f3[-1]), xytext=(0, -8), textcoords='offset points',
    #             ha='right', va="top", color="C1")
    plt.annotate(r"Low ($\rho$={})".format(ro_f25), xy=(175, f25[-1]), xytext=(0, -8), textcoords='offset points',
                 ha='right', va="top", color="C2")
    #plt.annotate(r"F1.75 ($\rho$={})".format(ro_f175), xy=(175, f175[-1]), xytext=(0, 10), textcoords='offset points',
    #            ha='right', va="bottom", color="C3")
    plt.annotate(r"High ($\rho$={})".format(ro_f18), xy=(175, f18[-1]), xytext=(0, -6), textcoords='offset points',
                 ha='right', va="top", color="C3")
    plt.ylabel("Number of containers")
    plt.ylim(bottom=0)
    plt.xlabel("Simulation Days")
    plt.xlim(left=0)
    plt.xticks(np.arange(0, 190, step=30))

def main_relocaciones():
    scenario_path = [(r"./INSTANCES/Resultados/F18_MM", "DET"),
                     (r"./INSTANCES/Resultados/F18_100_ST", "ST <= bloquea"),
                     (r"./INSTANCES/Resultados/F18_100_ST_E", "ST < bloquea"),
                    # (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18_100\MM-S", "MM-S"),
                    # (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18_100\RI", "RI"),
                    # (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18_100\RI-C", "RI-C "),
                    # (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18_100\RI-S", "RI-S"),
                    # (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18_100\RIL", "RIL"),
                    # (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18_100\RIL-C", "RIL-C"),
                    # (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F18_100\RIL-S", "RIL-S")
                     ]

    scenario_name = "Comparacion MM sin hora de salida"
    rho = 0.77

    box_plot_data = []
    scenario_names = []

    close_data = []     # N° de relocaciones close de cada replica
    medium_data = []    # N° de relocaciones medium de cada replica
    long_data = []      # N° de relocaciones large de cada replica

    CI_data = []

    for scenario, name in scenario_path:
        total, close, medium, long = getRelocationStatistics(scenario)
        box_plot_data.append(total)
        scenario_names.append(name)

        close_data.append(close)
        medium_data.append(medium)
        long_data.append(long)

        CI_data.append(mean_confidence_interval(total))

    # BOXPLOT
    fig, ax = plt.subplots(3)

    fig.suptitle(r'SCENARIO F18 100 Replicas ($\rho$=0.77 )')

    ax[0].set_title(scenario_name)
    ax[0].set_ylabel("Number of Relocations")
    ax[0].boxplot(box_plot_data, labels=scenario_names, notch=True)

    # COST PLOT
    avg_close_relocation = []
    std_close_relocation = []

    avg_med_relocation = []
    std_med_relocation = []

    avg_long_relocation = []
    std_long_relocation = []

    for i in close_data:
        avg_close_relocation.append(numpy.average(i))
        std_close_relocation.append(numpy.std(i))

    for i in medium_data:
        avg_med_relocation.append(numpy.average(i))
        std_med_relocation.append(numpy.std(i))

    for i in long_data:
        avg_long_relocation.append(numpy.average(i))
        std_long_relocation.append(numpy.std(i))

    bottom_long = []
    for i in range(len(close_data)):
        bottom_long.append(avg_close_relocation[i] + avg_med_relocation[i])

    number_bars = numpy.arange(len(avg_close_relocation))

    ax[1].bar(scenario_names, avg_close_relocation, width=0.8, label='Close')
    ax[1].bar(scenario_names, avg_med_relocation, width=0.8, bottom=avg_close_relocation, label='Medium')
    ax[1].bar(scenario_names, avg_long_relocation, width=0.8, bottom=bottom_long, label='Long')

    ax[1].set_title(r"RELOCATIONS BY DISTANCE")
    ax[1].set_xticks(number_bars, scenario_names)
    ax[1].set_ylabel("Number of Relocations")
    ax[1].legend()

    # COST PLOT 2
    relocation_costs = []
    for i in range(len(scenario_names)):
        relocation_costs.append(avg_close_relocation[i] * MOV_COST[0]
                                + avg_med_relocation[i] * MOV_COST[1]
                                + avg_long_relocation[i] * MOV_COST[2])

    ax[2].bar(scenario_names, relocation_costs)

    ax[2].set_title(r"RELOCATIONS COST")
    ax[2].set_ylabel("Expected Cost")

    plt.tight_layout()
    plt.show()

    print("------------------------------------------")
    print("sc \t mean \t std \t CI- \t CI+ \t AV_C \t AV_M \t AV_L")
    print("------------------------------------------")
    # PRINT 0.05% CONFIDENCE INTERVAL
    for i in range(len(scenario_names)):
        print(scenario_names[i]
              + "\t" + str(numpy.round(CI_data[i][0], 1))
              + "\t" + str(numpy.round(CI_data[i][1], 1))
              + "\t" + str(numpy.round(CI_data[i][2], 1))
              + "\t" + str(numpy.round(CI_data[i][3], 1))
              + "\t" + str(np.round(avg_close_relocation[i], 1))
              + "\t" + str(np.round(avg_med_relocation[i], 1))
              + "\t" + str(np.round(avg_long_relocation[i], 1))
              )
    print("------------------------------------------")


# for i in box_plot_data:
#     print(i)
def main_ocupation_by_replica():
    scenarios = [r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\MM-S",
                 r"C:\Users\Juampi\Docum ents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\RIL-C",
                 r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\RIL-S"
                 ]

    box_count = []
    for DIRPATH in scenarios:
        box_n = []
        for root, dirs, files in os.walk(DIRPATH, topdown=False):
            for name in files:
                if name.endswith("counter_day.txt"):
                    # print("Mirando {}".format(name))
                    aux_box_n = []
                    fopen = open(os.path.join(root, name))
                    for line in fopen.readlines():
                        if line[:1] != "#":
                            # Example line #TIME; BOXN,
                            line_split = line.split(",")
                            if 0 <= int(line_split[0]) <= END_RECOUNT_TS:
                                aux_box_n.append(int(line_split[1]))

                    box_n.append(aux_box_n)
            box_count.append(box_n)

    fig, ax = plt.subplots(1, 3)
    for i in range(3):
        ax[i].axhline(y=768, color='r', linestyle='-')
        ax[i].set_ylim(0, 800)

    ax[0].set_title("MM-S")
    for i in box_count[0]:
        ax[0].plot(i)

    ax[1].set_title("RIL-C")
    for i in box_count[1]:
        ax[1].plot(i)

    ax[2].set_title("RIL-S")
    for i in box_count[2]:
        ax[2].plot(i)


def count_box_when_fail(DIRPATH):
    snap_dic = {}
    for root, dirs, files in os.walk(DIRPATH, topdown=False):
        for name in files:
            if name.endswith("_failed_snapshot.txt"):
                # print("Mirando {}".format(name))
                None_count = 0
                fopen = open(os.path.join(root, name))
                for line in fopen.readlines():
                    if line[:1] != "#":
                        None_count = line.count("None") + None_count
                end_pos = name.find("_failed_snapshot.txt")
                start_pos = name[:end_pos].rfind("_") + 1
                snap_dic[name[start_pos:end_pos]] = None_count

    return snap_dic


def main_count_fails():
    scenario_path = [(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F175\MM", "MM"),
                     (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F175\MM-S", "MM-S"),
                     (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F175\RI", "RI"),
                     (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F175\RI-C", "RI-C "),
                     (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F175\RI-S", "RI-S"),
                     (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F175\RIL", "RIL"),
                     (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F175\RIL-C", "RIL-C"),
                     (r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F175\RIL-S", "RIL-S")
                     ]

    eje_x = []
    eje_y = []
    eje_z = []
    for i in range(len(scenario_path)):
        snap = count_box_when_fail(scenario_path[i][0])
        replicas = []
        nones = []
        for k, v in snap.items():
            replicas.append(k)
            nones.append(v)
            # list.append((scenario_path[i][1], int(k), v))
            eje_x.append(scenario_path[i][1])
            eje_y.append(int(k))
            eje_z.append(v)

    print("x:", eje_x)
    print("y:", eje_y)
    print("z:", eje_z)

    eje_z_2 = [str(i).replace(str(i), r"$" + str(i) + r"$") for i in eje_z]

    print(eje_z_2)
    # list tiene el formato (Nombre_serie, lista_nombre_escenario, lista_valores)
    fig1, ax1 = plt.subplots()
    ax1.set_xlabel("Algorithm")
    ax1.set_ylabel("Scenario N°")
    ax1.set_yticks(np.arange(26))
    im = ax1.scatter(eje_x, eje_y, marker="s", c=eje_z, cmap="inferno")
    plt.colorbar(im, ax=ax1)

    # plt.annotate(it[2], (it[0], it[1]), xytext=(0,0), textcoords='offset points')


def getDecisions(DIRPATH):
    # decions 0:RI, 1:RIL, 2:MM, 3:RI-C, 4:RIL-C, 5:RI-S, 6:RIL-S, 7:MM-S
    inbound_decisions = []
    rel_inbound = []
    relocation_decisions = []
    rel_relocation = []

    for root, dirs, files in os.walk(DIRPATH, topdown=False):
        for name in files:
            # Get decisions info
            if name.endswith("decisions.txt"):
                inbound_temp = [0, 0, 0, 0, 0, 0, 0, 0]
                reloc_temp = [0, 0, 0, 0, 0, 0, 0, 0]
                # print("Mirando {}".format(name))
                fopen = open(os.path.join(root, name))
                for line in fopen.readlines():
                    if line[:1] != "#":
                        # 489,C0-0-8;Inbound;RI:LUA1;RIL:LUA1;MM:LUA1;RIC:LUA1;RIL-C:LUA1;RI-S:LUA1;RIL-S:LUA1;MM-S:LUA1;F:MM:LUA1:[None, None, None, None]
                        line = line.replace(",", ";", 1)
                        line_split = line.split(";")
                        if START_RECOUNT_TS <= int(line_split[0]) <= END_RECOUNT_TS:
                            correct_answer = line_split[11].split(":")[2]
                            ri = 0
                            if line_split[3].split(":")[1] == correct_answer:
                                ri = 1
                            ril = 0
                            if line_split[4].split(":")[1] == correct_answer:
                                ril = 1
                            mm = 0
                            if line_split[5].split(":")[1] == correct_answer:
                                mm = 1
                            ric = 0
                            if line_split[6].split(":")[1] == correct_answer:
                                ric = 1
                            rilc = 0
                            if line_split[7].split(":")[1] == correct_answer:
                                rilc = 1
                            ris = 0
                            if line_split[8].split(":")[1] == correct_answer:
                                ris = 1
                            rils = 0
                            if line_split[9].split(":")[1] == correct_answer:
                                rils = 1
                            mms = 0
                            if line_split[10].split(":")[1] == correct_answer:
                                mms = 1
                            if line_split[2] == "Inbound":
                                inbound_temp[0] = inbound_temp[0] + ri
                                inbound_temp[1] = inbound_temp[1] + ril
                                inbound_temp[2] = inbound_temp[2] + mm
                                inbound_temp[3] = inbound_temp[3] + ric
                                inbound_temp[4] = inbound_temp[4] + rilc
                                inbound_temp[5] = inbound_temp[5] + ris
                                inbound_temp[6] = inbound_temp[6] + rils
                                inbound_temp[7] = inbound_temp[7] + mms
                            else:
                                reloc_temp[0] = reloc_temp[0] + ri
                                reloc_temp[1] = reloc_temp[1] + ril
                                reloc_temp[2] = reloc_temp[2] + mm
                                reloc_temp[3] = reloc_temp[3] + ric
                                reloc_temp[4] = reloc_temp[4] + rilc
                                reloc_temp[5] = reloc_temp[5] + ris
                                reloc_temp[6] = reloc_temp[6] + rils
                                reloc_temp[7] = reloc_temp[7] + mms

                rel_inbound.append([i / np.max(inbound_temp) for i in inbound_temp])
                inbound_decisions.append(inbound_temp)
                rel_relocation.append([i / np.max(reloc_temp) for i in reloc_temp])
                relocation_decisions.append(reloc_temp)

    average_rel_inbound = np.average(rel_inbound, axis=0)
    average_rel_relocations = np.average(rel_relocation, axis=0)
    return average_rel_inbound.tolist(), average_rel_relocations.tolist()


def main_decisiones():
    RI, RIr = getDecisions(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\Versus\RI")
    RIL, RILr = getDecisions(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\Versus\RIL")
    MM, MMr = getDecisions(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\Versus\MM")
    RIC, RICr = getDecisions(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\Versus\RI-C")
    RILC, RILCr = getDecisions(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\Versus\RIL-C")
    RIS, RISr = getDecisions(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\Versus\RI-S")
    RILS, RILSr = getDecisions(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\Versus\RIL-S")
    MMS, MMSr = getDecisions(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2\Versus\MM-S")

    print("INBOUND")
    print("{}:{}".format("RI", RI))
    print("{}:{}".format("RIL", RIL))
    print("{}:{}".format("MM", MM))
    print("{}:{}".format("RI-C", RIC))
    print("{}:{}".format("RIL-C", RILC))
    print("{}:{}".format("RI-S", RIS))
    print("{}:{}".format("RIL-S", RILS))
    print("{}:{}".format("MM-S", MMS))

    print("RELOCATIONS")
    print("{}:{}".format("RI", RIr))
    print("{}:{}".format("RIL", RILr))
    print("{}:{}".format("MM", MMr))
    print("{}:{}".format("RI-C", RICr))
    print("{}:{}".format("RIL-C", RILCr))
    print("{}:{}".format("RI-S", RISr))
    print("{}:{}".format("RIL-S", RILSr))
    print("{}:{}".format("MM-S", MMSr))


def getArrivalsAndRemovals(DIRPATH):
    n_arrivals = []
    n_removals = []
    for root, dirs, files in os.walk(DIRPATH, topdown=False):
        for name in files:
            # Get decisions info
            if name.endswith("arrivals.txt"):
                n_temp = 0
                # print("Mirando {}".format(name))
                fopen = open(os.path.join(root, name))
                for line in fopen.readlines():
                    if line[:1] != "#":
                        # BOX_NAME,CALL_TIME,CRANE_TIME,EXECUTION_TIME,line = line.replace(",", ";", 1)
                        line_split = line.split(",")
                        if START_RECOUNT_TS <= int(line_split[3]) <= END_RECOUNT_TS:
                            n_temp += 1
                n_arrivals.append(n_temp)
            if name.endswith("removals.txt"):
                n_temp = 0
                # print("Mirando {}".format(name))
                fopen = open(os.path.join(root, name))
                for line in fopen.readlines():
                    if line[:1] != "#":
                        # BOX_NAME,CALL_TIME,CRANE_TIME,EXECUTION_TIME,line = line.replace(",", ";", 1)
                        line_split = line.split(",")
                        if START_RECOUNT_TS <= int(line_split[3]) <= END_RECOUNT_TS:
                            n_temp += 1
                n_removals.append(n_temp)
    return n_arrivals, n_removals


def main_arrivals_and_removals():
    scenario_path = [(r"C:\Users\Juampi\Documents\GitHub\DSI-TSSIM\INSTANCES\Resultados\F2_100\MM", "MM")]

    print("SCEN", "ARR_AVE", "ARR_STD", "REM_AVE", "REM_STD")
    for scenario in scenario_path:
        scn_arr, scn_rem = getArrivalsAndRemovals(scenario[0])
        print(scenario[1], np.round(np.average(scn_arr), 1),
              np.round(np.std(scn_arr), 1),
              np.round(np.average(scn_rem), 1),
              np.round(np.std(scn_rem), 1))


if __name__ == '__main__':
    # main_count_fails()
    # main_ocupation_by_replica()
    # main_ocupacion()
     main_relocaciones()
    #main_arrivals_and_removals()
    # main_decisiones()
