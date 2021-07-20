import gurobipy as gp
from gurobipy import GRB
import json
from collections import namedtuple
import sys
import time
from functools import wraps
import argparse
import pathlib

BASE_COST_CLOSE = 10
BASE_COST_MEDIUM = 30
BASE_COST_LONG = 100
BASE_COST_RELOC = 20
BASE_COST_EXILE = 200


def printer(function):
    @wraps(function)
    def print_status(*args, **kwargs):
        print('{:20}'.format('{}...'.format(function.__name__)), end='')
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        print("{:.2f}".format(t1 - t0))
        return result

    return print_status


class TLSMODEL:
    model_name = ''
    cont = []  # Contenedores: C
    c_llegan = []  # Contenedores que llegan: C+
    c_salen = []  # Contenedores que salen: C-
    c_fijos = []  # Contenedores que no de deben mover
    c_libres = []  # Contenedores que se van a tener que relocar

    c_mueven = []  # Contenedores que salen o lle,gan (ordenados): Cm

    positions = []  # Posiciones en el patio: P

    # all_pos = []  # (auxiliar) Positions + lm + lp
    fix_pos = []  # (auxiliar) Posiciones que no se moveran
    mov_pos = []  # (auxiliar) Posiciones que se moveran

    close_pos = []  # Pairs of positions that are within close range
    med_pos = []  # Pairs of positions that are within medium range
    long_pos = []  # Pairs of positions that are within long range

    U = {}  # Posición bajo de i in P: U[i]
    B = {}  # Posiones que bloquean a i in I: B[i]
    B_I = {}  # Posiciones bloqueadas por i in I: B^{-1}[i]

    # Declaración de Parámetros
    Y0 = {}  # Posición inicial de cada Contenedor, vale 1 si el cont c esta en la posicion p en t=0 {('cont',
    T = {}  # Tiempo de salida del contenedor c {'cont': int}
    T_In = {}  # (auxiliar) Tiempo de llegada
    pos_base_cost = {}

    pos_ini_cont = {}
    mov_cortos = []
    mov_medios = []
    mov_largos = []

    # Etapas
    etapas = []
    e_llega = {}
    e_sale = {}
    e_activacion = {}
    etapas_activas = {}
    etapas_inactivas = {}

    # Tuplas
    t_y_fijos = set()
    t_y_salen = set()
    t_y_libres = set()
    t_y_llegan = set()
    all_y = set()

    t_x_close = set()
    t_x_medium = set()
    t_x_long = set()

    t_v_llegan = set()
    t_w_salen = set()

    t_exile = set()

    # Costos tuplas
    cost_x_c = {}
    cost_x_m = {}
    cost_x_l = {}
    cost_v = {}
    cost_w = {}
    # Modelo
    model = None

    # Variables
    x_c = None
    x_m = None
    x_l = None
    v = None
    w = None
    y = None
    z = None
    x_ex = None

    # Auxliary dictionaries
    # varName_KeySets_RetSet
    xc_ice_j = {}
    xm_ice_j = {}
    xl_ice_j = {}
    xc_jce_i = {}
    xm_jce_i = {}
    xl_jce_i = {}
    xc_ie_jc = {}
    xm_ie_jc = {}
    xl_ie_jc = {}
    w_ie_c = {}
    yc_ie = {}
    yi_ce ={}
    xc_je_ic = {}
    xm_je_ic = {}
    xl_je_ic = {}
    v_je_c = {}
    xe_ie_c = {}
    
    c10set = set()

    def __init__(self, files, name='', echo=True):
        self.model_name = name
        # Hack to get status code
        sc = gp.StatusConstClass
        self.status_dic = {sc.__dict__[k]: k for k in sc.__dict__.keys() if 'A' <= k[0] <= 'Z'}

        #  Sets and parameters declarations
        self.echo = echo

        self.loadContainers(files[0], echo=self.echo)
        self.loadPositions(files[1], echo=self.echo)
        self.buildMovements(echo=self.echo)
        self.buildStages(echo=self.echo)

        self.buildPositionTuples(echo=self.echo)
        self.BuildTupleMovementsCLoseMedium(echo=self.echo)
        self.BuildTupleMovementsLong([], [], echo=self.echo)
        self.BuildTupleInbounds(echo=self.echo)
        self.BuildTupleOutbounds(echo=self.echo)
        self.BuildTuplesExile()

    def InitModel(self):
        self.model = gp.Model(name=self.model_name)
        self.x_c = self.SetVar('XC', self.t_x_close, obj=self.cost_x_c, type=GRB.INTEGER, echo=self.echo)
        self.x_m = self.SetVar('XM', self.t_x_medium, obj=self.cost_x_m, type=GRB.INTEGER, echo=self.echo)
        self.x_l = self.SetVar('XL', self.t_x_long, obj=self.cost_x_l, type=GRB.INTEGER, echo=self.echo)

        self.x_ex = self.SetVar('XE', self.t_exile, obj=BASE_COST_EXILE, type=GRB.INTEGER, echo=self.echo)

        self.AuxDicts()

        altura = {}
        for j, c, e in self.t_v_llegan:
            altura[(j, c, e)] = int(j[-1])

        self.v = self.SetVar('V', self.t_v_llegan, obj=self.cost_v, type=GRB.INTEGER, echo=self.echo)
        self.w = self.SetVar('W', self.t_w_salen, obj=0, type=GRB.INTEGER, echo=self.echo)
        self.y = self.SetVar('Y', self.all_y, obj=0, echo=self.echo)
        self.z = self.SetVar('Z', self.etapas, obj=BASE_COST_RELOC, type=GRB.INTEGER, echo=self.echo)
#        self.ex = self.SetVar('EX', self.t_exile, obj=BASE_COST_EXILE, type=GRB.INTEGER, echo=self.echo)

        self.Const1()
        self.Const2()
        self.Const3()
        self.Const4_a()
        self.Const4_b()
        self.Const4_c()
        self.Const4_d()
        self.Const5()
        self.Const6()
        self.Const7()
        self.Const8()
        self.Const9()
        self.Const10()
        self.Const11()

    @printer
    def loadContainers(self, contenedores_file, echo=True):
        """
        Cargar la data de contenedores desde un archivo JSON
        :param echo:
        :param self:
        :param contenedores_file:
        :return:
        """
        # Data Import
        with open(contenedores_file) as json_file:
            data = json.load(json_file)

        # Deficion de Sets [tc, pos_ini, status]

        for c, [tc, pos, status] in data['contenedores'].items():  # val=[t_salida, posicion, status]
            self.cont.append(c)
            self.T[c] = tc
            self.Y0[(c, pos)] = 1
            self.pos_ini_cont[c] = pos
            if status == 'fijo':
                self.c_fijos.append(c)
            elif status == 'sale':
                self.c_salen.append(c)
            else:
                self.c_libres.append(c)

        for c, [tin, tc] in data['cont_llegadas'].items():  # val=[t_llegada, t_salida]
            self.cont.append(c)
            self.c_llegan.append(c)
            self.T[c] = tc
            self.T_In[c] = tin
            self.Y0[c, 'arrival'] = 1

        # Armamos la lista de los que se mueven
        # Primero los que salen en con el tiempo de salida
        self.c_mueven = []
        aux_orden = []
        for c in self.c_salen:
            self.c_mueven.append(c)
            aux_orden.append(self.T[c])
        # Segundo los que salen
        # Luego los que llegan con el tiempo de llegada
        for c in self.c_llegan:
            self.c_mueven.append(c)
            aux_orden.append(self.T_In[c])
        # Finalmente los ordenamos:

        self.c_mueven = [i for _, i in sorted(zip(aux_orden, self.c_mueven))]

        if echo:
            print("Resumen contenedores")
            print("-------------------------")
            print("Total  (cont)     : {:5}".format(len(self.cont)))
            print("Llegan (c_llegan) : {:5}".format(len(self.c_llegan)))
            print("Salen  (c_salen)  : {:5}".format(len(self.c_salen)))
            print("Mueven (c_mueven) : {:5}".format(len(self.c_mueven)))
            print("Fijos  (c_fijos)  : {:5}".format(len(self.c_fijos)))
            print("Libres (c_libres) : {:5}".format(len(self.c_libres)))

            print("-------------------------")

    @printer
    def loadPositions(self, posiciones_file, echo=True):
        """
        Leer el archivo de posiciones JSON
        :param posiciones_file:
        :param echo:
        :return: None
        """

        with open(posiciones_file) as json_file:
            data_pos = json.load(json_file)

        for p in data_pos['posiciones']:
            self.positions.append(p)

        for par, dist in data_pos['distancias'].items():
            orig, dest = par.split('_')
            if dist == 'C':
                if orig[:2] + orig[3:] == dest[:2] + dest[3:]:
                    if orig[2] in ['A', 'Y']:
                        self.close_pos.append(('{}-{}'.format(orig, 2), '{}-{}'.format(dest, 1)))
                        self.close_pos.append(('{}-{}'.format(orig, 2), '{}-{}'.format(dest, 2)))
                        self.close_pos.append(('{}-{}'.format(orig, 2), '{}-{}'.format(dest, 3)))
                        self.close_pos.append(('{}-{}'.format(orig, 2), '{}-{}'.format(dest, 4)))
                        self.close_pos.append(('{}-{}'.format(orig, 3), '{}-{}'.format(dest, 3)))
                        self.close_pos.append(('{}-{}'.format(orig, 3), '{}-{}'.format(dest, 4)))
                    elif orig[2] in ['B', 'X']:
                        self.close_pos.append(('{}-{}'.format(orig, 2), '{}-{}'.format(dest, 1)))
                        self.close_pos.append(('{}-{}'.format(orig, 3), '{}-{}'.format(dest, 1)))
                        self.close_pos.append(('{}-{}'.format(orig, 3), '{}-{}'.format(dest, 2)))
                        self.close_pos.append(('{}-{}'.format(orig, 4), '{}-{}'.format(dest, 1)))
                        self.close_pos.append(('{}-{}'.format(orig, 4), '{}-{}'.format(dest, 2)))
                        self.close_pos.append(('{}-{}'.format(orig, 4), '{}-{}'.format(dest, 3)))

                else:
                    for i in range(1, 5):
                        for j in range(1, 5):
                            self.close_pos.append(('{}-{}'.format(orig, i), '{}-{}'.format(dest, j)))
            elif dist == 'M':
                for i in range(1, 5):
                    for j in range(1, 5):
                        self.med_pos.append(('{}-{}'.format(orig, i), '{}-{}'.format(dest, j)))
            elif dist == 'L':
                for i in range(1, 5):
                    for j in range(1, 5):
                        self.long_pos.append(('{}-{}'.format(orig, i), '{}-{}'.format(dest, j)))

        for c in self.Y0.keys():
            if c[0] in self.c_fijos:
                self.fix_pos.append(c[1])

        for p in self.positions:
            if p not in self.fix_pos:
                self.mov_pos.append(p)

        if echo:
            print("Resumen Posiciones")
            print("-------------------------")
            print("Total   (positions) :{:4}".format(len(self.positions)))
            print("Fijas   (fix_pos)   :{:4}".format(len(self.fix_pos)))
            print("Mobiles (mov_pos)   :{:4}".format(len(self.mov_pos)))
            print("-------------------------")

        self.mov_pos = set(self.mov_pos)

        # Crear U, B y B-1, BASE_COST

        for p in self.positions:
            bloque = p[:2]
            fila = p[2:3]
            columna = p[p.find(fila) + 1:p.find('-')]
            nivel = p[-1:]
            # U
            if int(nivel) > 1:
                self.U[p] = '{}{}'.format(p[:-1], int(nivel) - 1)

            # CALCULO COSTO BASE DE LA POSICION
            if fila in ['A', 'Y']:
                self.pos_base_cost[p] = int(nivel) * 2
            if fila in ['B', 'X']:
                self.pos_base_cost[p] = int(nivel) * 2 - 1

            # B
            temp = []
            if fila in ['A', 'Y']:
                for r in range(int(nivel) + 1, 5):
                    temp.append('{}{}{}-{}'.format(bloque, fila, columna, r))
            if fila in ['B', 'X']:
                for r in range(int(nivel) + 1, 5):
                    temp.append('{}{}{}-{}'.format(bloque, fila, columna, r))
                if fila == 'B':
                    for r in range(int(nivel), 5):
                        if r > 1:
                            temp.append('{}{}{}-{}'.format(bloque, 'A', columna, r))
                else:
                    for r in range(int(nivel), 5):
                        if r > 1:
                            temp.append('{}{}{}-{}'.format(bloque, 'Y', columna, r))
            # if temp:
            self.B[p] = temp

        # B-1
        for i in self.B:
            for j in self.B[i]:
                if j not in self.B_I:
                    self.B_I[j] = set([i])
                else:
                    self.B_I[j].add(i)

        if echo:
            print('Creados U, B y B_I')

    @printer
    def buildMovements(self, echo=True):
        """
        Builds the sets of posible movements (close, mid and long range), eliminates those that start or begin at the
        position of a fixed container.
        :param echo:
        :return:
        """
        for o, d in self.close_pos:
            if o in self.mov_pos:
                if d in self.mov_pos:
                    self.mov_cortos.append((o, d))

        for o, d in self.med_pos:
            if o in self.mov_pos:
                if d in self.mov_pos:
                    self.mov_medios.append((o, d))

        for o, d in self.long_pos:
            if o in self.mov_pos:
                if d in self.mov_pos:
                    self.mov_largos.append((o, d))

        if echo:
            print("Resumen Movimientos Internos")
            print("----------------------------------------")
            print("Total                         :{:6}".format(len(self.close_pos) + len(self.med_pos)
                                                               + len(self.long_pos)))
            print("Total Filtrado                :{:6}".format(len(self.mov_cortos) + len(self.mov_medios)
                                                               + len(self.mov_largos)))
            print("----------------------------------------")
            print("Cortos  (close_pos)           :{:6}".format(len(self.close_pos)))
            print("Cortos Filtrados (mov_cortos) :{:6}".format(len(self.mov_cortos)))
            print("Medios  (med_pos)             :{:6}".format(len(self.med_pos)))
            print("Medios Filtrados (mov_medios) :{:6}".format(len(self.mov_medios)))
            print("Largos  (long_pos)            :{:6}".format(len(self.long_pos)))
            print("Largos Filtrados (mov_cortos) :{:6}".format(len(self.mov_largos)))
            print("----------------------------------------")
            print("posiciones x posiciones       :{:6}".format(len(self.positions) * len(self.positions)))
            print("mov_pos x mov_pos             :{:6}".format(len(self.mov_pos) * len(self.mov_pos)))
            print("----------------------------------------")

    @printer
    def buildDestinations(self):
        destinos_cortos = {}
        destinos_medios = {}
        origenes_cortos = {}
        origenes_medios = {}
        for i in self.positions:
            destinos_cortos[i] = []
            destinos_medios[i] = []
            origenes_cortos[i] = []
            origenes_medios[i] = []

        for o, d in self.mov_cortos:
            if o in destinos_cortos.keys():
                destinos_cortos[o].append(d)

        for o, d in self.mov_medios:
            if o in destinos_medios.keys():
                destinos_medios[o].append(d)

        for o, d in self.mov_cortos:
            if d in origenes_cortos.keys():
                origenes_cortos[d].append(o)

        for o, d in self.mov_medios:
            if d in origenes_medios.keys():
                origenes_medios[d].append(o)

    @printer
    def buildStages(self, echo=True):
        """
        Estimates the number of stages and on which stage each container must arrive, leave or begin move for the first
        time.
        :param echo:
        :return:
        """
        # Calculo de ETAPAS por contentenedor

        e = 2
        for i in self.c_mueven:
            if i in self.c_llegan:
                self.e_llega[i] = e
                self.e_activacion[i] = e + 1
                e += 1
                if echo:
                    print('Llega {} en {}'.format(i, self.e_llega[i]))
            if i in self.c_salen:
                ee = 0
                if echo:
                    print('Sale {} {} {}'.format(i,
                                                 self.pos_ini_cont[i],
                                                 self.B[self.pos_ini_cont[i]]))

                for j in self.c_salen + self.c_libres:
                    if self.pos_ini_cont[j] in self.B[self.pos_ini_cont[i]]:
                        if j not in self.e_activacion.keys():  # Revisamos si ya fue activado
                            # Lo activamos y fijamos su fecha de movimiento mas temprano
                            self.e_activacion[j] = e
                            ee += 1
                            if echo:
                                print('\tActivado {} a partir de {} en {}'.format(j, e, self.pos_ini_cont[j]))
                        else:
                            if echo:
                                print('\t{} Ya fue activado en {}'.format(j, self.e_activacion[j]))
                e = e + ee
                self.e_sale[i] = e
                if i not in self.e_activacion.keys():
                    self.e_activacion[i] = e
                e += 1
                if echo:
                    print('\t{} Saldra en {}'.format(i, self.e_sale[i]))

        self.etapas = list(range(1, e))

        # Calcular etapas activas de cada contenedor

        for c in self.c_salen:
            self.etapas_activas[c] = [e for e in range(self.e_activacion[c], self.e_sale[c])]
        for c in self.c_llegan:
            self.etapas_activas[c] = [e for e in range(self.e_activacion[c], self.etapas[-1] + 1)]
        for c in self.c_libres:
            self.etapas_activas[c] = [e for e in range(self.e_activacion[c], self.etapas[-1] + 1)]

        if echo:
            print("SALEN")
            for c in self.c_salen:
                print('{} {} (Sale en {})\nActivos: {}'.format(c, self.e_activacion[c], self.e_sale[c],
                                                               self.etapas_activas[c]))
            print("LLEGAN")
            for c in self.c_llegan:
                print('{} (Llega en {})\nActivos: {}'.format(c, self.e_llega[c], self.etapas_activas[c]))
            print("LIBRES")
            for c in self.c_libres:
                print('{} {}\nActivos: {}'.format(c, self.e_activacion[c], self.etapas_activas[c]))

    @printer
    def buildPositionTuples(self, echo=True):
        """
        Build all position named tuples ['pos', 'cont', 'etapa']
        :param echo:
        :return:
        """
        # Tuplas para las variables de posicion

        # Para los fijos, solo tienen una posición posible
        # Para lo que salen, estan hasta que salen
        named_y = namedtuple('named_y', ['pos', 'cont', 'etapa'])
        t_y_fijos = set()
        t_y_salen = set()
        t_y_libres = set()
        for c, p in self.Y0.keys():
            # Fijos tienen solo una posicion
            if c in self.c_fijos:
                [t_y_fijos.add(named_y(p, c, e)) for e in self.etapas]

            # Los que salen tienen una pocion hasta que salen
            elif c in self.c_salen:
                [t_y_salen.add(named_y(p, c, e)) for e in self.etapas if e <= self.e_sale[c]]
                # A menos que se activen antes
                if self.etapas_activas[c]:
                    aux_e = self.etapas_activas[c]
                    aux_e.append(self.e_sale[c])
                    min_e = min(aux_e)
                    if min_e > 1:
                        aux_e.append(min_e - 1)

                    for e in aux_e:
                        for pp in self.mov_pos:
                            t_y_salen.add(named_y(pp, c, e))

            # Tienen una posicion hasta que se activan, de alli pueden estar en cualquier lugar
            if c in self.c_libres:
                [t_y_libres.add(named_y(p, c, e)) for e in self.etapas if e < self.e_activacion[c]]
                for e in self.etapas_activas[c]:
                    for pp in self.mov_pos:
                        t_y_libres.add(named_y(pp, c, e))

        # Para los que llegan pueden estar en cualquier posicion no fija despues de que arriban
        t_y_llegan = set()
        for c in self.c_llegan:
            for p in self.mov_pos:
                [t_y_llegan.add(named_y(p, c, e)) for e in self.etapas if e >= self.e_llega[c]]

        if echo:
            print('Resumen Tuplas (Variables Y)')
            print('-----------------------')
            print('t_y_fijos     : {:8}'.format(len(t_y_fijos)))
            print('t_y_salen     : {:8}'.format(len(t_y_salen)))
            print('t_y_llegan    : {:8}'.format(len(t_y_llegan)))
            print('t_y_libres    : {:8}'.format(len(t_y_libres)))
            print('-----------------------')
            print('Total (Y)     : {:8}'.format(len(t_y_fijos) + len(t_y_salen) + len(t_y_llegan) + len(t_y_libres)))
            print('-----------------------')

        self.all_y = t_y_fijos.union(t_y_salen, t_y_llegan, t_y_libres)
        self.t_y_fijos = t_y_fijos
        self.t_y_salen = t_y_salen
        self.t_y_libres = t_y_libres
        self.t_y_llegan = t_y_llegan

    @printer
    def BuildTupleMovementsCLoseMedium(self, echo=True):
        """
        Builds all movement tuples ['orig', 'dest', 'cont', 'etapa'] for close and mid range movements.
        :param echo:
        :return:
        """
        # Creo las tuplas para cada variable x(origen, destino, cont, etapa)
        named_x = namedtuple('named_x', ['orig', 'dest', 'cont', 'etapa'])
        # Listado de movimientos internos x(origen, destino, cont, etapa)
        t_int_close = set()
        t_int_medium = set()

        for c in self.c_libres:
            for e in self.etapas_activas[c]:
                for o, d in self.mov_cortos:
                    t = named_x(o, d, c, e)
                    t_int_close.add(t)
                    self.cost_x_c[t] = self.pos_base_cost[d] + BASE_COST_CLOSE
                for o, d in self.mov_medios:
                    t = named_x(o, d, c, e)
                    t_int_medium.add(t)
                    self.cost_x_m[t] = self.pos_base_cost[d] + BASE_COST_MEDIUM

        for c in self.c_mueven:
            for e in self.etapas_activas[c]:
                for o, d in self.mov_cortos:
                    t = named_x(o, d, c, e)
                    t_int_close.add(t)
                    self.cost_x_c[t] = self.pos_base_cost[d] + BASE_COST_CLOSE
                for o, d in self.mov_medios:
                    t = named_x(o, d, c, e)
                    t_int_medium.add(t)
                    self.cost_x_m[t] = self.pos_base_cost[d] + BASE_COST_MEDIUM

        if echo:
            print('Resumen Tuplas (Variables Movimientos)')
            print('-----------------------')
            print('Close Moves   : {:8}'.format(len(t_int_close)))
            print('Medium Moves  : {:8}'.format(len(t_int_medium)))

            print('-----------------------')

        self.t_x_close = t_int_close
        self.t_x_medium = t_int_medium

    @printer
    def BuildTupleMovementsLong(self, containers, etapas, echo=True):
        named_x = namedtuple('named_x', ['orig', 'dest', 'cont', 'etapa'])
        for c in containers:
            for e in etapas:
                for o, d in self.mov_largos:
                    self.t_x_long.add(named_x(o, d, c, e))
                    self.cost_x_l[named_x(o, d, c, e)] = self.pos_base_cost[d] + BASE_COST_LONG
        if echo:
            print('Long Moves   : {:8}'.format(len(self.t_x_long)))

    @printer
    def BuildTupleInbounds(self, echo=True):
        """
        Build the named tuples ['dest', 'cont', 'etapa'] for the movements of arriving containers
        :param echo:
        :return:
        """
        named_v = namedtuple('named_v', ['dest', 'cont', 'etapa'])
        t_x_llegan = set()
        for c in self.c_llegan:
            for d in self.mov_pos:
                if (d, c, self.e_llega[c]) in self.t_y_llegan:
                    t = named_v(d, c, self.e_llega[c])
                    t_x_llegan.add(t)
                    self.cost_v[t] = self.pos_base_cost[d]

        self.t_v_llegan = t_x_llegan
        if echo:
            print('t_x_llegan   : {:8}'.format(len(t_x_llegan)))

    @printer
    def BuildTupleOutbounds(self, echo=True):
        # Listado de movimientos cont que salen w(orig, cont, etapa)
        named_w = namedtuple('named_w', ['orig', 'cont', 'etapa'])
        t_x_salen = set()
        for c in self.c_salen:
            for o in self.mov_pos:
                if (o, c, self.e_sale[c]) in self.t_y_salen:
                    t = named_w(o, c, self.e_sale[c])
                    t_x_salen.add(t)

        self.t_w_salen = t_x_salen
        if echo:
            print('t_x_salen    : {:8}'.format(len(t_x_salen)))
            print('-----------------------')

    @printer
    def BuildTuplesExile(self):
        """
        Build the named tuples ['orig, 'cont', 'etapa'] for exiling containers
        :return:
        """
        # tuplas exilio
        named_ex = namedtuple('named_ex', ['orig','cont', 'etapa'])
        t_exilio = set()
        for t in self.t_y_libres:
            if t.etapa in self.etapas_activas[t.cont]:
                t_exilio.add(named_ex(t.pos, t.cont, t.etapa))
        self.t_exile = t_exilio



    @printer
    def AuxDicts(self):
        for i, j, c, e in self.t_x_close:
            if (i, c, e) not in self.xc_ice_j:
                self.xc_ice_j[i, c, e] = set([j])
            else:
                self.xc_ice_j[i, c, e].add(j)

        for i, j, c, e in self.t_x_medium:
            if (i, c, e) not in self.xm_ice_j:
                self.xm_ice_j[i, c, e] = set([j])
            else:
                self.xm_ice_j[i, c, e].add(j)

        for i, j, c, e in self.t_x_long:
            if (i, c, e) not in self.xl_ice_j:
                self.xl_ice_j[i, c, e] = set([j])
            else:
                self.xl_ice_j[i, c, e].add(j)

        for i, j, c, e in self.t_x_close:
            if (j, c, e) not in self.xc_jce_i:
                self.xc_jce_i[j, c, e] = set([i])
            else:
                self.xc_jce_i[j, c, e].add(i)

        for i, j, c, e in self.t_x_medium:
            if (j, c, e) not in self.xm_jce_i:
                self.xm_jce_i[j, c, e] = set([i])
            else:
                self.xm_jce_i[j, c, e].add(i)

        for i, j, c, e in self.t_x_long:
            if (j, c, e) not in self.xl_jce_i:
                self.xl_jce_i[j, c, e] = set([i])
            else:
                self.xl_jce_i[j, c, e].add(i)

        for t in self.t_x_close:
            if (t.orig, t.etapa) not in self.xc_ie_jc:
                self.xc_ie_jc[t.orig, t.etapa] = set([(t.dest, t.cont)])
            else:
                self.xc_ie_jc[t.orig, t.etapa].add((t.dest, t.cont))

        for t in self.t_x_medium:
            if (t.orig, t.etapa) not in self.xm_ie_jc:
                self.xm_ie_jc[t.orig, t.etapa] = set([(t.dest, t.cont)])
            else:
                self.xm_ie_jc[t.orig, t.etapa].add((t.dest, t.cont))

        for t in self.t_x_long:
            if (t.orig, t.etapa) not in self.xl_ie_jc:
                self.xl_ie_jc[t.orig, t.etapa] = set([(t.dest, t.cont)])
            else:
                self.xl_ie_jc[t.orig, t.etapa].add((t.dest, t.cont))

        for t in self.t_w_salen:
            if (t.orig, t.etapa) not in self.w_ie_c:
                self.w_ie_c[t.orig, t.etapa] = set([t.cont])
            else:
                self.w_ie_c[t.orig, t.etapa].add([t.cont])

        for t in self.all_y:
            if (t.pos, t.etapa) not in self.yc_ie:
                self.yc_ie[t.pos, t.etapa] = set([t.cont])
            else:
                self.yc_ie[t.pos, t.etapa].add(t.cont)

        for t in self.all_y:
            if (t.cont, t.etapa) not in self.yi_ce:
                self.yi_ce[t.cont, t.etapa] = set([t.pos])
            else:
                self.yi_ce[t.cont, t.etapa].add(t.pos)

        for t in self.t_x_close:
            if (t.dest, t.etapa) not in self.xc_je_ic:
                self.xc_je_ic[t.dest, t.etapa] = set([(t.orig, t.cont)])
            else:
                self.xc_je_ic[t.dest, t.etapa].add((t.orig, t.cont))

        for t in self.t_x_medium:
            if (t.dest, t.etapa) not in self.xm_je_ic:
                self.xm_je_ic[t.dest, t.etapa] = set([(t.orig, t.cont)])
            else:
                self.xm_je_ic[t.dest, t.etapa].add((t.orig, t.cont))

        for t in self.t_x_long:
            if (t.dest, t.etapa) not in self.xl_je_ic:
                self.xl_je_ic[t.dest, t.etapa] = set([(t.orig, t.cont)])
            else:
                self.xl_je_ic[t.dest, t.etapa].add((t.orig, t.cont))

        for t in self.t_v_llegan:
            if (t.dest, t.etapa) not in self.v_je_c:
                self.v_je_c[t.dest, t.etapa] = set([t.cont])
            else:
                self.v_je_c[t.dest, t.etapa].add([t.cont])

        for t in self.t_exile:
            if (t.orig, t.etapa) not in self.xe_ie_c:
                self.xe_ie_c[t.orig, t.etapa] = set([t.cont])
            else:
                self.xe_ie_c[t.orig, t.etapa].add(t.cont)
                

        self.c10set = set([(i, e) for i, c, e in self.t_y_libres.union(self.t_y_salen, self.t_y_llegan)])

    @printer
    def SetVar(self, name, tuple_set, obj, type=GRB.BINARY, echo=True):
        if echo:
            print('{}   '.format(name), end="")
        new_var = self.model.addVars(tuple_set, obj=obj, vtype=type, name=name)
        if echo:
            print("{:7} ({:8.2f} MB)".format(len(new_var), sys.getsizeof(new_var) / (1024 ** 2)))
        return new_var

    @printer
    def Const1(self):
        # C3: Pocision Inicial contenedores
        counter = 0
        for key, val in self.Y0.items():
            if key[1] != 'arrival':
                self.model.addConstr(self.y[key[1], key[0], 1] == self.Y0[key[0], key[1]], name='C1_{}'.format(counter))
                counter += 1



    @printer
    def Const2(self):
        # C4: Un contenedor por posicion sum y[i,c,e] <= 1 Vi,e
        counter = 0
        c4set = set([(i, e) for i, c, e in self.all_y])

        for i, e in c4set:
            self.model.addConstr(gp.quicksum(self.y[i, c, e] for c in self.cont if (i, c, e) in self.all_y) <= 1,
                                 name='C2_{}'.format(counter))
            counter += 1

    @printer
    def Const3(self):
        counter = 0
        # C4B Una posicion por contenedor
        c4bset = set([(c, e) for i, c, e in self.all_y])
        for c, e in c4bset:
            lhs = gp.LinExpr(gp.quicksum(self.y[i, c, e] for i in self.positions if (i, c, e) in self.all_y))
            #if (c, e) in self.t_exile:
            #    lhs.add(gp.LinExpr(gp.quicksum(self.ex[c, k] for k in self.etapas_activas[c] if k <= e )))
            if c in self.c_libres:
                self.model.addConstr(lhs <= 1, name='C3libres_{}'.format(counter))
            else:
                self.model.addConstr(lhs <= 1, name='C3_{}'.format(counter))
            counter += 1

    @printer
    def Const4_a(self):
        # C2: Conservacion de Flujo para libres
        c2 = 0
        for i, c, e in self.t_y_libres:
            if (i, c, e + 1) in self.t_y_libres:
                lhs = gp.LinExpr(self.y[i, c, e + 1])
                rhs = gp.LinExpr(self.y[i, c, e])
                if (i, c, e) in self.xc_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_c[i, j, c, e] for j in self.xc_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xc_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_c[j, i, c, e] for j in self.xc_jce_i[i, c, e])))
                if (i, c, e) in self.xm_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_m[i, j, c, e] for j in self.xm_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xm_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_m[j, i, c, e] for j in self.xm_jce_i[i, c, e])))
                if (i, c, e) in self.xl_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_l[i, j, c, e] for j in self.xl_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xl_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_l[j, i, c, e] for j in self.xl_jce_i[i, c, e])))
                if (i,c,e,) in self.t_exile:
                    rhs.add(gp.LinExpr(self.x_ex[i,c,e]), -1)
                #if (c, e) in self.t_exile:
                #    rhs.add(gp.LinExpr(self.ex[c, e]), -1)
                self.model.addConstr(lhs == rhs, name="C4_FRE[{},{},{}]".format(i,c,e))
                c2 += 1

    @printer
    def Const4_b(self):
        counter = 0
        for i, c, e in self.t_y_fijos:
            if (i, c, e + 1) in self.t_y_fijos:
                self.model.addConstr(self.y[i, c, e] == self.y[i, c, e + 1], name="C4_FIX_{}".format(counter))
                counter += 1

    @printer
    def Const4_c(self):
        counter = 0
        for i, c, e in self.t_y_salen:
            if e == self.e_sale[c] and (i, c, e + 1) in self.t_y_salen:
                self.model.addConstr(self.y[i, c, e + 1] == self.y[i, c, e] - self.w[i, c, e],
                                     name="C2_OUT_{}".format(counter))
                counter += 1
            elif e < self.e_sale[c] and (i, c, e + 1) in self.t_y_salen:
                rhs = gp.LinExpr(self.y[i, c, e])
                lhs = gp.LinExpr(self.y[i, c, e + 1])
                if (i, c, e) in self.xc_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_c[i, j, c, e] for j in self.xc_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xc_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_c[j, i, c, e] for j in self.xc_jce_i[i, c, e])))
                if (i, c, e) in self.xm_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_m[i, j, c, e] for j in self.xm_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xm_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_m[j, i, c, e] for j in self.xm_jce_i[i, c, e])))
                if (i, c, e) in self.xl_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_l[i, j, c, e] for j in self.xl_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xl_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_l[j, i, c, e] for j in self.xl_jce_i[i, c, e])))
                self.model.addConstr(lhs == rhs, name="C4_OUTF_{}".format(counter))
                counter += 1

    @printer
    def Const4_d(self):
        counter = 0
        for i, c, e in self.t_y_llegan:
            if e == self.e_llega[c] and (i, c, e+1) in self.t_y_llegan:
                self.model.addConstr(self.y[i, c, e+1] == self.v[i, c, e] + self.y[i, c, e], name="C2_INB_{}".format(counter))
                counter += 1
            elif e > self.e_llega[c] and (i, c, e + 1) in self.t_y_llegan:
                lhs = gp.LinExpr(self.y[i, c, e + 1])
                rhs = gp.LinExpr(self.y[i, c, e])
                if (i, c, e) in self.xc_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_c[i, j, c, e] for j in self.xc_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xc_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_c[j, i, c, e] for j in self.xc_jce_i[i, c, e])))
                if (i, c, e) in self.xm_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_m[i, j, c, e] for j in self.xm_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xm_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_m[j, i, c, e] for j in self.xm_jce_i[i, c, e])))
                if (i, c, e) in self.xl_ice_j:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_l[i, j, c, e] for j in self.xl_ice_j[i, c, e])), -1)
                if (i, c, e) in self.xl_jce_i:
                    rhs.add(gp.LinExpr(gp.quicksum(self.x_l[j, i, c, e] for j in self.xl_jce_i[i, c, e])))
                self.model.addConstr(lhs == rhs, name="C2_INBF_{}".format(counter))
                counter += 1

    @printer
    def Const5(self):
        # C5: Todos deben salir cuando les toca desde algun lugar
        # sum_i w[i,c,e] = 1 for c, e

        c5set = set([(c, e) for i, c, e in self.t_w_salen])
        self.model.addConstrs(
            (gp.quicksum(self.w[t.orig, c, e] for t in self.t_w_salen if t.cont == c and t.etapa == e)
             == 1 for c, e in c5set),
            name='c5')

    @printer
    def Const6(self):
        # C6: Los que llegan lo hacen a un solo lugar
        # sum_i v[i,c,e] = 1 for c, e
        c6set = set([(c, e) for i, c, e in self.t_v_llegan])
        self.model.addConstrs(
            (gp.quicksum(self.v[t.dest, c, e] for t in self.t_v_llegan if t.cont == c and t.etapa == e)
             == 1 for c, e in c6set),
            name='C6')

    @printer
    def Const7(self):
        # C9: Un movimiento por etapa
        # sum_i,j,c x_c[i,j,c,e] + x_c[i,j,c,e] + v[= 1  Ve
        counter = 0
        c9set_close = set([e for i, j, c, e in self.t_x_close])
        c9set_medium = set([e for i, j, c, e in self.t_x_medium])
        c9set_long = set([e for i, j, c, e in self.t_x_long])

        xc_e_ijc = {}
        for t in self.t_x_close:
            if t.etapa not in xc_e_ijc:
                xc_e_ijc[t.etapa] = set([(t.orig, t.dest, t.cont)])
            else:
                xc_e_ijc[t.etapa].add((t.orig, t.dest, t.cont))

        xm_e_ijc = {}
        for t in self.t_x_medium:
            if t.etapa not in xm_e_ijc:
                xm_e_ijc[t.etapa] = set([(t.orig, t.dest, t.cont)])
            else:
                xm_e_ijc[t.etapa].add((t.orig, t.dest, t.cont))

        xl_e_ijc = {}
        for t in self.t_x_long:
            if t.etapa not in xl_e_ijc:
                xl_e_ijc[t.etapa] = set([(t.orig, t.dest, t.cont)])
            else:
                xl_e_ijc[t.etapa].add((t.orig, t.dest, t.cont))

        v_e_ic = {}
        for t in self.t_v_llegan:
            if t.etapa not in v_e_ic:
                v_e_ic[t.etapa] = set([(t.dest, t.cont)])
            else:
                v_e_ic[t.etapa].add((t.dest, t.cont))

        w_e_jc = {}
        for t in self.t_w_salen:
            if t.etapa not in w_e_jc:
                w_e_jc[t.etapa] = set([(t.orig, t.cont)])
            else:
                w_e_jc[t.etapa].add((t.orig, t.cont))
        
        xe_e_ic = {}
        for t in self.t_exile:
            if t.etapa not in xe_e_ic:
                xe_e_ic[t.etapa] = set([(t.orig, t.cont)])
            else:
                xe_e_ic[t.etapa].add((t.orig, t.cont))

        for e in self.etapas:
            lhs = gp.LinExpr(0)
            if e in c9set_close:
                lhs.add(gp.LinExpr(
                    (gp.quicksum(self.x_c[i, j, c, e] for i, j, c in xc_e_ijc[e]))
                ))
            if e in c9set_medium:
                lhs.add(gp.LinExpr(
                    (gp.quicksum(self.x_m[i, j, c, e] for i, j, c in xm_e_ijc[e]))
                ))
            if e in c9set_long:
                lhs.add(gp.LinExpr(
                    (gp.quicksum(self.x_l[i, j, c, e] for i, j, c in xl_e_ijc[e]))
                ))
            if e in v_e_ic:
                lhs.add(gp.LinExpr(
                    (gp.quicksum(self.v[i, c, e] for i, c in v_e_ic[e]))
                ))
            if e in w_e_jc:
                lhs.add(gp.LinExpr(
                    (gp.quicksum(self.w[j, c, e] for j, c in w_e_jc[e]))
                ))
            if e in xe_e_ic:
                lhs.add(gp.LinExpr(
                    (gp.quicksum(self.x_ex[i,c,e] for i, c in xe_e_ic[e]))
                ))
            self.model.addConstr(lhs <= 1, name='C7_{}'.format(counter))
            counter += 1

    @printer
    def Const8(self):
        # C10: Prohibido salir de posiciones bloqueadas
        # sum_j,c x[i,j,c,e] <= 1 - sum_c y[i,c,e] for i in B for e

 
        for i, e in self.c10set:
            if e > 1:
                if i in self.B.keys():
                    for k in self.B[i]:
                        if (k, e) in self.yc_ie.keys():
                            rhs = gp.LinExpr(1 - gp.quicksum(self.y[k, c, e] for c in self.yc_ie[k, e]))
                            lhs = gp.LinExpr(0)
                            if (i, e) in self.xc_ie_jc.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.x_c[i, j, c, e] for j, c in self.xc_ie_jc[i, e])))
                            if (i, e) in self.xm_ie_jc.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.x_m[i, j, c, e] for j, c in self.xm_ie_jc[i, e])))
                            if (i, e) in self.xl_ie_jc.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.x_l[i, j, c, e] for j, c in self.xl_ie_jc[i, e])))
                            if (i, e) in self.w_ie_c.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.w[i, c, e] for c in self.w_ie_c[i, e])))
                            if (i, e) in self.xe_ie_c.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.x_ex[i,c,e] for c in self.xe_ie_c[i, e])))
                            aux_constr = self.model.addConstr(lhs <= rhs, name='C8[{},{},{}]'.format(i, e, k))
                            aux_constr.setAttr("Lazy", 1)
                            

    @printer
    def Const9(self):
        # C11: No puedo llegar a posiciones bloquedas
        counter = 0
        for j, e in self.c10set:
            if j in self.B.keys():
                if e > 1:
                    for k in self.B[j]:
                        if (k, e) in self.yc_ie.keys():
                            rhs = gp.LinExpr(1 - gp.quicksum(self.y[k, c, e] for c in self.yc_ie[k, e]))
                            lhs = gp.LinExpr(0)
                            if (j, e) in self.xc_je_ic.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.x_c[i, j, c, e] for i, c in self.xc_je_ic[j, e])))
                            if (j, e) in self.xm_je_ic.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.x_m[i, j, c, e] for i, c in self.xm_je_ic[j, e])))
                            if (j, e) in self.xl_je_ic.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.x_l[i, j, c, e] for i, c in self.xl_je_ic[j, e])))
                            if (j, e) in self.v_je_c.keys():
                                lhs.add(gp.LinExpr(gp.quicksum(self.v[j, c, e] for c in self.v_je_c[j, e])))
                            aux_constr = self.model.addConstr(lhs <= rhs, name='C9_{}'.format(counter))
                            aux_constr.setAttr("Lazy", 1)
                            counter += 1

    @printer
    def Const10(self):
        # C12: No puedo llegar al aire
        counter = 0
        for j, e in self.c10set:
            if e > 1:
                if j in self.U.keys():
                    if self.U[j]:
                        lhs = gp.LinExpr(0)
                        rhs = gp.LinExpr(gp.quicksum(self.y[self.U[j], c, e] for c in self.yc_ie[self.U[j], e]))
                        if (j, e) in self.xc_je_ic.keys():
                            lhs.add(gp.LinExpr(gp.quicksum(self.x_c[i, j, c, e] for i, c in self.xc_je_ic[j, e])))
                        if (j, e) in self.xm_je_ic.keys():
                            lhs.add(gp.LinExpr(gp.quicksum(self.x_m[i, j, c, e] for i, c in self.xm_je_ic[j, e])))
                        if (j, e) in self.xl_je_ic.keys():
                            lhs.add(gp.LinExpr(gp.quicksum(self.x_l[i, j, c, e] for i, c in self.xl_je_ic[j, e])))
                        if (j, e) in self.v_je_c.keys():
                            lhs.add(gp.LinExpr(gp.quicksum(self.v[j, c, e] for c in self.v_je_c[j, e])))
                        aux_constr = self.model.addConstr(lhs <= rhs, name='C10_{}'.format(counter))
                        aux_constr.setAttr("Lazy", 1)
                        counter += 1

    @printer
    def Const11(self):
        # #############  RESTRICCIONES DE RELOCACIONES ################
        # C19: Definir R

        c19set_c = set([(j, c, e) for i, j, c, e in self.t_x_close])
        c19set_m = set([(j, c, e) for i, j, c, e in self.t_x_medium])
        c19set_l = set([(j, c, e) for i, j, c, e in self.t_x_long])

        cont_que_salen_antes = {}
        for c in self.c_salen + self.c_llegan + self.c_libres:
            cont_que_salen_antes[c] = []
            for b in self.cont:
                if self.T[b] < self.T[c]:
                    if c in cont_que_salen_antes.keys():
                        cont_que_salen_antes[c].append(b)
        counter = 0
        for j, c, e in c19set_c:
            if cont_que_salen_antes[c]:
                if j in self.B_I.keys():
                    lhs = gp.LinExpr(len(self.B_I[j]) * (self.z[e] + 1))
                    rhs1 = gp.LinExpr()
                    for k in self.B_I[j]:
                        for b in cont_que_salen_antes[c]:
                            if (k, b, e) in self.all_y:
                                rhs1.add(gp.LinExpr(self.y[k, b, e]))

                    rhs2 = gp.LinExpr(len(self.B_I[j]) * gp.quicksum(self.x_c[i, j, c, e]
                                                                     for i in self.xc_jce_i[j, c, e]))
                    aux_constr = self.model.addConstr(lhs >= rhs1 + rhs2, name='C11_{}'.format(counter))
                    aux_constr.setAttr("Lazy", 1)
                    counter += 1

        for j, c, e in c19set_m:
            if cont_que_salen_antes[c]:
                if j in self.B_I.keys():
                    lhs = gp.LinExpr(len(self.B_I[j]) * (self.z[e] + 1))
                    rhs1 = gp.LinExpr()
                    for k in self.B_I[j]:
                        for b in cont_que_salen_antes[c]:
                            if (k, b, e) in self.all_y:
                                rhs1.add(gp.LinExpr(self.y[k, b, e]))

                    rhs2 = gp.LinExpr(len(self.B_I[j]) * gp.quicksum(self.x_m[i, j, c, e]
                                                                     for i in self.xm_jce_i[j, c, e]))
                    aux_constr = self.model.addConstr(lhs >= rhs1 + rhs2, name='C11_{}'.format(counter))
                    aux_constr.setAttr("Lazy", 1)
                    counter += 1

        for j, c, e in c19set_l:
            if cont_que_salen_antes[c]:
                if j in self.B_I.keys():
                    lhs = gp.LinExpr(len(self.B_I[j]) * (self.z[e] + 1))
                    rhs1 = gp.LinExpr()
                    for k in self.B_I[j]:
                        for b in cont_que_salen_antes[c]:
                            if (k, b, e) in self.all_y:
                                rhs1.add(gp.LinExpr(self.y[k, b, e]))

                    rhs2 = gp.LinExpr(len(self.B_I[j]) * gp.quicksum(self.x_l[i, j, c, e]
                                                                     for i in self.xl_jce_i[j, c, e]))
                    aux_constr = self.model.addConstr(lhs >= rhs1 + rhs2, name='C11_{}'.format(counter))
                    aux_constr.setAttr("Lazy", 1)
                    counter += 1

    def BuildStartingSolution(self):
        # Lista de contenedores a definir:
        # print('SALEN')
        for c in self.c_salen:
            #    print(c, self.e_sale[c], self.pos_ini_cont[c], self.B[self.pos_ini_cont[c]], self.etapas_activas[c])
            if not self.etapas_activas[c]:
                a = self.w[self.pos_ini_cont[c], c, self.e_sale[c]]
                a.start = 1
        #        print('{} fijo en 1'.format(a))
        '''
        print('LLEGAN')
        for c in self.c_llegan:
            print(c)
        print('LIBRES')
        for c in self.c_libres:
            print(c, self.etapas_activas[c])
        '''
        for t in self.t_x_close:
            self.x_c[t].start = 0
        for t in self.t_x_medium:
            self.x_m[t].start = 0
        for t in self.t_x_long:
            self.x_l[t].start = 0



    def getModelStatus(self, outpath='', stats_file=None):
        status = self.model.Status
        solution = self.status_dic[status]
        if status == 2 or status == 9:
            modeltime = self.model.Runtime
            gap = self.model.MIPGap

            z_count = 0
            for t in self.etapas:
                if self.z[t].x > 0:
                    z_count += 1
            n_exiled = 0
            #for t in self.t_exile:
            #    if self.ex[t].x > 0:
            for t in self.t_exile:
                if self.x_ex[t].x > 0:
                    n_exiled += 1
            self.print_resumen_y(outpath)
            self.print_resumen_x(outpath)
            mod_status = '{:10} {:10} INB:{:4} OUT:{:4} FRE:{:4} T: {:4.2f}s GAP: {:4.2f} z:{:3} e:{:3}'.format(
                self.model_name,
                solution,
                len(self.c_llegan),
                len(self.c_salen),
                len(self.c_libres),
                modeltime,
                gap,
                z_count,
                n_exiled)
        else:
            mod_status = '{:10} {:10} INB:{:4} OUT:{:4} FRE:{:4}'.format(
                self.model_name, solution, len(self.c_llegan), len(self.c_salen), len(self.c_libres))
        if stats_file:
            f = open(stats_file, 'a+')
            f.write('{}  '.format(time.strftime('%d-%b-%y %H:%M:%S', time.localtime())))
            f.write(mod_status)
            f.write('\n')
        return solution

    def print_resumen_y(self, path=''):
        f1 = open('{}_y'.format(path + self.model_name), 'w')
        f1.write('\nFIJOS\n')
        f1.write('{:21}'.format('Cont/pos'))
        for e in self.etapas:
            f1.write('{:3}'.format(e))
        f1.write('\n')
        p1set = list(set([(i, c) for i, c, e in self.t_y_fijos]))
        for i, c in p1set:
            line = '{:7} {:13}'.format(i, c)
            se_imprime = False
            for e in self.etapas:
                if not se_imprime and self.y[i, c, e].x != 0:
                    se_imprime = True
                line += '{:3}'.format(int(self.y[i, c, e].x))
            if se_imprime:
                f1.write(line + '\n')

        f1.write('\nSALEN\n')
        f1.write('{:21}'.format('Cont/pos'))
        for e in self.etapas:
            f1.write('{:3}'.format(e))
        f1.write('\n')
        p1set = list(set([(i, c) for i, c, e in self.t_y_salen]))
        for i, c in p1set:
            line = '{:7} {:13}'.format(i, c)
            se_imprime = False
            for e in self.etapas:
                if (i, c, e) in self.t_y_salen:
                    if not se_imprime and self.y[i, c, e].x != 0:
                        se_imprime = True
                    line += '{:3}'.format(int(self.y[i, c, e].x))
                else:
                    line += '{:3}'.format('-')
            if se_imprime:
                f1.write(line + '\n')

        f1.write('\nLLEGAN\n')
        f1.write('{:21}'.format('Cont/pos'))
        for e in self.etapas:
            f1.write('{:3}'.format(e))
        f1.write('\n')
        p1set = list(set([(i, c) for i, c, e in self.t_y_llegan]))
        for i, c in p1set:
            line = '{:7} {:13}'.format(i, c)
            se_imprime = False
            for e in self.etapas:
                try:
                    if not se_imprime and self.y[i, c, e].x != 0:
                        se_imprime = True
                    line += '{:3}'.format(int(self.y[i, c, e].x))
                except KeyError:
                    line += '{:3}'.format('-')
            if se_imprime:
                f1.write(line + '\n')

        f1.write('\nLIBRES\n')
        f1.write('{:21}'.format('Cont/pos'))
        for e in self.etapas:
            f1.write('{:3}'.format(e))
        f1.write('\n')
        p1set = list(set([(i, c) for i, c, e in self.t_y_libres]))
        for i, c in p1set:
            line = '{:7} {:13}'.format(i, c)
            se_imprime = False
            for e in self.etapas:
                try:
                    if not se_imprime and self.y[i, c, e].x != 0:
                        se_imprime = True
                    line += '{:3}'.format(int(self.y[i, c, e].x))
                except KeyError:
                    line += '{:3}'.format('-')
            if se_imprime:
                f1.write(line + '\n')

        f1.write('FIN')
        f1.close()
        # print('impreso')

    def print_resumen_x(self, path=''):
        # Resumen Movimientos
        resumen = []
        for t in self.t_x_close:
            if self.x_c[t].x > 0.1:
                resumen.append([t.etapa, 'XC', t.cont, t.orig, t.dest, self.x_c[t].varName, self.x_c[t].x])
        for t in self.t_x_medium:
            if self.x_m[t].x > 0.1:
                resumen.append([t.etapa, 'XM', t.cont, t.orig, t.dest, self.x_m[t].varName, self.x_m[t].x])

        for t in self.t_x_long:
            if self.x_l[t].x > 0.1:
                resumen.append([t.etapa, 'XL', t.cont, t.orig, t.dest, self.x_l[t].varName, self.x_l[t].x])

        for t in self.t_w_salen:
            if self.w[t].x > 0.1:
                resumen.append([t.etapa, 'W', t.cont, t.orig, 'SALE', self.w[t].varName, self.w[t].x])

        for t in self.t_v_llegan:
            if self.v[t].x > 0.1:
                resumen.append([t.etapa, 'V', t.cont, 'LLEGA', t.dest, self.v[t].varName, self.v[t].x])
        #for t in self.t_exile:
        #    if self.ex[t].x > 0.1:
        for t in self.t_exile:
            if self.x_ex[t].x > 0: 
                #resumen.append([t.etapa, 'EX', t.cont, 'SOMEWHERE', 'EL LIMBO', self.ex[t].varName, self.ex[t].x])
                resumen.append([t.etapa, 'EX', t.cont, t.orig, 'EL LIMBO', self.x_ex[t].varName, self.x_ex[t].x])

        resumen.sort(key=lambda items: items[0])
        # for i in resumen:
        #    print('{:2} {:2} {:13} {:9} {:8} {}'.format(i[0], i[1], i[2], i[3], i[4], i[5], i[6]))

        f2 = open('{}_x'.format(path + self.model_name), 'w+')
        f2.write('{:2} {:4} {:13} {:9} {:8}\n'.format('E', 'Tipo', 'Cont', 'Origen', 'Destino'))
        for i in resumen:
            f2.write('{:2} {:2} {:13} {:9} {:8}\n'.format(i[0], i[1], i[2], i[3], i[4]))
        # print('Impreso x.txt')


def run(name, cont_file, pos_file, outpath='', echo=False, sf=''):
    MODEL = TLSMODEL(name=name, files=[cont_file, pos_file], echo=echo)
    MODEL.InitModel()
    MODEL.BuildStartingSolution()
    MODEL.model.setParam('TimeLimit', 600)
    MODEL.model.setParam('MIPFocus', 2)
    MODEL.model.setParam('Presolve', 1)
    MODEL.model.setParam('Method', 1)
    MODEL.model.write('modelo.lp')
    MODEL.model.optimize()
    solution = MODEL.getModelStatus(outpath=outpath, stats_file=sf)
    with open(pathlib.Path(outpath, 'status'), 'w') as f:
        f.write(solution)
    #MODEL.model.dispose()
    return solution


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cont_file")
    parser.add_argument("pos_file")
    parser.add_argument("-s", "--stats_file", help="File to append the results resume")
    parser.add_argument("-n", "--name", default="NONAME", help=" The name of the model")
    parser.add_argument("-o", "--outpath", help="Path to store the solution files")
    parser.add_argument("-e", "--echo", action="store_true", help="Set verbosity True")

    args = parser.parse_args()
    salida = run(args.name,
                 args.cont_file,
                 args.pos_file,
                 outpath=args.outpath,
                 echo=args.echo,
                 sf=args.stats_file)

    # print(salida)
    # run('test', 'inputs/95040_contenedores.json', 'inputs/95040_posiciones.json', echo=False)
