import numpy as np
import matplotlib.pyplot as plt
import sys

OUTPUT_FOLDER = "INSTANCES\INSTANCES_180D_F3"
random_state = None
T_INICIAL = 8 * 60
T_FINAL = 18 * 60
FACTOR_DE_ESCALA = 1.75
DIAS = 180
SERVICE_CHANCE = 0.15
RANGO_SERVICIO_EN_HORA = [1, 4]

# Tasa de llegada, (limite inferior del intervalo, tasa minutos)
TASA_LLEGADA = [(11, 3.66),
                (14, 7.05),
                (18, 8.97)]

TASA_ESTADIA = 12 #dias
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


class Arrival:
    '''
    Clase que guarda toda la informacion de cada llegada
    '''

    def __init__(self, day, min):
        self.arrival_day = day
        self.arrival_min = min
        self.stay_time = int(np.ceil(-np.log(1 - random_state.rand()) * TASA_ESTADIA))

        # Generamos la hora de salida:
        random_number = random_state.rand()
        for n, p in DIST_ACUMULADA_PROBABILIDAD_SALIDAS:
            if random_number <= p:
                self.leave_min = n * 60 + random_state.randint(1, 60)
                break

        if random_state.rand() <= SERVICE_CHANCE:
            self.service = True
            #Si tiene servicio le sorteamos una duracion
            self.service_len = random_state.randint(RANGO_SERVICIO_EN_HORA[0], RANGO_SERVICIO_EN_HORA[1]+1)
            self.service_day = random_state.randint(self.arrival_day, self.arrival_day+self.stay_time + 1)
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

#WRITE ARRIVAL FILE

def write_arrival_file(arrival_list, file_name, Min_to_Timestep_coeff = 1):
    file = open(file_name, "w+")
    count = 0
    for i in arrival_list:
        ts_arrival = int((i.arrival_day*1440 + i.arrival_min)/Min_to_Timestep_coeff)
        ts_leave = int(((i.arrival_day + i.stay_time)*1440 + i.leave_min)/Min_to_Timestep_coeff)
        name = "C{}-{}-{}".format(i.arrival_day, count, i.arrival_day + i.stay_time)
        count = count + 1
        file.write("{} {} {}\n".format(name, ts_arrival, ts_leave))

def main(seed, output_file_name, grap=False):
    global random_state
    random_state = np.random.RandomState(seed)
    # Primero creamos todas las llegades de todos los dias, estas se guardan en un arreglo para cada día.
    llegadas_dias = []
    todas_horas_llegada_dia = []
    for dia in range(DIAS):
        llegadas_dias.append(crear_llegadas_dia())


    print(llegadas_dias)

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
     #Graficos solo para ver que no pase nada raro
    if grap == True:

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

        #Estadisticos
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



        fig, a = plt.subplots(2,2)
        a[0][0].set_title("Llegadas")
        a[0][0].set_xlabel("Minuto del día")
        a[0][0].hist(todas_llegadas, bins=11)


        a[0][1].set_title("Salidas")
        a[0][1].set_xlabel("Minuto del día")
        a[0][1].hist(todas_salidas, bins=11)


        a[1][0].set_title("Tiempo de Estadía")
        a[1][0].set_xlabel("Número de días")
        a[1][0].hist(todas_estadias, bins='auto')


        a[1][1].set_title("Duración Servicios")
        a[1][1].set_xlabel("Minuto del día")
        a[1][1].hist(todas_servicios_len, bins=[1,2,3,4,5])




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


