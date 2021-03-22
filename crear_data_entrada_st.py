"""
Generador de llegadas y salidas estocásticas
"""

import numpy as np
import matplotlib.pyplot as plt
import sys

OUTPUT_FOLDER = "INSTANCES/INSTANCES_180D_F18_100_ST"
random_state = None
random_state2 = None  # Utilizado para la instancias del modelo estocastico
T_INICIAL = 8 * 60
T_FINAL = 18 * 60
FACTOR_DE_ESCALA = 1.8
DIAS = 180
SERVICE_CHANCE = 0.15
RANGO_SERVICIO_EN_HORA = [1, 4]

# Tasa de llegada, (limite inferior del intervalo, tasa minutos)
TASA_LLEGADA = [(11, 3.66),
                (14, 7.05),
                (18, 8.97)]

TASA_ESTADIA = 12  # dias
# Limite in
DIST_ACUMULADA_PROBABILIDAD_SALIDAS = [(8, 0.03452914798206278),
                                       (9, 0.11569506726457399),
                                       (10, 0.2374439461883408),
                                       (11, 0.3630044843049327),
                                       (12, 0.4721973094170403),
                                       (13, 0.5567264573991031),
                                       (14, 0.6345291479820627),
                                       (15, 0.7434977578475336),
                                       (16, 0.8704035874439462),
                                       (17, 1.0)]


class Arrival_st:
    '''
    Clase que guarda toda la informacion de cada llegada y salida usando informacion deterministica
    '''

    def __init__(self, day, minute, error_desvest):
        """
        Arribo con llegadas deterministicas
        :param day: dia en que el contenedor
        :param minute: minuto en que llega el contenedor
        """

        self.arrival_day = day
        self.arrival_min = minute
        self.stay_time = int(np.ceil(-np.log(1 - random_state.rand()) * TASA_ESTADIA))

        # Generamos la hora de salida:
        random_number = random_state.rand()
        for n, p in DIST_ACUMULADA_PROBABILIDAD_SALIDAS:
            if random_number <= p:
                self.leave_min = n * 60 + random_state.randint(1, 60)
                break

        if random_state.rand() <= SERVICE_CHANCE:
            self.service = True
            # Si tiene servicio le sorteamos una duracion
            self.service_len = random_state.randint(RANGO_SERVICIO_EN_HORA[0], RANGO_SERVICIO_EN_HORA[1] + 1)
            self.service_day = random_state.randint(self.arrival_day, self.arrival_day + self.stay_time + 1)
            if self.service_day == (self.arrival_day + self.stay_time):
                self.service_min = random_state.randint(T_INICIAL, self.leave_min)
            else:
                self.service_min = random_state.randint(T_INICIAL, T_FINAL)
            '''print("Servicio: dia {}, min {}, por {} (Sale el {} a las {}".format(self.service_day,
                                                                                 self.service_min,
                                                                                 self.service_len,
                                                                                 self.arrival_day + self.stay_time,
                                                                               self.leave_min))
            '''
        else:
            self.service = False
            self.service_day = 0
            self.service_min = 0
            self.service_len = 0

    def __repr__(self):
        return "Arrive Day {}, Min {}, Stays for {} days, leaves at {}. Service {}\n".format(self.arrival_day,
                                                                                             self.arrival_min,
                                                                                             self.stay_time,
                                                                                             self.leave_min,
                                                                                             self.service)


##Creamos las llegadas de 1 dia
def crear_llegadas_dia():
    '''
    Metodo para crear las llegadas de un dia (de 8:00 a 18:00 hrs)
    :return: list of all the arrival times for a single day
    '''
    llegadas_dia = []

    t = T_INICIAL
    I = 0
    while t < T_FINAL:
        x = int(np.ceil(-np.log(1 - random_state.rand()) * TASA_LLEGADA[I][1] * FACTOR_DE_ESCALA))
        # print("T={}, siguiente llegada en {}, t+x = {}, tasa actual {}".format(t, x, t+x, TASA_LLEGADA[I][1]))
        if (t + x) <= TASA_LLEGADA[I][0] * 60:
            llegadas_dia.append(t + x)
            t = t + x
        else:
            if t + x > T_FINAL:
                break
            else:
                t = t + x
                I = I + 1
    return llegadas_dia


# WRITE ARRIVAL FILE

def write_arrival_file(arrival_list, file_name, Min_to_Timestep_coeff=1):
    file = open(file_name, "w+")
    count = 0
    for i in arrival_list:
        ts_arrival = int((i.arrival_day * 1440 + i.arrival_min) / Min_to_Timestep_coeff)
        ts_leave = int(((i.arrival_day + i.stay_time) * 1440 + i.leave_min) / Min_to_Timestep_coeff)
        name = "C{}-{}-{}".format(i.arrival_day, count, i.arrival_day + i.stay_time)
        count = count + 1
        file.write("{} {} {}\n".format(name, ts_arrival, ts_leave))


def main(seed, output_file_name, grap=False):
    global random_state
    random_state = np.random.RandomState(seed)

    global random_state_2
    random_state_2 = np.random.RandomState(seed + 1)

    # Primero creamos todas las llegades de todos los dias, estas se guardan en un arreglo para cada día.
    llegadas_dias = []
    todas_horas_llegada_dia = []
    for dia in range(DIAS):
        llegadas_dias.append(crear_llegadas_dia())

    # print(llegadas_dias)

    # Para cada llegada creamos un objeto arrival y le generamos la información faltante, queda guardados en una lista
    arrival_list = []
    for dia in range(len(llegadas_dias)):
        for arrival in llegadas_dias[dia]:
            new_arrival = Arrival(dia, arrival)
            arrival_list.append(new_arrival)
    import os
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    write_arrival_file(arrival_list, OUTPUT_FOLDER + "\\" + output_file_name)
    # Graficos solo para ver que no pase nada raro
    if grap == True:

        '''
        cantidad_llegadas_cada_dia =[]

        for i in llegadas_dias:
            cantidad_llegadas_cada_dia.append(len(i))

        print(cantidad_llegadas_cada_dia)
        plt.figure()
        plt.bar(range(0,DIAS), cantidad_llegadas_cada_dia)
        plt.plot(np.linspace(0,DIAS,2), [np.average(cantidad_llegadas_cada_dia),np.average(cantidad_llegadas_cada_dia)], lw=2, color='red')

        print(np.average(cantidad_llegadas_cada_dia))
        #plt.figure()
        #plt.hist(np.diff(llegadas_dias), bins='auto')
        '''
        # Estadisticos
        todas_llegadas = []
        todas_estadias = []
        todas_salidas = []
        todas_servicios_len = []

        for i in arrival_list:
            todas_llegadas.append(i.arrival_min)
            todas_estadias.append(i.stay_time)
            todas_salidas.append(i.leave_min)
            if i.service == True:
                todas_servicios_len.append(i.service_len)

        fig2, b = plt.subplots(2)
        b[0].set_xlabel("Time of day")
        b[0].hist(todas_llegadas, bins=11)
        b[0].set_xticks(np.arange(8 * 60, 19 * 60, step=60))
        b[0].set_xticklabels(np.arange(8, 20, step=1))

        b[1].set_xlabel("Time of day")
        b[1].hist(todas_salidas, bins=12)
        b[1].set_xticks(np.arange(8 * 60, 19 * 60, step=60))
        b[1].set_xticklabels(np.arange(8, 20, step=1))

        '''
        fig, a = plt.subplots(2,2)
        a[0][0].set_title("Llegadas")
        a[0][0].set_xlabel("Minuto del día")
        a[0][0].hist(todas_llegadas, bins=11)


        a[0][1].set_title("Salidas")
        a[0][1].set_xlabel("Minuto del día")
        a[0][1].hist(todas_salidas, bins=11)


        ave_estadia = np.average(todas_estadias)
        a[1][0].set_title("Tiempo de Estadía {}".format(ave_estadia))
        a[1][0].set_xlabel("Número de días")
        a[1][0].hist(todas_estadias, bins='auto')


        a[1][1].set_title("Duración Servicios")
        a[1][1].set_xlabel("Minuto del día")
        a[1][1].hist(todas_servicios_len, bins=[1,2,3,4,5])
    '''

    '''
    def find_probability(probability, dist):
    
        for n,p in dist:
            if probability <= p:
                return n
    
    for i in range(10):
        random_number = np.random.rand()
        n = find_probability(random_number, DIST_ACUMULADA_PROBABILIDAD_SALIDAS)
        print("{} cae en el bin {}".format(random_number, n))
    '''


if __name__ == '__main__':
    '''
    main(443, 'arrivals_1.ini')
    main(650, 'arrivals_2.ini')
    main(429, 'arrivals_3.ini')
    main(797, 'arrivals_4.ini')
    main(494, 'arrivals_5.ini')
    main(454, 'arrivals_6.ini')
    main(770, 'arrivals_7.ini')
    main(413, 'arrivals_8.ini')
    main(348, 'arrivals_9.ini')
    main(506, 'arrivals_10.ini')
    main(473, 'arrivals_11.ini')
    main(241, 'arrivals_12.ini')
    main(345, 'arrivals_13.ini')
    main(483, 'arrivals_14.ini')
    main(679, 'arrivals_15.ini')
    main(927, 'arrivals_16.ini')
    main(577, 'arrivals_17.ini')
    main(211, 'arrivals_18.ini')
    main(950, 'arrivals_19.ini')
    main(665, 'arrivals_20.ini')
    main(687, 'arrivals_21.ini')
    main(678, 'arrivals_22.ini')
    main(697, 'arrivals_23.ini')
    main(518, 'arrivals_24.ini')
    main(273, 'arrivals_25.ini')
    '''

    # 180 DIAS

    main(788, 'arrivals_1.ini', grap=True)
    main(747, 'arrivals_2.ini')
    main(580, 'arrivals_3.ini')
    main(640, 'arrivals_4.ini')
    main(430, 'arrivals_5.ini')
    main(207, 'arrivals_6.ini')
    main(546, 'arrivals_7.ini')
    main(618, 'arrivals_8.ini')
    main(588, 'arrivals_9.ini')
    main(165, 'arrivals_10.ini')
    main(644, 'arrivals_11.ini')
    main(897, 'arrivals_12.ini')
    main(194, 'arrivals_13.ini')
    main(540, 'arrivals_14.ini')
    main(638, 'arrivals_15.ini')
    '''
    main(261, 'arrivals_16.ini')
    main(751, 'arrivals_17.ini')
    main(301, 'arrivals_18.ini')
    main(448, 'arrivals_19.ini')
    main(528, 'arrivals_20.ini')
    main(470, 'arrivals_21.ini')
    main(385, 'arrivals_22.ini')
    main(823, 'arrivals_23.ini')
    main(983, 'arrivals_24.ini')
    main(919, 'arrivals_25.ini')
    main(341, 'arrivals_26.ini')
    main(421, 'arrivals_27.ini')
    main(297, 'arrivals_28.ini')
    main(590, 'arrivals_29.ini')
    main(480, 'arrivals_30.ini')
    main(326, 'arrivals_31.ini')
    main(710, 'arrivals_32.ini')
    main(665, 'arrivals_33.ini')
    main(425, 'arrivals_34.ini')
    main(973, 'arrivals_35.ini')
    main(507, 'arrivals_36.ini')
    main(758, 'arrivals_37.ini')
    main(792, 'arrivals_38.ini')
    main(333, 'arrivals_39.ini')
    main(147, 'arrivals_40.ini')
    main(211, 'arrivals_41.ini')
    main(551, 'arrivals_42.ini')
    main(320, 'arrivals_43.ini')
    main(885, 'arrivals_44.ini')
    main(579, 'arrivals_45.ini')
    main(713, 'arrivals_46.ini')
    main(649, 'arrivals_47.ini')
    main(988, 'arrivals_48.ini')
    main(778, 'arrivals_49.ini')
    main(747, 'arrivals_50.ini')
    main(752, 'arrivals_51.ini')
    main(676, 'arrivals_52.ini')
    main(268, 'arrivals_53.ini')
    main(619, 'arrivals_54.ini')
    main(100, 'arrivals_55.ini')
    main(869, 'arrivals_56.ini')
    main(514, 'arrivals_57.ini')
    main(180, 'arrivals_58.ini')
    main(376, 'arrivals_59.ini')
    main(676, 'arrivals_60.ini')
    main(258, 'arrivals_61.ini')
    main(336, 'arrivals_62.ini')
    main(932, 'arrivals_63.ini')
    main(788, 'arrivals_64.ini')
    main(585, 'arrivals_65.ini')
    main(292, 'arrivals_66.ini')
    main(837, 'arrivals_67.ini')
    main(450, 'arrivals_68.ini')
    main(889, 'arrivals_69.ini')
    main(216, 'arrivals_70.ini')
    main(428, 'arrivals_71.ini')
    main(261, 'arrivals_72.ini')
    main(652, 'arrivals_73.ini')
    main(588, 'arrivals_74.ini')
    main(940, 'arrivals_75.ini')
    main(137, 'arrivals_76.ini')
    main(449, 'arrivals_77.ini')
    main(118, 'arrivals_78.ini')
    main(797, 'arrivals_79.ini')
    main(841, 'arrivals_80.ini')
    main(637, 'arrivals_81.ini')
    main(635, 'arrivals_82.ini')
    main(535, 'arrivals_83.ini')
    main(647, 'arrivals_84.ini')
    main(821, 'arrivals_85.ini')
    main(294, 'arrivals_86.ini')
    main(783, 'arrivals_87.ini')
    main(657, 'arrivals_88.ini')
    main(987, 'arrivals_89.ini')
    main(974, 'arrivals_90.ini')
    main(737, 'arrivals_91.ini')
    main(612, 'arrivals_92.ini')
    main(329, 'arrivals_93.ini')
    main(767, 'arrivals_94.ini')
    main(223, 'arrivals_95.ini')
    main(434, 'arrivals_96.ini')
    main(559, 'arrivals_97.ini')
    main(713, 'arrivals_98.ini')
    main(430, 'arrivals_99.ini')
    main(126, 'arrivals_100.ini')

'''
    # main(788, 'test_sample.txt', grap=True)
