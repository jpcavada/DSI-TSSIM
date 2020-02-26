# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 16:02:51 2019

@author: jpcavada
"""
import numpy

DEFAULT_BAY_SIZE = 4

COST_TABLE = {
                "C": 1,
                "M": 3,
                "L": 7
            }
CLOSE_DISTANCE_COST = 1
MEDIUM_DISTANCE_COST = 3
LONG_DISTANCE_COST = 7

class Box:
    '''
    A container (or Box) object
    '''
    
    def __init__ (self, name, date_in=None, date_out=None, date_service=None):
        self.name = name
        self.date_in = date_in
        self.date_out = date_out
        self.date_service = date_service
        self.block = None
        self.bay = None
        self.last_bay = None
        self.removalTime = -1
        self.in_service = False
            
    def BOX_getName(self):
        return self.name
    
    def BOX_getDateIn(self):
        return self.date_in
    
    def BOX_getDateOut(self):
        return self.date_out
    
    def BOX_getDateService(self):
        return self.date_service

    def BOX_getPosition(self):
        '''
        Returns the boxs actual block and bay
        :return block, bay
        '''
        return self.block, self.bay

    def BOX_setPosition(self, block, bay):
        '''
        Sets a new position for the box. if no argument is passed the original position is keep.
        
        Parameters:
            block (yard.Block): the block
            bay (yard.Bay): the bay
        '''
        self.block = block
        self.bay = bay
    
    def __repr__(self):
        return self.name
        #return str([self.name, self.getDateIn(), self.position["bay"]])
class Bay:
    '''
    This class defines a container bay. 
    
    That is a stack of containers where only the top one can be removed.
    
    Attributes:
        box_list (list): a list of all the containers in the bay.
        actual_size (int): the number of containers the bay.
        max_size (int) : the max number of containers thar can be stacked in the bay. Default 4.
    '''
   
  
    def __init__ (self,name, max_size=DEFAULT_BAY_SIZE, block=None):
        '''
        Constructs a new bay with no containers.
            
        Parameters:
            box_list (list, optional) : the list of all containers in the bay. Default Empty
            max_size (int, optional) : the maximun number of containers that can be stacket. Default 4.
            block (yard.Block) : the block to witch this bay belongs to.
        '''
        self.box_list = []
        for i in range(max_size):
            self.box_list.append(None)
        self.max_size = max_size
        self.actual_size=0
        self.name = name
        self.block = block


    def BAY_addBox (self, box):
        '''
        Adds a container to the top of the stack.
        
        Adds a containter to the top of the stack only if there if the bay is not at maximun capacity. The box position is NOT UPDATED
        
        Parameters:
            box (container): the container to be added.
        
        Returns: 
            Boolean True if the container was succesfully stacked. False if th bay was full.
        '''
     
        if self.BAY_isFull():
            return False
        else:
            self.box_list[self.actual_size] = box
            self.actual_size = self.actual_size + 1   
            #print("Se agrego " + str(box) + " a la bahia " + str(self.BAY_getName()) + " : " + str(not(self.BAY_isFull())) + " su capacidad es " + str(self.BAY_getSize()) + "//" + str(self.BAY_getMaxSize()))
            return True
        
    def BAY_removeBox (self):
        '''Removes the top container
        
        The box position is NOT UPDATED
        
        Return:
            the top Box object from the stack. If stack is empty, it returns a False value.
        '''
        if self.actual_size > 0 :
            return_box = self.box_list[self.actual_size-1]
            self.box_list[self.actual_size-1] = None
            self.actual_size = self.actual_size - 1
            return return_box
        else:
            return False
        
    def BAY_findBoxIndex(self, box_name):
        '''
        Returns a container position index in the bay.
        
        Returns:
            returns an int with the containers position in the stack. Returns -1 is the container is not found.
        '''

        if self.actual_size == 0:
            return -1
        for index in range(len(self.box_list)):
            if not self.box_list[index] == None:
                if self.box_list[index].BOX_getName() == box_name:
                    return index
        return -1
    
    def BAY_getBox(self, box_index):
        return self.box_list[box_index]
        
    def BAY_getBoxList(self):
        '''
        Returns a list of all the containers in the bay.
        '''
        ret_box_list = []
        for box in self.box_list:
            if not(box == None):
                ret_box_list.append(box)
        return ret_box_list
    
    def BAY_getMaxSize(self):
        '''
        Returns the maximun number of containeres that can be stacked on this bay.
        '''
        return self.max_size
    
    def BAY_getSize(self):
        '''
        Returns the number of containers stacked on this bay.
        '''
        return self.actual_size  
    
    def BAY_isFull(self):
        if self.BAY_getMaxSize() > self.BAY_getSize():
            return False
        return True
    
    def BAY_getName(self):
        return self.name

    def BAY_getBlock(self):
        return self.block

    def __repr__ (self):
        return self.BAY_getName() + ":" + str(self.box_list)
    
class Block:
    
    def __init__(self,block_name):
        '''
        Constructs a new Block.
        
        Constructs a new block of cantainers. Each block must have a name.
        
        Parameters:
            block_name (list): the name of the block.
        Attributes:
            bay_list (list): a list containing all the bays in the block. Default is empty.
        '''
        self.name=block_name
        self.bay_list = []
        self.adjacency_blocking_map = {}
        self.invert_adjacency_blocking_map = {}
    
    def BLK_addBay (self, bay_max_size=DEFAULT_BAY_SIZE, bay_name=None):
        '''
        Creates a new bay in the block
        
        Creates a new bay in the block, if no parameters are given the bay would by empty and hava a maximun size of 4 containers
        
        Parameters:
                bay_box_list (list, optional) : an initial set of containers already in the bay. Defauly empty.
                max_bay_size (int, optional) : the number of containers that can be stacked on the bay. Defualt 4.
                bay_name (string, optional) : the name of the bay for referencias purposes. Default None.
        '''
        newBay = Bay(max_size=bay_max_size,name=bay_name,block=self)

        # Create an empty adyecency map for the bay.

        self.adjacency_blocking_map[bay_name] = []
        self.invert_adjacency_blocking_map[bay_name] = []

        self.bay_list.append(newBay)

    def BLK_getBayList(self):
        '''
        Returns a list of all the bays in the block.
        '''
        return self.bay_list
    
    def BLK_getBay(self, bay_index):
        '''
        Returns the Bay object by bay_index
        '''
        return self.bay_list[bay_index]
    
    def BLK_getBayByName(self, bay_name):
        '''
        Returns the Bay object by bay_name. False if doesn't contain the a bay with that name
        '''
        for bay_iter in self.BLK_getBayList():
            if bay_name == bay_iter.name:
                return bay_iter
        return False
    
    def BLK_getName(self):
        return self.name

    def BLK_addAdjacentBay(self, blocked_bay_name, blocking_bay_name):
        '''
        Add the bay position (high) to the list of positions that block [box] movement.
        :param blocked_bay : the bay being blocked at index
        :param blocking_bay: the bay that may block box
        '''
        self.adjacency_blocking_map[blocked_bay_name].append(self.BLK_getBayByName(blocking_bay_name))
        self.invert_adjacency_blocking_map[blocking_bay_name].append(self.BLK_getBayByName(blocked_bay_name))
        print("Added Adjacency: bay {} is now blocked by bay {}".format(blocked_bay_name, blocking_bay_name))

    def BLK_getBlockingBaysList(self, blocked_bay):
        '''
        Returns a list of all the bays that could block [blocked_bay]
        :param blocked_bay:
        :return: list of all the potentially blocking bays
        '''
        return self.adjacency_blocking_map[blocked_bay.BAY_getName()]

    def BLK_getInvertedBlockingBaysList(self, blocking_bay):
        '''
        Returns a list of all the bays that are blocked by [blocking_bay]
        :param blocking_bay:
        :return: list of all the potentially blocked bays
        '''
        return self.invert_adjacency_blocking_map[blocking_bay.BAY_getName()]

    def __repr__ (self):
        return self.name + " : " + str(self.bay_list)

class ContainerYard:
    '''
    The Container Yards
    
    A container yard is a set of blocks and bays in with containers are stored.
    
    Attributes:
        block_num (int): number of blocks in the yard
        block_list (list) : a list of the blocks in the yard.
        transfer_cost (list,list)
    '''
    
    def __init__ (self, block_num, block_names=None):
        '''
        Creates a new container yard.
        
        Creates a new container yard with a set number of blocks.
        
        Parameters:
            block_num (int) : the number of blocks in the yard
            block_names (list): a list with all the names of the block. If no paremeter is given the blocks will be named numericaly from starting from zero.
        '''
        self.block_list = []
        self.removed_box_list = []
        self.service_list_pending = []
        self.service_list_complete = []
        self.boxes_in_service = []

        for i in range(block_num):
            if block_names==None:
                self.block_list.append(Block(i))
            else:
                self.block_list.append(Block(block_names[i]))

        self.movement_distance = {}

    def YRD_getBlockList(self):
        '''
        :return the list of all the blocks in the Yard
        '''
        return self.block_list

    def YRD_getRemovedBoxList(self):
        '''
        :return the list of all the blocks in the Yard
        '''
        return self.removed_box_list

    def YRD_getBlock(self, index):
        '''
        :return the block using the block index
        '''
        return self.block_list[index]
    
    def YRD_getBlockByName(self, block_name):
        '''
        :return the Block object by block_name. False if doesn't contain the a bay with that name
        '''
        for block_iter in self.block_list:
            if block_name == block_iter.name:
                return block_iter
        return False
    
    def __repr__(self):
       return str(self.block_list)
   
    def YRD_moveInboundContainer(self, box, box_destiny_bay):
        '''
        Moves a new container to a bay, if the destiny doesn't have enough capacity it returns the False.
        
        :param: box (Box): the container box to be moved to the destiny bay.
        :param: box_destiny_bay (Bay): the container's destiny bay.
        :returns: Boolean, int : The first return is True if the bay had enough capacity, the second is an integer with the
             cost of the movement.
        '''
        success_result = True
        movement_cost = 0
        fail_msg= ""
        if self.YRD_isBayBlocked(box_destiny_bay):
            fail_msg = "Bay is Blocked "
            success_result = False
        if box_destiny_bay.BAY_isFull():
            fail_msg = fail_msg + "Bay is Full"
            success_result = False
        if success_result:
            success_result = box_destiny_bay.BAY_addBox(box)
            movement_cost = self.YRD_calculateMovementCost("Inbound", box_destiny_bay)
        if success_result:
            box.BOX_setPosition(box_destiny_bay.BAY_getBlock(),box_destiny_bay)
        else:
            raise Exception("Fallo movimiento: "+str(box)+" a "+str(box_destiny_bay)+" por "+fail_msg)
        return success_result, movement_cost

    def YRD_findBoxByName(self,box_name):
        '''
        returs the box object in the complete yard.

        :param box_name: the container name in string
        :return: the box object with the name, if not found returns False.
        '''
        found_it = False
        for blocks in self.YRD_getBlockList():
            for bays in blocks.BLK_getBayList():
                box_index = bays.BAY_findBoxIndex(box_name)
                if box_index >= 0:
                    found_it = bays.BAY_getBox(box_index)
                    #print("found {} in location {}".format(box_name, found_it.bay))
                    return found_it
        if found_it == False:
            raise Exception ("Failed to found box {}". format(box_name))
        return found_it

    def YRD_findBoxNewPosition(self, box):
        '''
        Function to find a new container position.
        
        returns the block and bay index and name were the new container should be located.
        
        :returns: block, bay : First argument is the destiny block and second return argument is de destiny bay.
        '''

        '''
        #This Code Orders all containers on after the other.
        for block_iter in self.getBlockList():
            for bay_iter in block_iter.getBayList():
                if not bay_iter.isFull():
                    return block_iter, bay_iter
        return None,None
        '''
        #This Code version asigns a random position, if not available it would choose again until it finds a non full bay.
        '''
        need_to_find_location = True
        r_block = None
        r_bay = None
        while need_to_find_location:
            #Choose a random block
            random_block = numpy.random.randint(0, len(self.YRD_getBlockList()))
            random_bay = numpy.random.randint(0, len(self.YRD_getBlock(random_block).BLK_getBayList()))
            r_block = self.YRD_getBlock(random_block)
            r_bay = self.YRD_getBlock(random_block).BLK_getBay(random_bay)
            if not(r_bay.BAY_isFull()) and not(self.YRD_isBayBlocked(r_bay)):
                need_to_find_location = False
            else:
                print("Intento mover {} a {} pero es inaccesible".format(box.BOX_getName(), str(r_bay)))
        '''
        #Here is the version of the code implementing the basic sorting and reposition algorith;
        r_bay = None
        r_block = None

        empty_bay_list = []
        empty_bay_adjacent_no = []
        non_blocking_candidate_bay_list = []
        non_blocking_candidate_bay_top_box_time_difference = []
        blocking_candidate_bay_list = []
        blocking_candidate_bay_top_box_time_difference = []

        for blocks in self.YRD_getBlockList():
            for target_bay in blocks.BLK_getBayList():
                valid_bay = True
                # Si esta llena la bay no es candidata
                if target_bay.BAY_isFull():
                    valid_bay = False
                # Si la bahia esta bloqueada no es opcion.
                if self.YRD_isBayBlocked(target_bay):
                    valid_bay = False
                # Regla de la piramide
                for blocked_bay in blocks.BLK_getInvertedBlockingBaysList(target_bay):
                    if blocked_bay.BAY_getSize() <= target_bay.BAY_getSize():
                        valid_bay = False

                if valid_bay:  # Si tiene contenedores veo si genera un bloqueo o no:
                    if target_bay.BAY_getSize() == 0: #Si esta vacia, la agrego a la lista correspondiente
                        empty_bay_list.append(target_bay)
                        empty_bay_adjacent_no.append(len(blocks.BLK_getBlockingBaysList(target_bay)))

                    else:
                        top_box_date_out = target_bay.BAY_getBox(target_bay.BAY_getSize()-1).BOX_getDateOut()
                        delta_out = top_box_date_out - box.BOX_getDateOut()
                        if 0 < delta_out: #box nuevo sale antes que el top
                            non_blocking_candidate_bay_list.append(target_bay)
                            non_blocking_candidate_bay_top_box_time_difference.append(delta_out)
                        else: #box nuevo sale despues del top
                            blocking_candidate_bay_list.append(target_bay)
                            blocking_candidate_bay_top_box_time_difference.append(delta_out)

        #Eligo en prioridad bahia libre - bahia que no bloquea - bahia que bloquea
        if empty_bay_list:
            max_block_no = 10#0
            incumbent = 0
            for i in range(0,len(empty_bay_list)):
                if empty_bay_adjacent_no[i] < max_block_no: #leq
                    incumbent = i
                    max_block_no = empty_bay_adjacent_no[i]
            r_bay = empty_bay_list[incumbent]
            r_block = empty_bay_list[incumbent].BAY_getBlock()

        elif non_blocking_candidate_bay_list : #elijo la de menor delta
            min_delta = 0
            incumbent = 0
            for i in range(0, len(non_blocking_candidate_bay_list)):
                if non_blocking_candidate_bay_top_box_time_difference[i] < min_delta:
                    incumbent = i
                    min_delta = non_blocking_candidate_bay_top_box_time_difference[i]
            r_bay = non_blocking_candidate_bay_list[incumbent]
            r_block = non_blocking_candidate_bay_list[incumbent].BAY_getBlock()

        elif blocking_candidate_bay_list:  # elijo la de mayor delta
            max_delta = 0
            incumbent = 0
            for i in range(0, len(blocking_candidate_bay_list)):
                if blocking_candidate_bay_top_box_time_difference[i] > max_delta:
                    incumbent = i
                    max_delta = blocking_candidate_bay_top_box_time_difference[i]
            r_bay = blocking_candidate_bay_list[incumbent]
            r_block = blocking_candidate_bay_list[incumbent].BAY_getBlock()

        else:
            raise Exception("No available location for {}".format(box.BOX_getName()))
        return r_block, r_bay

    def YRD_isBoxBlocked(self, box):
        '''
        Finds if box is blocked or not. If box is blocked returns a list of all blocking box IN THE ORDER they need to
        be removed.

        :param box: the box to be removed
        :return: a list of all the blocking boxes in order.
        '''
        list_of_blockers = []
        box_block, box_bay = box.BOX_getPosition()
        list_of_box_in_bay = box_bay.BAY_getBoxList()
        box_index = box_bay.BAY_findBoxIndex(box.BOX_getName())
        #First we check if the container is blocked from the top
        if not(box_index == box_bay.BAY_getSize()-1):
            for box_in_same_bay_on_top in range(box_index+1, box_bay.BAY_getSize()):
                list_of_blockers.append(list_of_box_in_bay[box_in_same_bay_on_top])
        #Then we check if the container is blocked from the sides, for that we check the block adyacency map.
        list_of_side_blocking_bays = box_block.BLK_getBlockingBaysList(box_bay)
        for blocking_bay in list_of_side_blocking_bays:
            if blocking_bay.BAY_getSize() > box_index + 1: ##Criterio para que esté blockeado lateralmente
                n_blocking_box = -box_bay.BAY_findBoxIndex(box.BOX_getName()) + blocking_bay.BAY_getSize() -1
                for side_blocking_box in blocking_bay.BAY_getBoxList()[-n_blocking_box:]:
                    list_of_blockers.append(side_blocking_box)
        return list_of_blockers[::-1]

    def YRD_ReshuffleIndexList(self, new_box, target_bay):
        '''
        Returns a list of the containers that would be time-blockecd if [new_box] is placed a top of [target_bay]. A
        container is considered time-blocked if 1) [new_box] Leaving date is after the leaving date of the container AND
         it physically blocks its retrieval (either because is on top or in a blocking bay).
        :param new_box: the container that would be located
        :param target_bay: the bay where the container would be placed.
        :return: a list of all the bloqued containers.
        '''
        list_of_blocked_boxes = []
        new_box_get_out_date = new_box.BOX_getDateOut()
        new_box_position = target_bay.BAY_getSize()
        for box_in_target_bay in target_bay.BAY_getBoxList():
            if box_in_target_bay.BOX_getDateOut() <= new_box_get_out_date:
                list_of_blocked_boxes.append(box_in_target_bay)
        for bay_blocked_target_bay in target_bay.BAY_getBlock().BLK_getInvertedBlockingBaysList(target_bay):
            for box_in_blocked_bay in bay_blocked_target_bay.BAY_getBoxList():
                if box_in_blocked_bay.BOX_getDateOut() <= new_box_get_out_date:
                    if new_box_position >= bay_blocked_target_bay.BAY_findBoxIndex(box_in_blocked_bay.BOX_getName()):
                        list_of_blocked_boxes.append(box_in_blocked_bay)
        return list_of_blocked_boxes

    def YRD_isBayBlocked(self, bay):
        '''
        Checks if it is possible to add a new box to a bay or if it is blocked by a container
        :param bay: Bay that will be checked
        :return: List of the container that are blocking the access to the bay
        '''
        blocking_bay_list = bay.BAY_getBlock().BLK_getBlockingBaysList(bay)
        blocking_box_list = []
        for blocking_bay in blocking_bay_list:
            if blocking_bay:
                if blocking_bay.BAY_getSize() == 1:
                    return False
                if blocking_bay.BAY_getSize() > bay.BAY_getSize():
                    for box_index in range(bay.BAY_getSize(), blocking_bay.BAY_getSize()):
                        blocking_box_list.append(blocking_bay.BAY_getBoxList()[box_index])
        return blocking_box_list

    def YRD_getBayByName(self, bay_name):
        for block in self.YRD_getBlockList():
            for bay in block.BLK_getBayList():
                if bay.BAY_getName() == bay_name:
                    return bay
        return False

    def YRD_setBayDistance(self, origin_bay, destiny_bay, distance):
        self.movement_distance[(origin_bay, destiny_bay)] = distance

    def YRD_getBayDistance(self, origin_bay, destiny_bay):
        return self.movement_distance[(origin_bay, destiny_bay)]

    def YRD_calculateMovementCost (self, origin, destiny):
        distance = False
        if origin == "Inbound":
            distance = "L"
        elif origin == "Service" or destiny == "Service":
            distance = "L"
        else:
            distance = self.YRD_getBayDistance(origin, destiny)

        return COST_TABLE[distance]

    def YRD_removeBox (self, box, removal_time=0):
        '''
        Removes a container from the yard (sends it to the exit gate) and updates its position The list of all removed
        boxes can be recovered using YRD_getRemovedBoxList(). Returns True if box is removed and the time the crane
        needs to remove the box.

        :param box: the box to be removed
        :returns remove_succ, remove_cost:
        '''
        #reviso si el contenedor es accesible
        blocking_containers = self.YRD_isBoxBlocked(box)
        if blocking_containers == []:
            box_block, box_bay = box.BOX_getPosition()
            self.removed_box_list.append(box_bay.BAY_removeBox())
            box.BOX_setPosition("Removed", "Removed")
            box.last_bay = box_bay
            box.removalTime = removal_time
            remove_cost = 1
            return True, remove_cost
        return False, 0

    def YRD_removeBoxFromService (self, box, removal_time=0):
        '''
        Removes a container from the service area (sends it to the exit gate) and updates its position The list of all removed
        boxes can be recovered using YRD_getRemovedBoxList(). Returns True if box is removed and the time the crane
        needs to remove the box.

        :param box: the box to be removed
        :returns remove_succ, remove_cost:
        '''
        #reviso si el contenedor esta en el area de servicio
        if self.YRD_isBoxInService(box):
            self.removed_box_list.append(box)
            box.BOX_setPosition("Removed", "Removed")
            box.last_bay = "Service"
            box.removalTime = removal_time
            remove_cost = 1
            return True, remove_cost
        return False

    def YRD_addNewIntialBox(self, box, bay_name, block_name):
        block = self.YRD_getBlockByName(block_name)
        if not(block):
            print("Error: block_name {} not found".format(block_name))
            return False

        bay = block.BLK_getBayByName(bay_name)
        if not(bay):
            print("Error: bay name {} not found".format(bay_name))
            return False

        box_added_ok = bay.BAY_addBox(box)
        if box_added_ok:
            box.BOX_setPosition(block, bay)
            print("{} added to bay {}".format(box, bay))
            return True
        print("Error: box {} not added, please check".format(box))

    def YRD_findRelocationPosition(self, box, other_boxes):
        '''
        Returns the most convenient location for a box that is being relocates, using the RI and movementCost as params
        :param box: the container that is being relocated
        :param other_boxes: list of all the other boxes involved in the relocation.
        :return: the bay that is going to be destiny.
        '''
        print("FIND_RELOC_POS: buscando lugar para {}, otros {}".format(box, other_boxes))
        origin_bay = box.bay

        candidate_bay_list = []
        candidate_bay_RI = []
        candidate_bay_cost = []

        #encontramos el minimo index de las boxes involucradas:
        # min_involved_box_index = 999
        # if other_boxes:
        #     involved_box_index = []
        #     for involved_box in other_boxes:
        #         involved_box_block, involved_box_bay = involved_box.BOX_getPosition()
        #         involved_box_index.append(involved_box_bay.BAY_findBoxIndex(involved_box.BOX_getName()))
        #     min_involved_box_index = min(involved_box_index)
        if box.BOX_getName() == "C9-457-4":
            print('stop')
        #self.YRD_printYard(4, 12)
        for target_block in self.YRD_getBlockList():
            for target_bay in target_block.BLK_getBayList():
                valid_bay = True
                bad_valid_bay = False
                if target_bay == origin_bay: #La bahia debe ser distinta
                    valid_bay = False
                    #TAMPOCO PUEDE SER LA BAHIA DE ALGUN INVOLUCRADO!!!! (NO IMPLEMENTADO)
                elif target_bay.BAY_isFull():  # Si esta llena la bay no es candidata
                    valid_bay = False

                elif self.YRD_isBayBlocked(target_bay):  # Si la bahia esta bloqueada no es opcion.
                    valid_bay = False
                    #a menos que el unico que lo bloquee es que se esta moviendo.
              #      if target_bay.BAY_getSize() > 0:
               #         top_box = target_bay.BAY_getBox(target_bay.BAY_getSize()-1).BOX_
                else:
                    target_bay_blocked_bays_list = target_block.BLK_getInvertedBlockingBaysList(target_bay)
                    for blocked_bay in target_bay_blocked_bays_list: #Tampoco si no respeta la regla piramide
                        if target_bay.BAY_getSize() >= blocked_bay.BAY_getSize():
                            valid_bay = False
                            #Pero si no bloquea directamente el movimiento, es una mala movida solamente
                            #if not valid_bay and (origin_bay not in target_bay_blocked_bays_list):
                            #    bad_valid_bay = True


                if valid_bay:
                    candidate_bay_list.append(target_bay)
                    candidate_bay_RI.append(len(self.YRD_ReshuffleIndexList(box, target_bay)))
                    candidate_bay_cost.append(self.YRD_calculateMovementCost(origin_bay, target_bay))
               # elif bad_valid_bay:

        if not candidate_bay_RI:
            self.YRD_printYard(4,12)
        min_RI_bay_index = numpy.argmin(candidate_bay_RI)
        print("Para {} se elegio {} de entre:".format(box, candidate_bay_list[min_RI_bay_index]))
        for i in range(0,len(candidate_bay_list)):
            print(candidate_bay_list[i], candidate_bay_RI[i])
        return candidate_bay_list[min_RI_bay_index]

        if candidate_bay_list == []:
            raise Exception("No position was found for box {}".format(box))
        '''
        #Choose a random bay in the same block that is accesible
        from random import randrange
        choose_again = True
        random_index = 0
        while choose_again:
            random_index = randrange(len(origin_block.BLK_getBayList()))
            temp_destiny_bay = origin_block.BLK_getBay(random_index)
            if not(origin_bay == temp_destiny_bay):
                if not(temp_destiny_bay.BAY_isFull()):
                    if not(self.YRD_isBayBlocked(temp_destiny_bay)):
                        print("FIND_RELOC_POS: Selecionada la {} para mover a box {}".format(temp_destiny_bay, box))
                        return temp_destiny_bay
        '''


    def YRD_relocateBox(self, box, destiny_bay):
        if self.YRD_isBoxBlocked(box):
            raise Exception("Relocating a blocked BOX {}, Check code!!".format(box))
        if self.YRD_isBayBlocked(destiny_bay):
            raise Exception("Relocating BOX {}, to a blocked Bay {} Check code!!".format(box, destiny_bay))
        if destiny_bay.BAY_isFull():
            raise Exception("Relocating BOX {}, to a FULL Bay {} Check code!!".format(box, destiny_bay))
        origin_bay = box.bay
        remove_ok = origin_bay.BAY_removeBox()
        if not(remove_ok):
            raise Exception("BOX {}, could not be removed from bay {} for relocation, Check code!!".format(box, box.bay))
        reloc_succ = destiny_bay.BAY_addBox(box)
        if not(reloc_succ):
            raise Exception("BOX {}, could not be added to bay {} for relocation, Check code!!".format(box, destiny_bay))
        reloc_cost = self.YRD_calculateMovementCost(origin_bay, destiny_bay)
        box.BOX_setPosition(destiny_bay.BAY_getBlock(), destiny_bay)
        return reloc_succ, reloc_cost

    def YRD_printYard(self, wide_number, long_number):
        '''
        Prints tehe current status of the container yard
        :param wide_number:
        :param long_number:
        :return:
        '''
        for block in self.YRD_getBlockList():
            print(block.BLK_getName())
            for i in range(long_number):
                aux_string = ""
                for j in range(wide_number):
                    aux_string = aux_string + str(block.BLK_getBay(i+long_number*j))
                print(aux_string)

##### SERVICIOS: LOGICAL ##############
    def YRD_addNewService(self, containers_list, due_time, service_lenght):
        aux_service = Service(containers_list, due_time, service_lenght)
        self.service_list_pending.append(aux_service)

    def YRD_completeService(self, Servicio):
        self.service_list_pending.remove(Servicio)
        self.service_list_complete.append(Servicio)
        return Servicio.SRV_getLenght()

#### SERVICIOS: FISICAL ##########

    def YRD_moveBoxToService(self, box):
        '''
        Removes a container from its current bay and adds it to the service containers list.
        :param box:
        :return: true/false if succeded, the time requiered to perform the movement.
        '''
        if self.YRD_isBoxBlocked(box):
            raise Exception("BOX {} cant enter Service is blocked , Check code!!".format(box))

        origin_bay = box.bay
        remove_ok = origin_bay.BAY_removeBox()
        if not (remove_ok):
            raise Exception(
                "BOX {}, could not be removed from bay {} for relocation, Check code!!".format(box, box.bay))

        self.boxes_in_service.append(box)
        box.BOX_setPosition("Service", 0)

        return True, self.YRD_calculateMovementCost(origin=origin_bay, destiny="Service")

    def YRD_isBoxInService(self, box):
        '''
        Check if box has a pending service.
        :param box:
        :return: True if box is in service
        '''
        if box.in_service:
                print("{} is in service area".format(box))
                return True
        return False

class Service:
    '''
    A service is a process that need to be performed to the container.
    '''
    def __init__(self, containers_list, start_time, due_time, service_lenght):
        '''
        Constructor of a service object.

        :param containers_list: list of all containers involved in the service.
        :param start_time: the earlist a service can start
        :param due_time: the latest a service can start
        :param service_lenght: the time (en min) that a service requires.
        '''
        self.container_list = containers_list
        self.start_time = start_time
        self.due_time=due_time
        self.service_lenght = service_lenght
        self.service_status = -1


    def SRV_getDueTime(self):
        return self.due_time

    def SRV_getLenght(self):
        return self.service_lenght

    def SRV_getStatus(self):
        return self.service_status

    def SRV_getStatusName(self):
        if self.service_status == 0:
            return "Pending"
        if self.service_status == 1:
            return "In Service Area"
        if self.service_status == 2:
            return "Finished"

    def SRV_setStatus(self, new_status):
        valid_status_list = [0,1,2]
        if new_status not in valid_status_list:
            raise Exception("Status {} not valid, must be {}".format(new_status, valid_status_list))
        self.service_status = new_status
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   