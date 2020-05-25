'''
Este ejemplo copnstruye SIMULA la lleada de 12 containers a un patio con 2 block de 4 bay cada uno

'''

import yard_class as yard
import numpy
import simpy

START_SIM_CLOCK = 0
FINAL_SIM_CLOCK = 120

CRANES_NUM = 1



def main():
    # 1° Creamos la yard
    patio = yard.ContainerYard(2, ["MAR", "COR"])
    patio.YRD_getBlock(0).BLK_addBay(bay_name="M.1.1", bay_max_size=2)
    patio.YRD_getBlock(0).BLK_addBay(bay_name="M.1.2", bay_max_size=2)
    patio.YRD_getBlock(0).BLK_addBay(bay_name="M.2.1", bay_max_size=2)
    patio.YRD_getBlock(0).BLK_addBay(bay_name="M.2.2", bay_max_size=2)
    patio.YRD_getBlock(1).BLK_addBay(bay_name="C.1.1", bay_max_size=2)
    patio.YRD_getBlock(1).BLK_addBay(bay_name="C.1.2", bay_max_size=2)
    patio.YRD_getBlock(1).BLK_addBay(bay_name="C.2.1", bay_max_size=0)
    patio.YRD_getBlock(1).BLK_addBay(bay_name="C.2.2", bay_max_size=0)

    print(patio)
    # 2 Creamos los 12 contenedores
    Box_arrival_list = []
    for i in range(12):
        new_box_hora_llegada = numpy.random.randint(START_SIM_CLOCK, FINAL_SIM_CLOCK)
        Box_arrival_list.append(yard.Box("B" + str(i + 1),date_in = new_box_hora_llegada))
    print(Box_arrival_list)

    #Elementos de la simulacion

    sim_enviroment = simpy.Environment()                        #CREA EL ENVIROMENT
    sim_res_CRANES = simpy.Resource(sim_enviroment,CRANES_NUM)  #AGREGA LOS RECURSOS GRUA AL ENV

    #PROCESOS DE LA SIMULACION
    #Calendarizamos todas las llegadas
    for arrival in Box_arrival_list:
        sim_enviroment.process(gen_Movements(sim_enviroment,patio,arrival,sim_res_CRANES))

    sim_enviroment.run(until=FINAL_SIM_CLOCK)

    for boxes in Box_arrival_list:
        print(boxes, boxes.BOX_getPosition())


def gen_Movements (env, patio, box,sim_res) :
#    Para todos los box se encola el momento de su llegada.
    time_in = box.BOX_getDateIn()
    time_out = box.BOX_getDateOut()
    print("[" + str(env.now) +"] Se espera que " + str(box.BOX_getName()) + " llegue a las " + str(box.BOX_getDateIn()))
    yield env.timeout(box.BOX_getDateIn() - env.now)
    #Cuando llega, se le busca lugar y luego se muevo
    print("[" + str(env.now) +"] Llego " + str(box.BOX_getName()) + " y esta esperando grúa")
    with sim_res.request() as i_have_a_crane:
        yield i_have_a_crane
        destiny_block, destiny_bay = patio.YRD_findBoxNewPosition(box)
        move_succ, move_cost = patio.YRD_moveInboundContainer(box, destiny_bay)
        if move_succ :
            print("[" + str(env.now) +"] Grua moviendo a " + str(box.BOX_getName()) + " a " + str(destiny_bay) + " por " + str(move_cost) + " min")
        yield env.timeout(move_cost)
        print("[" + str(env.now) +"] Grua finaliza movimiento de " + str(box.BOX_getName()))

if __name__ == '__main__':
    main()