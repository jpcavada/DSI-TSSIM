'''
Simulacion de un patio de contendores sin servicios (Solo entradas, salidas y recolocaciones)
VERSION STOCASTICA
Juan Pablo Cavada
Inicio: 19-08-2019
'''

# Import block
import yard_class_st as yr
import simpy
import os

import json
import logging

# logging.basicConfig(level=logging.INFO, format='%(message)s')


# Global Variables
INSTANCE_NAME = "NONAME"
START_SIM_CLOCK = 0
FINAL_SIM_CLOCK = 259200
START_RECOUNT_TIME = 43200
END_RECOUND_TIME = 259200
'''
1 dia = 1440
1 meses = 43200
2 meses = 86400
3 meses = 129600
180 dias = 259200


'''

# Inicialization Variables
# YARD_BLOCKS_NAMES = ["R"]
YARD_BLOCKS_NAMES = ["LU", "RU", "LD", "RD"]
BAYS_WIDE_NAMES = ["A", "B", "X", "Y"]
# BAYS_WIDE_NAMES = ["A", "B"]
BAYS_LONG_SIZE = 12
BAYS_HIGH_SIZE = 4

INITIAL_BOX_FILE = r"input_files/arrivalstest.ini"
INITIAL_SERVICE_FILE = "input_files/services.ini"

BLOCKING_BAYS_FILE = "input_files/layout_blocking_bays.ini"
CLOSE_BAYS_FILE = "input_files/layout_bay_distance_close.ini"
MEDIUM_BAYS_FILE = "input_files/layout_bay_distance_medium.ini"

OUTPUT_FILES_FOLDER = "output_files/"
RELOCATION_CRITERIA = "RI"

CRANES_NUM = 1
SERVICE_AREA_SIZE = 2
ARRIVING_BOXES = 0

# Parametros Estocasticos
random_seed = 123


###############################       SIMULACION         ###############################
class TLSSIM():
    def __init__(self, name=INSTANCE_NAME, arrivals=INITIAL_BOX_FILE, criteria=RELOCATION_CRITERIA,
                 outputdir=OUTPUT_FILES_FOLDER):
        # SET REPORTING VARIABLES
        self.DATA_BOX_ARRIVALS = [("#BOX_NAME", "CALL_TIME", "CRANE_TIME", "EXECUTION_TIME")]
        self.DATA_BOX_REMOVALS = [("#BOX_NAME", "CALL_TIME", "CRANE_TIME", "EXECUTION_TIME", "RELOCATIONS")]
        self.DATA_BOX_RELOCATIONS = [("#BOX_NAME", "CALL_TIME", "EXECUTION_TIME", "CALLER_BOX", "MOVCOST")]
        self.DATA_BOX_SERVICE = [("#BOX_NAME", "START_TIME", "EXECUTION_TIME", "END_TIME")]
        self.DATA_NUMBER_OF_BOXES = [("#TIMESTEP", "BOXES_IN_YARD")]
        self.COUNT_NUMBER_OF_BOXES = 0

        self.DATA_SNAPSHOTS = []
        self.DATA_NUMBER_OF_BOXES_DAY = []

        self.DATA_DECISION = [("#TIMESTAMP", "BOX_NAME, BOX_ORIGIN, DECISIONS")]
        self.run_status = "waiting"
        self.rep_name = name

        global INSTANCE_NAME
        INSTANCE_NAME = name
        global INITIAL_BOX_FILE
        INITIAL_BOX_FILE = arrivals
        global RELOCATION_CRITERIA
        RELOCATION_CRITERIA = criteria
        global OUTPUT_FILES_FOLDER
        OUTPUT_FILES_FOLDER = outputdir
        if not os.path.exists(OUTPUT_FILES_FOLDER):
            os.makedirs(OUTPUT_FILES_FOLDER)

        logging.getLogger().setLevel(logging.DEBUG)
        self.logger = logging.getLogger('sim_log')
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + '.log', 'w')
        file_handler.setLevel(logging.ERROR)
        self.logger.addHandler(file_handler)

    def runSimulation(self, quiet=False):
        global patio
        try:
            console_handler = logging.StreamHandler()
            if quiet:
                console_handler.setLevel(logging.CRITICAL)
            else:
                console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)

            # Elementos de la simulacion

            sim_enviroment = simpy.Environment()  # CREA EL ENVIROMENT
            sim_res_CRANES = self.MonitoredResource(sim_enviroment, CRANES_NUM)  # AGREGA LOS RECURSOS GRUA AL ENV
            sim_res_SERVICE_SLOT = simpy.Resource(sim_enviroment,
                                                  SERVICE_AREA_SIZE)  # Agrega recursos de service slots.

            ###############################     INICIALIZACION     ###############################
            # CREAMOS EL PATIO con los blockes YARD_BLOCK_NAMES
            patio = yr.ContainerYard(len(YARD_BLOCKS_NAMES), YARD_BLOCKS_NAMES, relocation_criteria=RELOCATION_CRITERIA)

            # A CADA BLOCK SE LE AGREGAN LOS BAHIAS CORRESPONDIENTES
            for block in patio.YRD_getBlockList():
                for bay_wide_name in BAYS_WIDE_NAMES:
                    for bay_long_name in range(BAYS_LONG_SIZE):
                        block.BLK_addBay(BAYS_HIGH_SIZE, block.BLK_getName() + bay_wide_name + str(bay_long_name + 1))

            # patio.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
            # Agregamos la tabla de adyacencias
            self.INI_createAdjacencyTable(patio, BLOCKING_BAYS_FILE)

            # AGREGAMOS LA TABLA DE DISTANCIAS
            self.INI_setBayDistance(patio, CLOSE_BAYS_FILE, MEDIUM_BAYS_FILE)

            self.logger.debug(patio.YRD_getBayDistance(patio.YRD_getBayByName("LUA1"), patio.YRD_getBayByName("LUB1")))
            self.logger.debug(patio.YRD_getBayDistance(patio.YRD_getBayByName("LUA12"), patio.YRD_getBayByName("LDX1")))
            self.logger.debug(patio.YRD_getBayDistance(patio.YRD_getBayByName("RUB3"), patio.YRD_getBayByName("LUY4")))
            self.logger.debug(patio.YRD_getBayDistance(patio.YRD_getBayByName("RUB3"), patio.YRD_getBayByName("LUX5")))
            self.logger.debug(patio.YRD_getBayDistance(patio.YRD_getBayByName("LDY10"), patio.YRD_getBayByName("LUB1")))

            # Inicializcion de contenedores ya en patio.

            Box_existing_list = []
            '''
            Box_existing_list = INI_startingYardLayout(patio)
            patio.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
            '''
            # Leemos la lista de contenedores que van a llegar a la simulacion
            Box_arrival_list = self.INI_readArrivingBoxes(print_to_console=True)

            # ------------------------------- PROCESOS ---------------------------------------#
            '''
            # PROCESOS DE LLEGADE DE CONTENEDORES: a cada contenedor que va a llegar se dispara un proceso de llegada.
            '''
            for box in Box_arrival_list:
                sim_enviroment.process(self.GEN_arrival(sim_enviroment, patio, sim_res_CRANES, box))

            # PROCES DE SALIDA DE CONTENEDORES
            master_box_list = Box_arrival_list + Box_existing_list
            self.logger.info("Agendado Salidas de contenedores existentes")
            for existing_box in master_box_list:
                if existing_box.date_out > 0:
                    sim_enviroment.process(self.GEN_removal(sim_enviroment, patio, sim_res_CRANES, existing_box))

            '''
            PROCESO DE SERVICIOS
            '''
            # service_list = [yard_class.Service(["INI_2", "INI_4"], 3, 25, 5)]
            service_list = self.INI_readSimpleServices(master_box_list, print_to_console=True)
            for servicio in service_list:
                sim_enviroment.process(
                    self.GEN_services(sim_enviroment, patio, sim_res_CRANES, sim_res_SERVICE_SLOT, servicio))
            '''
            PROCESO DE RECOPILACION DATOS
            '''
            sim_enviroment.process(self.GEN_snapshots(sim_enviroment, patio, 1440 * 5))
            sim_enviroment.process(self.GEN_EndOfDayReports(sim_enviroment, patio, 1440))

            '''
            MODELO DE CONTROL
            '''
            sim_enviroment.process(self.GEN_export_sim_status(sim_enviroment,
                                                              patio,
                                                              Box_arrival_list,
                                                              look_ahead_time=1440/2,
                                                              export_interval=129600,
                                                              file_name='export'))

            # ----------------------------- EJECUCION ---------------------------------------#
            self.logger.warning("INICIO SIMULACION")
            self.logger.info("Iniciando simulacion")
            sim_enviroment.run(until=FINAL_SIM_CLOCK)

            self.logger.info("------------------------- Fin Simulacion-----------------------")
            self.logger.info("=========== FINAL YARD LAYOUT =============")
            patio.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
            self.export_snapshot(self.DATA_SNAPSHOTS, OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + "_snapshots.txt")
            self.logger.info("============= REMOVED BOXES ===============")
            self.logger.info(str(patio.removed_box_list))

            self.logger.info("============= CRANE RESOURCE ==============")
            self.logger.info(str(sim_res_CRANES.data))
            self.logger.info("=========== REGISTIO EVENTOS: ARRIVALS ==============")
            self.logger.info(str(self.DATA_BOX_ARRIVALS))
            self.export_data(self.DATA_BOX_ARRIVALS, OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + "_arrivals.txt")
            self.logger.info("=========== REGISTIO EVENTOS: REMOVALS ==============")
            self.logger.info(str(self.DATA_BOX_REMOVALS))
            self.export_data(self.DATA_BOX_REMOVALS, OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + "_removals.txt")
            self.logger.info("=========== REGISTIO EVENTOS: RELOCATIONS ==============")
            self.logger.info(str(self.DATA_BOX_RELOCATIONS))
            self.export_data(self.DATA_BOX_RELOCATIONS, OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + "_relocations.txt")
            self.logger.info("=========== REGISTIO EVENTOS: SERVICES ==============")
            self.logger.info(str(self.DATA_BOX_SERVICE))

            self.export_data(self.DATA_DECISION, OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + "_decisions.txt")
            # self.export_data(self.DATA_DECISION, OUTPUT_FILES_FOLDER + '\\' + INSTANCE_NAME + "_decisions2.txt")

            self.export_data(self.DATA_BOX_SERVICE, OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + "_services.txt")
            # export_data(self.DATA_NUMBER_OF_BOXES, OUTPUT_FILES_FOLDER + '\\' + INSTANCE_NAME + "_box_counter.txt")
            self.export_snapshot(self.DATA_NUMBER_OF_BOXES_DAY,
                                 OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + "_box_counter_day.txt")
            self.run_status = "COMPLETE"

            handlers = self.logger.handlers[:]
            for handler in handlers:
                handler.close()
                self.logger.removeHandler(handler)

        except Exception as ex:
            self.logger.exception(ex)
            self.run_status = "Unable to complete"

            # Imprimo el estado del patio en un archivo
            error_File = open(OUTPUT_FILES_FOLDER + '/' + INSTANCE_NAME + "_failed_snapshot.txt", "w+")
            error_File.write(patio.YRD_exportYardSnapShot(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE))

            handlers = self.logger.handlers[:]
            for handler in handlers:
                handler.close()
                self.logger.removeHandler(handler)

            return 0

    ###############################     RUTINAS DE INICIALIZACION   ###############################

    def INI_createAdjacencyTable(self, yard, layout_blocking_bays_file=BLOCKING_BAYS_FILE):
        '''
        In this function define all the adjacency (blocked and blocking) bays.
        :param yard: the container yard
        :param layout_blocking_bays_file: the file with the adyacency constraints.
        '''
        blocking_file = open(layout_blocking_bays_file, "r")
        for line in blocking_file.readlines():
            if not (line[:1] == '#'):
                tokens = line.strip("\n").split("=")
                yard.YRD_getBlockByName(tokens[0][:2]).BLK_addAdjacentBay(tokens[0], tokens[1])
                # yard.YRD_getBlock(1).BLK_addAdjacentBay("MC7", "MD7")


    def INI_setBayDistance(self, yard, close_bays_file, medium_bays_file):

        # Set all distances as "L"
        for o_block in yard.YRD_getBlockList():
            for o_bay in o_block.BLK_getBayList():
                for i_block in yard.YRD_getBlockList():
                    for i_bay in i_block.BLK_getBayList():
                        yard.YRD_setBayDistance(o_bay, i_bay, "L")

        # Set Close bays
        close_file = open(close_bays_file, "r")
        for line in close_file.readlines():
            tokens = line.strip("\n").split("=")
            origin_bay_name = tokens[0]
            destiny_bay_list = tokens[1].split(",")
            for destiny_bay_name in destiny_bay_list:
                yard.YRD_setBayDistance(yard.YRD_getBayByName(origin_bay_name), yard.YRD_getBayByName(destiny_bay_name),
                                        "C")
        close_file.close()

        # Set  Medium bays
        medium_file = open(medium_bays_file, "r")
        for line in medium_file.readlines():
            tokens = line.strip("\n").split("=")
            origin_bay_name = tokens[0]
            destiny_bay_list = tokens[1].split(",")
            for destiny_bay_name in destiny_bay_list:
                yard.YRD_setBayDistance(yard.YRD_getBayByName(origin_bay_name), yard.YRD_getBayByName(destiny_bay_name),
                                        "M")
        medium_file.close()

    def INI_readArrivingBoxes(self, print_to_console=False):
        '''
        Reads the file with all the arriving boxes and returns a list with them.
        :param print_to_console:
        :return:
        '''
        return_box_arrival_list = []
        arrival_box_file = open(INITIAL_BOX_FILE, "r")
        for line in arrival_box_file.readlines():
            if not (line[:1] == '#'):
                tokens = line.split()
                name = tokens[0]
                arrival_date = int(tokens[1])
                leaving_date = int(tokens[2])
                return_box_arrival_list.append(yr.Box(name, date_in=arrival_date, date_out=leaving_date))

        if print_to_console:
            self.logger.info("Lista de llegadas Programadas")
            for box in return_box_arrival_list:
                self.logger.info("BOX NAME : {} arrives at {} leaves at {}, ( {} )".format(box.BOX_getName(),
                                                                                           box.BOX_getName(),
                                                                                           box.BOX_getDateIn(),
                                                                                           box.BOX_getDateOut(),
                                                                                           box.BOX_getExpectedDateOut()
                                                                                           ))
        return return_box_arrival_list

    def INI_readSimpleServices(self, box_list, print_to_console=False):
        return_service_list = []
        service_file = open(INITIAL_SERVICE_FILE, "r")
        for line in service_file.readlines():
            if not (line[:1] == '#'):
                tokens = line.split()
                name = tokens[0]
                length = int(tokens[1])
                start_time = int(tokens[2])
                due_time = start_time
                return_service_list.append(yr.Service(containers_list=[name],
                                                      start_time=start_time,
                                                      due_time=due_time,
                                                      service_lenght=length))
        if print_to_console:
            self.logger.info("Lista de servicios Programados")
            for serv in return_service_list:
                self.logger.info("BOX LIST : {} enter service at {} for {}".format(serv.container_list, serv.start_time,
                                                                                   serv.service_lenght))
        return return_service_list

    ###############################     RUTINAS DE EVENTOS   ###############################
    def GEN_arrival(self, env, yard, sim_res_Crane, arriving_box):
        '''
        Generator proces for arriving containers. This process wait until the container arrives. Then when it arrives will
        find a location for the new container (YRD_findBoxNewPosition) and call a crane to move it taking the time necessary
        to complete the movement (YRD_moveInboundContainer).
        :param env: the simulation enviroment
        :param yard: the ContainerYard
        :param sim_res_Crane: the simulation resouerce for cranes
        :param arriving_box: the container that its arriving
        '''
        self.logger.info(
            "[" + str(env.now) + "] Se espera que " + str(arriving_box.BOX_getName()) + " llegue a las " + str(
                arriving_box.BOX_getDateIn()))
        yield env.timeout(arriving_box.BOX_getDateIn() - env.now)
        data_call_time = env.now
        # Cuando llega, se le busca lugar y luego se mueve
        self.logger.info("[" + str(env.now) + "] Llego " + str(arriving_box.BOX_getName()) + " y esta esperando grúa")
        arriving_box.bay = "Inbound"
        with sim_res_Crane.request() as i_have_a_crane:
            yield i_have_a_crane
            data_crane_time = env.now
            destiny_block, destiny_bay, decision_string = yard.YRD_BoxAllocation(arriving_box)
            self.DATA_DECISION.append((env.now, decision_string))
            move_succ, move_cost = yard.YRD_moveInboundContainer(arriving_box, destiny_bay)
            if move_succ:
                self.logger.info(
                    "[" + str(env.now) + "] Grua moviendo a " + str(arriving_box.BOX_getName()) + " a " + str(
                        destiny_bay) + " por " + str(move_cost) + " min")
                yield env.timeout(move_cost)
                data_execution_time = env.now
                self.logger.info(
                    "[" + str(env.now) + "] Grua finaliza movimiento de " + str(arriving_box.BOX_getName()))
                # yard.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
                self.DATA_BOX_ARRIVALS.append(
                    (arriving_box.BOX_getName(), data_call_time, data_crane_time, data_execution_time))
                # global self.COUNT_NUMBER_OF_BOXES
                self.COUNT_NUMBER_OF_BOXES = self.COUNT_NUMBER_OF_BOXES + 1
                self.DATA_NUMBER_OF_BOXES.append((data_execution_time, self.COUNT_NUMBER_OF_BOXES))

    def GEN_removal(self, env, yard, sim_res_Crane, leaving_box):
        '''
        Generator proces for leaving containers. This process wait until the containers time to leave. Then it will check if
        it is accesible (YRD_isBoxBlocked). For each blocking container it will call for a relocation (YRD_relocateBox).
        After all relocations are done (or if it was not blocked) it will call for crane to move the container to out of the
         system (YRD_removeBox).
        :param env: the simulation enviroment
        :param yard: the ContainerYard
        :param sim_res_Crane: the simulation resouerce for cranes
        :param leaving_box: the container that its leaving the yard
        '''
        self.logger.info("[" + str(env.now) + "] " + str(leaving_box.BOX_getName()) + " se debe retirar a las " + str(
            leaving_box.BOX_getDateOut()))
        yield env.timeout(leaving_box.BOX_getDateOut() - env.now)

        data_removal_call_time = env.now

        remove_succ, remove_cost = False, 0  # forward declaration
        # If container is in service area is removed from there
        if yard.YRD_isBoxInService(leaving_box):
            remove_succ = True
            remove_cost = 0
            self.logger.info(
                "[{}] Time to remove {}, but will be removed once service in complete".format(env.now, leaving_box))
            data_removal_crane_time = 0
            data_removal_execute = 0
            data_removal_relocatins = 0
            self.DATA_BOX_REMOVALS.append((str(leaving_box.BOX_getName()),
                                           str(data_removal_call_time),
                                           str(data_removal_crane_time),
                                           str(data_removal_execute),
                                           str(data_removal_relocatins)))

        else:
            self.logger.info("[{}] Hora de retirar {}, esperando grua".format(env.now, leaving_box))
            # Espero a que llegue una grúa
            with sim_res_Crane.request() as i_have_a_crane:
                yield i_have_a_crane
                data_removal_crane_time = env.now
                self.logger.info("[{}] Grua llega para retirar {}".format(env.now, leaving_box))

                # Cuando se debe retirar, se revisa si esta bloqueado
                blockers_list = yard.YRD_isBoxBlocked(leaving_box)
                data_removal_relocatins = len(blockers_list)
                if not (blockers_list == []):
                    self.logger.info("[{}] RELOC: debemos relocar a {}".format(env.now, blockers_list))
                    # yard.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
                    involved_boxes = blockers_list.copy()
                    involved_boxes.append(leaving_box)
                    # Llamamos a la relocacion de todos los blockers
                    while blockers_list:
                        for blocker in blockers_list:
                            # Find an accessible box to remove
                            if not yard.YRD_isBoxBlocked(blocker):
                                blockers_list.remove(blocker)
                                involved_boxes.remove(blocker)
                                destiny_bay, decision_string = yard.YRD_findRelocationPosition(blocker, involved_boxes)
                                # Si esta bloqueado, Falla!!
                                if yard.YRD_isBoxBlocked(blocker):
                                    raise Exception(
                                        "Relocating a blocked BOX {} from {}, original list was {} now is {}, Check code!!".format(
                                            blocker, blocker.bay, blockers_list, yard.YRD_isBoxBlocked(blocker)))
                                # Llamamos una grua
                                reloc_succ, reloc_cost = yard.YRD_relocateBox(blocker, destiny_bay)
                                if reloc_succ:
                                    data_reloc_call = env.now
                                    yield env.timeout(reloc_cost)
                                    self.logger.info(
                                        "[{}] RELOC: se recoloco {} a {}, costo {}".format(env.now, blocker,
                                                                                           destiny_bay, reloc_cost))
                                    data_reloc_execute = env.now
                                    self.DATA_BOX_RELOCATIONS.append((blocker.BOX_getName(), data_reloc_call,
                                                                      data_reloc_execute, leaving_box.BOX_getName(),
                                                                      reloc_cost))
                                    self.DATA_DECISION.append((env.now, decision_string))
                                else:
                                    raise Exception("[{}]Relocation of {} failed".format(env.now, blocker))
                # Cuando este accesible retiro el contenedor
                remove_succ, remove_cost = yard.YRD_removeBox(leaving_box, env.now)
            if remove_succ:
                yield env.timeout(remove_cost)
                self.logger.info("[{}] Retirando {} con la grua, costo {}".format(env.now, leaving_box, remove_cost))
                data_removal_execute = env.now
                self.DATA_BOX_REMOVALS.append((leaving_box.BOX_getName(), data_removal_call_time,
                                               data_removal_crane_time, data_removal_execute, data_removal_relocatins))
                # global self.COUNT_NUMBER_OF_BOXES
                self.COUNT_NUMBER_OF_BOXES = self.COUNT_NUMBER_OF_BOXES - 1
                self.DATA_NUMBER_OF_BOXES.append((data_removal_execute, self.COUNT_NUMBER_OF_BOXES))
            else:
                yard.YRD_printYard(4, 12)
                raise Exception("Box {} failed to be removed, blocked by {}".format(leaving_box, remove_cost))

    def GEN_moveToService(self, env, yard, sim_res_Crane, box):
        '''
        Moves a container from the yard to the service area. Then it calls for a crane (sim_res_Crane). With a crane in house it relocates any blocking
        containers. Finally it moves the container to the service area (YRD_moveBoxToService).
        :param env:
        :param yard:
        :param sim_res_Crane:
        :param box:
        '''
        self.logger.info("[{}] Inicia movimiento de {} a servicio".format(env.now, box))

        with sim_res_Crane.request() as i_have_a_crane:
            yield i_have_a_crane
            self.logger.info("[{}] Grua llega para llevar {} a servicio".format(env.now, box))

            ### INICIO RELOCACIONES:  Cuando se debe retirar, se revisa si esta bloqueado #########################
            blockers_list = yard.YRD_isBoxBlocked(box)

            if not (blockers_list == []):
                self.logger.info("[{}] RELOC: debemos relocar a {} por servicio".format(env.now, blockers_list))
                # Llamamos a la relocacion de todos los blockers
                involved_boxes = blockers_list.copy()
                involved_boxes.append(box)
                for blocker in blockers_list:
                    involved_boxes.remove(blocker)
                    destiny_bay, decision_string = yard.YRD_findRelocationPosition(blocker, involved_boxes)
                    # Si esta bloqueado, Falla!!
                    if yard.YRD_isBoxBlocked(blocker):
                        raise Exception("Relocating a blocked BOX {}, Check code!!".format(blocker))
                    # Llamamos una grua
                    reloc_succ, reloc_cost = yard.YRD_relocateBox(blocker, destiny_bay)
                    if reloc_succ:
                        data_reloc_call = env.now
                        yield env.timeout(reloc_cost)
                        self.logger.info("[{}] RELOC: se recoloco {} a {}, costo {}".format(
                            env.now,
                            blocker,
                            destiny_bay,
                            reloc_cost))
                        data_reloc_execute = env.now
                        self.DATA_BOX_RELOCATIONS.append(
                            (blocker.BOX_getName(), data_reloc_call, data_reloc_execute, box.BOX_getName(), reloc_cost))
                        self.DATA_DECISION.append((env.now, decision_string))
                        #### FIN RELOCACIOES ####################################################

            # Cuando este accesible nuevo el contenedor al area de servicio
            move_succ, move_cost = yard.YRD_moveBoxToService(box)
            if move_succ:
                yield env.timeout(move_cost)
                self.logger.info("[{}] Moving {} to service, cost {}".format(env.now, box, move_cost))

    def GEN_moveFromService(self, env, yard, sim_res_Crane, box):
        self.logger.info("[{}] Box {} is leaving service area".format(env.now, box))
        with sim_res_Crane.request() as i_have_a_crane:
            yield i_have_a_crane
            destiny_block, destiny_bay, decision_string = yard.YRD_BoxAllocation(box)
            self.DATA_DECISION.append((env.now, decision_string))
            move_succ, move_cost = yard.YRD_moveInboundContainer(box, destiny_bay)
            if move_succ:
                self.logger.info("[" + str(env.now) + "] Crane moving " + str(box.BOX_getName()) + " to " + str(
                    destiny_bay) + " at cost " + str(move_cost) + " from service area")
                yield env.timeout(move_cost)
                self.logger.info("[" + str(env.now) + "] Crane completed movement of " + str(box.BOX_getName()))

    def GEN_services(self, env, yard, sim_res_Crane, sim_res_Service_slot, service):
        '''
        Generator process for an scheduled service. It wil start when the start_time of the service equals the run time,
        it will call for all the boxes en service.container_list to be moved to the container area. Once they are moved the
        service starts for service.service_lenght timesteps. After thar the containers are returned to the yard or removed
        if their removal time is past.
        :param env: the simulation enviroment
        :param yard: the container yard
        :param service: the service to be done
        '''
        self.logger.info("[{}] SERV: Calendarizado servicio de {} a las {}".format(
            env.now,
            service.container_list,
            service.start_time))
        service.SRV_setStatus(0)
        time_to_wait = max(0, service.start_time - env.now)
        yield env.timeout(time_to_wait)
        service_boxes = []
        for box_names in service.container_list:
            aux_box = yard.YRD_findBoxByName(box_names)
            if not aux_box:
                raise Exception("Error in service, box name {} not found".format(box_names))
            service_boxes.append(aux_box)
        # Ask for enought slots in service area
        available_slots = []
        for box in service_boxes:
            available_slots.append(sim_res_Service_slot.request())
            box.in_service = True  # Container is flagged as "In Service" so it can not be removed.
        yield simpy.events.AllOf(env, available_slots)
        # Once all slots are secured, proceed to move the containers.
        moves = [
            env.process(self.GEN_moveToService(env, yard, sim_res_Crane, box))
            for box in service_boxes]
        yield simpy.events.AllOf(env, moves)
        self.logger.info("[{}] SERV: servicio de {} in position ".format(env.now, service.container_list))
        # Wait until the servive due time
        yield env.timeout(max(0, service.due_time - env.now))
        data_execution_time = env.now
        self.logger.info("[{}] SER: service of {} starting now".format(env.now, service.container_list))
        yield env.timeout(service.service_lenght)
        data_end_time = env.now
        # After service return containers to yard or remove them if removal time has passed.
        for box in service_boxes:
            if env.now >= box.BOX_getDateOut() > 0:
                remove_succ, remove_cost = yard.YRD_removeBoxFromService(box, env.now)
                box.in_service = False
                if remove_succ:
                    self.logger.info("[{}] Removing {} from service area, costs {}".format(env.now, box, remove_cost))
                    sim_res_Service_slot.release(available_slots.pop(0))  # Release the service slot
                    self.DATA_BOX_REMOVALS.append((str(box.BOX_getName()), str(box.BOX_getDateOut()), str(env.now),
                                                   str(env.now), str(0)))
                    # global self.COUNT_NUMBER_OF_BOXES
                    self.COUNT_NUMBER_OF_BOXES = self.COUNT_NUMBER_OF_BOXES - 1
                    self.DATA_NUMBER_OF_BOXES.append((str(env.now), self.COUNT_NUMBER_OF_BOXES))
            else:
                # Call for a move
                yield env.process(self.GEN_moveFromService(env, yard, sim_res_Crane, box))
                # once move is complete release service slot and flag that box is no longer in service
                box.in_service = False
                sim_res_Service_slot.release(available_slots.pop(0))
        self.logger.info("[{}] Service of {} is complete".format(env.now, service_boxes))
        self.DATA_BOX_SERVICE.append(
            (str(service_boxes), str(service.start_time), str(data_execution_time), str(data_end_time)))

    def GEN_snapshots(self, env, yard, snap_interval):
        '''
        A intervalos regulares actualiza los reportes
        '''
        # global self.DATA_SNAPSHOTS
        # Esperamos al inicio del periodo de test
        yield env.timeout(START_RECOUNT_TIME)
        self.DATA_SNAPSHOTS.append(
            'Yard @' + str(env.now) + '\n' + yard.YRD_exportYardSnapShot(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE))
        while env.now < END_RECOUND_TIME:
            yield env.timeout(snap_interval)
            snap = yard.YRD_exportYardSnapShot(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
            self.DATA_SNAPSHOTS.append('Yard @' + str(env.now) + '\n' + snap)

    def GEN_EndOfDayReports(self, env, yard, report_interval):

        # global self.DATA_NUMBER_OF_BOXES_DAY
        # yield env.timeout(START_RECOUNT_TIME)
        self.DATA_NUMBER_OF_BOXES_DAY.append(str(env.now) + ',' + str(self.COUNT_NUMBER_OF_BOXES))
        while env.now < END_RECOUND_TIME:
            yield env.timeout(report_interval)
            self.DATA_NUMBER_OF_BOXES_DAY.append(str(env.now) + ',' + str(self.COUNT_NUMBER_OF_BOXES))

            # Update the global progress of the simulation

            self.run_status = int(((env.now / FINAL_SIM_CLOCK) * 100 + 1))

    def GEN_export_sim_status(self, env, yard, arrivals,
                              export_interval=1440, look_ahead_time=1440, file_name='export'):
        """
        A intervalos regulares exporta el status del patio en un JSON
            :param arrivals:
            :param file_name:
            :param look_ahead_time:
            :param env: simulation enviromnent
            :param yard: patio de contenedores
            :param export_interval: tiempo (en ts) entre reportes 1440 = 1 dia
            :return: nada
        """
        # Listas/Diccionarios temporales
        positions = []
        cont_list = {}  # box_name: [Tc, position, arrival/leave time]
        # Reporte inicial de posiciones y costos
        Reporte_inicial_ok = 0
        distancias = {}
        # INTERVALO DE REPORTE #
        # while env.now < END_RECOUND_TIME:
        while env.now < 1:
            yield env.timeout(export_interval)
            # print("({}) IMPORTANDO ESTADO SIMULADOR".format(env.now))
            # Crear directorio de contenedores #
            for block in yard.YRD_getBlockList():
                for bay in block.BLK_getBayList():
                    tmp_bay = bay.BAY_getName()
                    for i in range(4):
                        tmp_pos = tmp_bay + '-' + str(i + 1)
                        positions.append(tmp_pos)
                        # Escribir estado contenedor
                        if bay.BAY_getBox(i):
                            tmp_cont_name = bay.BAY_getBox(i).BOX_getName()
                            tmp_cont_date_Out = bay.BAY_getBox(i).BOX_getDateOut()
                            if tmp_cont_date_Out <= env.now + look_ahead_time:
                                tmp_status = 'sale'
                            else:
                                tmp_status = 'fijo'
                            cont_list[tmp_cont_name] = [tmp_cont_date_Out, tmp_pos, tmp_status]
                        # Obtener Distancias
                        if Reporte_inicial_ok == 0:
                            for block2 in yard.YRD_getBlockList():
                                for bay2 in block2.BLK_getBayList():
                                    if bay != bay2:
                                        a = '{}_{}'.format(tmp_bay, bay2.BAY_getName())
                                        distancias[a] = yard.YRD_getBayDistance(bay, bay2)

            # Marcamos todos los que bloquean como 'mover'
            for key, val in cont_list.items():
                if val[2] == 'sale':
                    bl_list = yard.YRD_isBoxBlocked(yard.YRD_findBoxByName(key))
                    if bl_list:
                        for blocking in bl_list:
                            blocking_name = blocking.BOX_getName()
                            aux_val = cont_list[blocking_name]
                            cont_list[blocking_name] = [aux_val[0], aux_val[1], 'mover']

            # Agregamos los contenedores nuevos
            llegan_cont = {}
            for arr in arrivals:
                if env.now <= arr.BOX_getDateIn() <= env.now + look_ahead_time:
                    # print(arr, arr.BOX_getName(), arr.BOX_getDateIn(), arr.BOX_getDateOut())
                    llegan_cont[arr.BOX_getName()] = [arr.BOX_getDateIn(), arr.BOX_getDateOut()]

            # Export JSON files
            export_data = {
                #               'posiciones': positions,
                'contenedores': cont_list,
                'cont_llegadas': llegan_cont
            }
            with open(file_name + '.json', 'w+') as outfile:
                json.dump(export_data, outfile, indent=4)

            if Reporte_inicial_ok == 0:
                export_data_pos = {
                    'posiciones': positions,
                    'distancias': distancias
                }
                with open(file_name + '_posiciones.json', 'w+') as outfile:
                    json.dump(export_data_pos, outfile, indent=4)
                Reporte_inicial_ok = 1

    def export_data(self, data_string_list, file_name):
        file = open(file_name, "w+")
        for line in data_string_list:
            string_line = ""
            for item in line:
                string_line = string_line + str(item) + ","
            file.write(string_line + "\n")
        file.close()

    def export_snapshot(self, data_string_list, file_name):
        file = open(file_name, "w+")
        for line in data_string_list:
            file.write(line + "\n")
        file.close()

    class MonitoredResource(simpy.Resource):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.data = []

        def request(self, *args, **kwargs):
            self.data.append((self._env.now, len(self.queue)))
            return super().request(*args, **kwargs)

        def release(self, *args, **kwargs):
            self.data.append((self._env.now, len(self.queue)))
            return super().release(*args, **kwargs)

    #################   Ejecutor    ################


if __name__ == '__main__':
    import time

    # sim = TLSSIM()
    sim = TLSSIM(name="LACAGA",
                 outputdir="INSTANCES/DEBUG/Salidas/",
                 criteria="MM",
                 arrivals="INSTANCES/INSTANCES_180D_F2_100/arrivals_1.ini")
    start_time = time.time()
    sim.runSimulation(quiet=True)
    end_time = time.time()
    delta = end_time - start_time
    print("Demoró {} secs".format(delta))
