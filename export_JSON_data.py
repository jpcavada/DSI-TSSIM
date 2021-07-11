from pathlib import Path
import json


def export_JSON_status(simtime, yard, arrivals, look_ahead_time, path, name, export_positions=True):
    """
    A intervalos regulares exporta el status del patio en un JSON
        :param path:
        :param export_positions:
        :param arrivals:
        :param look_ahead_time:
        :param simtime: simulation enviromnent
        :param yard: patio de contenedores
        :return: nada
    """
    # Listas/Diccionarios temporales
    positions = []
    cont_list = {}  # box_name: [Tc, position, arrival/leave time]
    distancias = {}

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
                    if tmp_cont_date_Out <= simtime + look_ahead_time:
                        tmp_status = 'sale'
                    else:
                        tmp_status = 'fijo'
                    cont_list[tmp_cont_name] = [tmp_cont_date_Out, tmp_pos, tmp_status]
                # Obtener Distancias
                if export_positions:
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
                    if aux_val[2] != 'sale':
                        cont_list[blocking_name] = [aux_val[0], aux_val[1], 'mover']

    # Agregamos los contenedores nuevos
    llegan_cont = {}
    for arr in arrivals:
        if simtime <= arr.BOX_getDateIn() <= simtime + look_ahead_time:
            llegan_cont[arr.BOX_getName()] = [arr.BOX_getDateIn(), arr.BOX_getDateOut()]

    # Export JSON files
    export_json_data = {
        'contenedores': cont_list,
        'cont_llegadas': llegan_cont
    }
    p1 = path / '{}_contenedores.json'.format(name)
    with open(p1, mode='w+') as outfile:
        json.dump(export_json_data, outfile, indent=4)

    if export_positions:
        export_data_pos = {
            'posiciones': positions,
            'distancias': distancias
        }
        p2 = path / '{}_posiciones.json'.format(name)
        with open(p2, mode='w+') as outfile:
            json.dump(export_data_pos, outfile, indent=4)
