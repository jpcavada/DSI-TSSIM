'''
Simulacion de un patio de contendores sin servicios (Solo entradas, salidas y recolocaciones)

Juan Pablo Cavada
Inicio: 19-08-2019
'''

# Import block
import yard_class
import numpy
import simpy

# Global Variables
START_SIM_CLOCK = 0
FINAL_SIM_CLOCK = 43200

'''
1 dia = 1440
1 meses = 43200
2 meses = 86400
3 meses = 129600
'''

# Inicialization Variables
#YARD_BLOCKS_NAMES = ["R"]
YARD_BLOCKS_NAMES = ["LU", "RU", "LD", "RD"]
BAYS_WIDE_NAMES = ["A", "B", "X", "Y"]
#BAYS_WIDE_NAMES = ["A", "B"]
BAYS_LONG_SIZE = 12
BAYS_HIGH_SIZE = 4
INITIAL_BOX_FILE = r"input_files\arrivalstest.ini"
INITIAL_SERVICE_FILE = "input_files\services.ini"
BLOCKING_BAYS_FILE = "input_files\layout_blocking_bays.ini"

CLOSE_BAYS_FILE = "input_files\layout_bay_distance_close.ini"
MEDIUM_BAYS_FILE = "input_files\layout_bay_distance_medium.ini"

OUTPUT_FILES_FOLDER = "output_files"

CRANES_NUM = 1
SERVICE_AREA_SIZE = 2
ARRIVING_BOXES = 0

DATA_BOX_ARRIVALS = [("#BOX_NAME", "CALL_TIME", "CRANE_TIME", "EXECUTION_TIME")]
DATA_BOX_REMOVALS = [("#BOX_NAME", "CALL_TIME", "CRANE_TIME", "EXECUTION_TIME", "RELOCATIONS")]
DATA_BOX_RELOCATIONS = [("#BOX_NAME", "CALL_TIME", "EXECUTION_TIME", "CALLER_BOX")]
DATA_BOX_SERVICE = [("#BOX_NAME", "START_TIME", "EXECUTION_TIME", "END_TIME")]
DATA_NUMBER_OF_BOXES = [("#TIMESTEP","BOXES_IN_YARD")]
COUNT_NUMBER_OF_BOXES = 0

###############################       SIMULACION         ###############################
def main():
    # Elementos de la simulacion

    sim_enviroment = simpy.Environment()  # CREA EL ENVIROMENT
    sim_res_CRANES = MonitoredResource(sim_enviroment, CRANES_NUM)  # AGREGA LOS RECURSOS GRUA AL ENV
    sim_res_SERVICE_SLOT = simpy.Resource(sim_enviroment, SERVICE_AREA_SIZE) # Agrega recursos de service slots.



    ###############################     INICIALIZACION     ###############################
    # CREAMOS EL PATIO con los blockes YARD_BLOCK_NAMES
    patio = yard_class.ContainerYard(len(YARD_BLOCKS_NAMES), YARD_BLOCKS_NAMES)

    # A CADA BLOCK SE LE AGREGAN LOS BAHIAS CORRESPONDIENTES
    for block in patio.YRD_getBlockList():
        for bay_wide_name in BAYS_WIDE_NAMES:
            for bay_long_name in range(BAYS_LONG_SIZE):
                block.BLK_addBay(BAYS_HIGH_SIZE, block.BLK_getName() + bay_wide_name + str(bay_long_name + 1))

    patio.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
    # Agregamos la tabla de adyacencias
    INI_createAdjacencyTable(patio, BLOCKING_BAYS_FILE)

    # AGREGAMOS LA TABLA DE DISTANCIAS
    INI_setBayDistance(patio, CLOSE_BAYS_FILE, MEDIUM_BAYS_FILE)

    print(patio.YRD_getBayDistance(patio.YRD_getBayByName("LUA1"), patio.YRD_getBayByName("LUB1")))
    print(patio.YRD_getBayDistance(patio.YRD_getBayByName("LUA12"), patio.YRD_getBayByName("LDX1")))
    print(patio.YRD_getBayDistance(patio.YRD_getBayByName("RUB3"), patio.YRD_getBayByName("LUY4")))
    print(patio.YRD_getBayDistance(patio.YRD_getBayByName("RUB3"), patio.YRD_getBayByName("LUX5")))
    print(patio.YRD_getBayDistance(patio.YRD_getBayByName("LDY10"), patio.YRD_getBayByName("LUB1")))

    # Inicializcion de contenedores ya en patio.

    Box_existing_list = []
    '''
    Box_existing_list = INI_startingYardLayout(patio)
    patio.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
    '''
    #Leemos la lista de contenedores que van a llegar a la simulacion
    Box_arrival_list = INI_readArrivingBoxes(print_to_console=True)

    #------------------------------- PROCESOS ---------------------------------------#
    '''
    # PROCESOS DE LLEGADE DE CONTENEDORES: a cada contenedor que va a llegar se dispara un proceso de llegada.
    '''
    for box in Box_arrival_list:
        sim_enviroment.process(GEN_arrival(sim_enviroment, patio, sim_res_CRANES,box))


    # PROCES DE SALIDA DE CONTENEDORES
    master_box_list = Box_arrival_list + Box_existing_list
    print("Agendado Salidas de contenedores existentes")
    for existing_box in master_box_list:
        if existing_box.date_out > 0:
            sim_enviroment.process(GEN_removal(sim_enviroment, patio, sim_res_CRANES, existing_box))


    '''
    PROCESO DE SERVICIOS
    '''
    #service_list = [yard_class.Service(["INI_2", "INI_4"], 3, 25, 5)]
    service_list = INI_readSimpleServices(master_box_list, print_to_console=True)
    for servicio in service_list:
        sim_enviroment.process(GEN_services(sim_enviroment, patio, sim_res_CRANES, sim_res_SERVICE_SLOT, servicio))

    #----------------------------- EJECUCION ---------------------------------------#
    print("Iniciando simulacion")
    sim_enviroment.run(until=FINAL_SIM_CLOCK)
    print(sim_res_SERVICE_SLOT.count)


    print("------------------------- Fin Simulacion-----------------------")
    print("=========== FINAL YARD LAYOUT =============")
    patio.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)

    print("============= REMOVED BOXES ===============")
    print(patio.removed_box_list)

    print("============= CRANE RESOURCE ==============")
    print(sim_res_CRANES.data)
    print("=========== REGISTIO EVENTOS: ARRIVALS ==============")
    print(DATA_BOX_ARRIVALS)
    export_data(DATA_BOX_ARRIVALS, OUTPUT_FILES_FOLDER + "\export_arrivals.txt")
    print("=========== REGISTIO EVENTOS: REMOVALS ==============")
    print(DATA_BOX_REMOVALS)
    export_data(DATA_BOX_REMOVALS, OUTPUT_FILES_FOLDER + "\export_removals.txt")
    print("=========== REGISTIO EVENTOS: RELOCATIONS ==============")
    print(DATA_BOX_RELOCATIONS)
    export_data(DATA_BOX_RELOCATIONS, OUTPUT_FILES_FOLDER + "\export_relocations.txt")
    print("=========== REGISTIO EVENTOS: RELOCATIONS ==============")
    print(DATA_BOX_SERVICE)


    export_data(DATA_BOX_SERVICE, OUTPUT_FILES_FOLDER + "\export_services.txt")
    export_data(DATA_NUMBER_OF_BOXES, OUTPUT_FILES_FOLDER + r"\export_box_counter.txt")

###############################     RUTINAS DE INICIALIZACION   ###############################
def INI_createAdjacencyTable(yard, layout_blocking_bays_file=BLOCKING_BAYS_FILE):
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
            #yard.YRD_getBlock(1).BLK_addAdjacentBay("MC7", "MD7")

def INI_setBayDistance(yard, close_bays_file, medium_bays_file):

    #Set all distances as "L"
    for o_block in yard.YRD_getBlockList():
        for o_bay in o_block.BLK_getBayList():
            for i_block in yard.YRD_getBlockList():
                for i_bay in i_block.BLK_getBayList():
                    yard.YRD_setBayDistance(o_bay, i_bay, "L")

    #Set Close bays
    close_file = open(close_bays_file, "r")
    for line in close_file.readlines():
        tokens = line.strip("\n").split("=")
        origin_bay_name = tokens[0]
        destiny_bay_list = tokens[1].split(",")
        for destiny_bay_name in destiny_bay_list:
            yard.YRD_setBayDistance(yard.YRD_getBayByName(origin_bay_name), yard.YRD_getBayByName(destiny_bay_name), "C")
    close_file.close()

    #Set  Medium bays
    medium_file = open(medium_bays_file, "r")
    for line in medium_file.readlines():
        tokens = line.strip("\n").split("=")
        origin_bay_name =  tokens[0]
        destiny_bay_list = tokens[1].split(",")
        for destiny_bay_name in destiny_bay_list:
            yard.YRD_setBayDistance(yard.YRD_getBayByName(origin_bay_name), yard.YRD_getBayByName(destiny_bay_name), "M")
    medium_file.close()


def DEP_INI_arrival_list(earliest_arrival_time=START_SIM_CLOCK, latest_arrival_time=FINAL_SIM_CLOCK,
                     print_to_console=False):
    '''
    Creates de list of all the container that are going to arrive.
    :return: unordered list of all arrival containers.
    '''
    return_box_arrival_list = []
    for i in range(ARRIVING_BOXES):
        new_box_hora_llegada = numpy.random.randint(earliest_arrival_time, latest_arrival_time - 50)
        new_box_hora_salida = numpy.random.randint(new_box_hora_llegada + 5, latest_arrival_time)
        return_box_arrival_list.append(
            yard_class.Box("B" + str(i + 1), date_in=new_box_hora_llegada, date_out=new_box_hora_salida))
    if print_to_console:
        print("Lista de llegadas Programadas")
        for box in return_box_arrival_list:
            print("BOX NAME : {} arrives at {} leaves at {}".format(box.BOX_getName(), box.BOX_getDateIn(),
                                                                    box.BOX_getDateOut()))
    return return_box_arrival_list

def DEP_INI_startingYardLayout(yard):
    existing_box_list = []
    starting_box_file = open(INITIAL_BOX_FILE, "r")
    for line in starting_box_file.readlines():
        if not (line[:1] == '#'):
            line = line.replace(' ', '').strip('\n')
            split_line = line.split(",")
            new_box = yard_class.Box(split_line[2],
                                     date_in=int(split_line[3]),
                                     date_out=int(split_line[4]),
                                     date_service=int(split_line[5]))
            yard.YRD_addNewIntialBox(new_box, split_line[1], split_line[0])
            existing_box_list.append(new_box)
    return existing_box_list

def INI_readArrivingBoxes(print_to_console=False):
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
            return_box_arrival_list.append(yard_class.Box(name, date_in=arrival_date, date_out=leaving_date))

    if print_to_console:
        print("Lista de llegadas Programadas")
        for box in return_box_arrival_list:
            print("BOX NAME : {} arrives at {} leaves at {}".format(box.BOX_getName(), box.BOX_getDateIn(),
                                                                    box.BOX_getDateOut()))
    return return_box_arrival_list

def INI_readSimpleServices(box_list, print_to_console=False):
    return_service_list = []
    service_file = open(INITIAL_SERVICE_FILE,"r")
    for line in service_file.readlines():
        if not (line[:1] == '#'):
            tokens = line.split()
            name = tokens[0]
            length = int(tokens[1])
            start_time = int(tokens[2])
            due_time = start_time
            return_service_list.append(yard_class.Service(containers_list=[name],
                                                          start_time=start_time,
                                                          due_time=due_time,
                                                          service_lenght=length))
    if print_to_console:
        print("Lista de servicios Programados")
        for serv in return_service_list:
            print("BOX LIST : {} enter service at {} for {}".format(serv.container_list, serv.start_time, serv.service_lenght))
    return return_service_list


###############################     RUTINAS DE EVENTOS   ###############################
def GEN_arrival(env, yard, sim_res_Crane, arriving_box):
    '''
    Generator proces for arriving containers. This process wait until the container arrives. Then when it arrives will
    find a location for the new container (YRD_findBoxNewPosition) and call a crane to move it taking the time necessary
    to complete the movement (YRD_moveInboundContainer).
    :param env: the simulation enviroment
    :param yard: the ContainerYard
    :param sim_res_Crane: the simulation resouerce for cranes
    :param arriving_box: the container that its arriving
    '''
    print("[" + str(env.now) + "] Se espera que " + str(arriving_box.BOX_getName()) + " llegue a las " + str(
        arriving_box.BOX_getDateIn()))
    yield env.timeout(arriving_box.BOX_getDateIn() - env.now)
    data_call_time = env.now
    # Cuando llega, se le busca lugar y luego se mueve
    print("[" + str(env.now) + "] Llego " + str(arriving_box.BOX_getName()) + " y esta esperando grúa")
    with sim_res_Crane.request() as i_have_a_crane:
        yield i_have_a_crane
        data_crane_time = env.now
        destiny_block, destiny_bay = yard.YRD_findBoxNewPosition(arriving_box)
        move_succ, move_cost = yard.YRD_moveInboundContainer(arriving_box, destiny_bay)
        if move_succ:
            print("[" + str(env.now) + "] Grua moviendo a " + str(arriving_box.BOX_getName()) + " a " + str(
                destiny_bay) + " por " + str(move_cost) + " min")
            yield env.timeout(move_cost)
            data_execution_time = env.now
            print("[" + str(env.now) + "] Grua finaliza movimiento de " + str(arriving_box.BOX_getName()))
            #yard.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
            DATA_BOX_ARRIVALS.append((arriving_box.BOX_getName(), data_call_time, data_crane_time, data_execution_time))
            global COUNT_NUMBER_OF_BOXES
            COUNT_NUMBER_OF_BOXES = COUNT_NUMBER_OF_BOXES + 1
            DATA_NUMBER_OF_BOXES.append((data_execution_time, COUNT_NUMBER_OF_BOXES))

def GEN_removal(env, yard, sim_res_Crane, leaving_box):
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
    print("[" + str(env.now) + "] " + str(leaving_box.BOX_getName()) + " se debe retirar a las " + str(
        leaving_box.BOX_getDateOut()))
    yield env.timeout(leaving_box.BOX_getDateOut() - env.now)

    data_removal_call_time = env.now


    remove_succ, remove_cost = False, 0 #forward declaration
    #If container is in service area is removed from there
    if yard.YRD_isBoxInService(leaving_box):
        remove_succ = True
        remove_cost = 0
        print("[{}] Time to remove {}, but will be removed once service in complete".format(env.now, leaving_box))
        data_removal_crane_time = 0
        data_removal_execute = 0
        data_removal_relocatins = 0
        DATA_BOX_REMOVALS.append((leaving_box.BOX_getName(), data_removal_call_time, data_removal_crane_time,
                                  data_removal_execute, data_removal_relocatins))

    else:
        print("[{}] Hora de retirar {}, esperando grua".format(env.now, leaving_box))
        #Espero a que llegue una grúa
        with sim_res_Crane.request() as i_have_a_crane:
            yield i_have_a_crane
            data_removal_crane_time = env.now
            print("[{}] Grua llega para retirar {}".format(env.now, leaving_box))

            #Cuando se debe retirar, se revisa si esta bloqueado
            blockers_list = yard.YRD_isBoxBlocked(leaving_box)
            data_removal_relocatins = len(blockers_list)
            if not(blockers_list == []):
                print("[{}] RELOC: debemos relocar a {}".format(env.now, blockers_list))
                #yard.YRD_printYard(len(BAYS_WIDE_NAMES), BAYS_LONG_SIZE)
                involved_boxes = blockers_list.copy()
                involved_boxes.append(leaving_box)
                #Llamamos a la relocacion de todos los blockers
                for blocker in blockers_list:
                    involved_boxes.remove(blocker)
                    #print(involved_boxes)
                    #print(blockers_list)
                    destiny_bay = yard.YRD_findRelocationPosition(blocker, involved_boxes)
                    # Si esta bloqueado, Falla!!
                    if yard.YRD_isBoxBlocked(blocker):
                        raise Exception("Relocating a blocked BOX {} from {}, original list was {} now is {}, Check code!!".format(blocker, blocker.bay,blockers_list, yard.YRD_isBoxBlocked(blocker)))
                    # Llamamos una grua
                    reloc_succ, reloc_cost = yard.YRD_relocateBox(blocker, destiny_bay)
                    if reloc_succ:
                        data_reloc_call =env.now
                        yield env.timeout(reloc_cost)
                        print("[{}] RELOC: se recoloco {} a {}, costo {}".format(env.now, blocker, destiny_bay, reloc_cost))
                        data_reloc_execute =env.now
                        DATA_BOX_RELOCATIONS.append((blocker.BOX_getName(), data_reloc_call, data_reloc_execute, leaving_box.BOX_getName()))
            #Cuando este accesible retiro el contenedor
            remove_succ, remove_cost = yard.YRD_removeBox(leaving_box, env.now)
        if remove_succ:
            yield env.timeout(remove_cost)
            print("[{}] Retirando {} con la grua, costo {}".format(env.now, leaving_box, remove_cost))
            data_removal_execute = env.now
            DATA_BOX_REMOVALS.append((leaving_box.BOX_getName(), data_removal_call_time, data_removal_crane_time, data_removal_execute, data_removal_relocatins))
            global COUNT_NUMBER_OF_BOXES
            COUNT_NUMBER_OF_BOXES = COUNT_NUMBER_OF_BOXES - 1
            DATA_NUMBER_OF_BOXES.append((data_removal_execute, COUNT_NUMBER_OF_BOXES))

'''
def GEN_relocation(env, yard, sim_res_Crane, relocating_box):
    ¿
    Generator process for relocating containers. The process will check if the container is accessible, choose a new
    location for the container (YRD_findRelocationPosition) and call a crane to perform the movement.
    :param env: the simulation enviroment
    :param yard: the ContainerYard
    :param sim_res_Crane: the simulation resouerce for cranes
    :param relocating_box: the container that its being relocated
    ¿
    print("[{}] RELOC: Calendarizada relocacion de {}".format(env.now, relocating_box))

    #Si esta bloqueado, Falla!!
    if yard.YRD_isBoxBlocked(relocating_box):
        raise Exception("Relocating a blocked BOX {}, Check code!!".format(relocating_box))
    #Llamamos una grua
    with sim_res_Crane.request() as i_have_a_crane:
        yield i_have_a_crane
        #Buscamos donde poner el nuevo contenedor
        
        destiny_bay = yard.YRD_findRelocationPosition(relocating_box)
        reloc_succ, reloc_cost = yard.YRD_relocateBox(relocating_box, destiny_bay)
        if reloc_succ:
            yield env.timeout(reloc_cost)
            print("[{}] RELOC: se recoloco {} a {}".format(env.now, relocating_box, destiny_bay))
'''
def GEN_moveToService(env, yard, sim_res_Crane, box):
    '''
    Moves a container from the yard to the service area. Then it calls for a crane (sim_res_Crane). With a crane in house it relocates any blocking
    containers. Finally it moves the container to the service area (YRD_moveBoxToService).
    :param env:
    :param yard:
    :param sim_res_Crane:
    :param box:
    '''
    print("[{}] Inicia movimiento de {} a servicio".format(env.now, box))

    with sim_res_Crane.request() as i_have_a_crane:
        yield i_have_a_crane
        print("[{}] Grua llega para llevar {} a servicio".format(env.now, box))

        ### INICIO RELOCACIONES:  Cuando se debe retirar, se revisa si esta bloqueado #########################
        blockers_list = yard.YRD_isBoxBlocked(box)


        if not (blockers_list == []):
            print("[{}] RELOC: debemos relocar a {} por servicio".format(env.now, blockers_list))
            # Llamamos a la relocacion de todos los blockers
            involved_boxes = blockers_list.copy()
            involved_boxes.append(box)
            for blocker in blockers_list:
                involved_boxes.remove(blocker)
                destiny_bay = yard.YRD_findRelocationPosition(blocker, involved_boxes)
                # Si esta bloqueado, Falla!!
                if yard.YRD_isBoxBlocked(blocker):
                    raise Exception("Relocating a blocked BOX {}, Check code!!".format(blocker))
                # Llamamos una grua
                reloc_succ, reloc_cost = yard.YRD_relocateBox(blocker, destiny_bay)
                if reloc_succ:
                    data_reloc_call = env.now
                    yield env.timeout(reloc_cost)
                    print("[{}] RELOC: se recoloco {} a {}, costo {}".format(
                                                                            env.now,
                                                                            blocker,
                                                                            destiny_bay,
                                                                            reloc_cost))
                    data_reloc_execute = env.now
                    DATA_BOX_RELOCATIONS.append(
                        (blocker.BOX_getName(), data_reloc_call, data_reloc_execute, box.BOX_getName()))
                    #### FIN RELOCACIOES ####################################################

        # Cuando este accesible muevo el contenedor al area de servicio
        move_succ, move_cost = yard.YRD_moveBoxToService(box)
        if move_succ:
            yield env.timeout(move_cost)
            print("[{}] Moving {} to service, cost {}".format(env.now, box, move_cost))

def GEN_moveFromService(env, yard, sim_res_Crane, box):
    print("[{}] Box {} is leaving service area".format(env.now, box))
    with sim_res_Crane.request() as i_have_a_crane:
        yield i_have_a_crane
        destiny_block, destiny_bay = yard.YRD_findBoxNewPosition(box)
        move_succ, move_cost = yard.YRD_moveInboundContainer(box, destiny_bay)
        if move_succ:
            print("[" + str(env.now) + "] Crane moving " + str(box.BOX_getName()) + " to " + str(
                destiny_bay) + " at cost " + str(move_cost) + " from service area")
            yield env.timeout(move_cost)
            print("[" + str(env.now) + "] Crane completed movement of " + str(box.BOX_getName()))


def GEN_services (env, yard, sim_res_Crane, sim_res_Service_slot, service):
    '''
    Generator process for an scheduled service. It wil start when the start_time of the service equals the run time,
    it will call for all the boxes en service.container_list to be moved to the container area. Once they are moved the
    service starts for service.service_lenght timesteps. After thar the containers are returned to the yard or removed
    if their removal time is past.
    :param env: the simulation enviroment
    :param yard: the container yard
    :param service: the service to be done
    '''
    print("[{}] SERV: Calendarizado servicio de {} a las {}".format(
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
    #Ask for enought slots in service area
    available_slots = []
    for box in service_boxes:
        available_slots.append(sim_res_Service_slot.request())
        box.in_service = True #Container is flagged as "In Service" so it can not be removed.
    yield simpy.events.AllOf(env, available_slots)
    #Once all slots are secured, proceed to move the containers.
    moves = [
            env.process(GEN_moveToService(env, yard, sim_res_Crane, box))
            for box in service_boxes]
    yield simpy.events.AllOf(env, moves)
    print("[{}] SERV: servicio de {} in position ".format(env.now,service.container_list))
    #Wait until the servive due time
    yield env.timeout(max(0, service.due_time-env.now))
    data_execution_time = env.now
    print("[{}] SER: service of {} starting now".format(env.now, service.container_list))
    yield env.timeout(service.service_lenght)
    data_end_time = env.now
    #After service return containers to yard or remove them if removal time has passed.
    for box in service_boxes:
        if env.now >= box.BOX_getDateOut() > 0:
            remove_succ, remove_cost = yard.YRD_removeBoxFromService(box, env.now)
            box.in_service = False
            if remove_succ:
                print("[{}] Removing {} from service area, costs {}".format(env.now, box, remove_cost))
                sim_res_Service_slot.release(available_slots.pop(0)) #Release the service slot
                DATA_BOX_REMOVALS.append((str(box.BOX_getName()), str(box.BOX_getDateOut()), str(env.now),
                                          str(env.now), str(0)))
                global COUNT_NUMBER_OF_BOXES
                COUNT_NUMBER_OF_BOXES = COUNT_NUMBER_OF_BOXES - 1
                DATA_NUMBER_OF_BOXES.append((str(env.now), COUNT_NUMBER_OF_BOXES))
        else:
            #Call for a move
            yield env.process(GEN_moveFromService(env, yard, sim_res_Crane, box))
            #once move is complete release service slot and flag that box is no longer in service
            box.in_service = False
            sim_res_Service_slot.release(available_slots.pop(0))
    print("[{}] Service of {} is complete".format(env.now, service_boxes))
    DATA_BOX_SERVICE.append((str(service_boxes), str(service.start_time), str(data_execution_time),str(data_end_time)))

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


def export_data(data_string_list, file_name):
    file = open(file_name, "w+")
    for line in data_string_list:
        string_line = ""
        for item in line:
            string_line = string_line + str(item) + ","
        file.write(string_line + "\n")
    file.close()
#################   Ejecutor    ################
if __name__ == '__main__':
    main()
