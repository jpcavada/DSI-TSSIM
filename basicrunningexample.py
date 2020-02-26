import yard_class as yard

patio = yard.ContainerYard(2, ["MAR", "COR"])
patio.YRD_getBlock(0).BLK_addBay(bay_name="M.1.1", bay_max_size=4)
patio.YRD_getBlock(0).BLK_addBay(bay_name="M.1.2", bay_max_size=4)
patio.YRD_getBlock(1).BLK_addBay(bay_name="C.1.1", bay_max_size=3)
patio.YRD_getBlock(1).BLK_addBay(bay_name="C.1.2", bay_max_size=3)

patio.block_list[0].BLK_addAdjacentBay("M.1.1", "M.1.2")
patio.block_list[1].BLK_addAdjacentBay("C.1.1", "C.1.2")

# 2 Creamos los 6 contenedores
Box_arrival_list = []
for i in range(12):
    Box_arrival_list.append(yard.Box("B" + str(i + 1), date_in=0))
print(Box_arrival_list)

# Agrego los 2 contenedores al block 1
patio.YRD_moveInboundContainer(Box_arrival_list[0], patio.YRD_getBlock(0).BLK_getBay(0))
patio.YRD_moveInboundContainer(Box_arrival_list[1], patio.YRD_getBlock(0).BLK_getBay(0))
patio.YRD_moveInboundContainer(Box_arrival_list[2], patio.YRD_getBlock(0).BLK_getBay(1))
patio.YRD_moveInboundContainer(Box_arrival_list[3], patio.YRD_getBlock(0).BLK_getBay(1))
patio.YRD_moveInboundContainer(Box_arrival_list[4], patio.YRD_getBlock(0).BLK_getBay(1))
patio.YRD_moveInboundContainer(Box_arrival_list[5], patio.YRD_getBlock(0).BLK_getBay(1))

#Agregamos los otros contenedores al block 2
patio.YRD_moveInboundContainer(Box_arrival_list[6], patio.YRD_getBlock(1).BLK_getBay(0))
patio.YRD_moveInboundContainer(Box_arrival_list[7], patio.YRD_getBlock(1).BLK_getBay(1))
patio.YRD_moveInboundContainer(Box_arrival_list[8], patio.YRD_getBlock(1).BLK_getBay(1))
patio.YRD_moveInboundContainer(Box_arrival_list[9], patio.YRD_getBlock(1).BLK_getBay(1))
patio.YRD_moveInboundContainer(Box_arrival_list[10], patio.YRD_getBlock(1).BLK_getBay(1))
patio.YRD_moveInboundContainer(Box_arrival_list[11], patio.YRD_getBlock(1).BLK_getBay(0))

print(patio)
print("probando bloqueo para salir")
for i in patio.YRD_getBlockList():
    for j in i.BLK_getBayList():
        for k in j.BAY_getBoxList():
            print("bloqueando a "+str(k)+" : " +str(patio.YRD_isBoxBlocked(k)))

print("probando bloque para entrar")
for j in patio.YRD_getBlockList():
    for k in j.BLK_getBayList():
        print("Bloqueando "+str(k) + " : "+str(patio.YRD_isBayBlocked(k)))