# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 15:19:42 2019

@author: Juampi
Este archivo prueba la clase container yard.

1° Crea un patio con 2 bloques (MAR y COR) y 4 Bahias cada uno

MAR
M.1.1 M.1.2
M.2.1 M.2.2


COR
C.1.1 C.1.2
C.2.1 C.2.2

2° Crea 12 contenedores: "B1...B12" (solo tienen nombre).
3° Los posiciona por orden de llegada en las bahias, si una esta llena, entonces usa la siguiente, si un bloque esta lleno entonces se mueve al siguiente.

"""

import yard_class as yard

def main():
    #1° Creamos la yard
    patio = yard.ContainerYard(2,["MAR","COR"])
    patio.YRD_getBlock(0).BLK_addBay(bay_name="M.1.1", bay_max_size = 2)
    patio.YRD_getBlock(0).BLK_addBay(bay_name="M.1.2", bay_max_size = 2)
    patio.YRD_getBlock(0).BLK_addBay(bay_name="M.2.1", bay_max_size = 2)
    patio.YRD_getBlock(0).BLK_addBay(bay_name="M.2.2", bay_max_size = 2)
    patio.YRD_getBlock(1).BLK_addBay(bay_name="C.1.1", bay_max_size = 2)
    patio.YRD_getBlock(1).BLK_addBay(bay_name="C.1.2", bay_max_size = 2)
    patio.YRD_getBlock(1).BLK_addBay(bay_name="C.2.1", bay_max_size = 2)
    patio.YRD_getBlock(1).BLK_addBay(bay_name="C.2.2", bay_max_size = 2)
    
    print(patio)
    #2 Creamos los 12 contenedores
    Box_arrival_list = []
    for i in range(12):
        Box_arrival_list.append(yard.Box("B"+str(i+1)))
    print(Box_arrival_list)

#    #3 Agregamos todos los contenedores al terminal
    for cont in Box_arrival_list:
        bl,ba = patio.YRD_findBoxNewPosition(cont)
        print(str(cont) +" asignado a " + str(bl.BOX_getName()) + " " + str(ba.BOX_getName()))
        print("Capacidad de " + ba.BOX_getName() + " es " + str(ba.BAY_getSize()))
        print(patio.YRD_moveInboundContainer(cont, ba))
        print(patio)

if __name__ ==  '__main__':
    main()
    