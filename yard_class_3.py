# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 16:02:51 2019

@author: jpcavada
"""
import numpy

import logging

logger = logging.getLogger("sim_log")

#logging.basicConfig(level=logging.INFO, format='%(message)s')
#logger = logging.getLogger('sim_log')
#print = logger.info


DEFAULT_BAY_SIZE = 4

COST_TABLE = {
                "I" : 0,
                "C": 1,
                "M": 3,
                "L": 7
            }
#CLOSE_DISTANCE_COST = 1
#MEDIUM_DISTANCE_COST = 3
#LONG_DISTANCE_COST = 7

RELOCATION_CRITERIA = "mising_relocation_criteria"
ALL_DECISIONS = False

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

    def Bay_getFirstRetrieval(self):
        '''
        Returns the box and time of the box with the lowest retrieval time, either to leave or to service
        :return: box, retrieval_time
        '''
        if self.BAY_getSize() == 0:
            return None, 99999999
        else:
            aux_leaving_dates = []
            for box in self.BAY_getBoxList():
                if box is not None:
                    leave_time = None
                    if box.BOX_getDateService() == None:
                        aux_leaving_dates.append(box.BOX_getDateOut())
                    else:
                        aux_leaving_dates.append(min(box.BOX_getDateOut(), box.BOX_getDateService()))

            pos_min = numpy.argmin(aux_leaving_dates)

            return self.BAY_getBoxList()[pos_min], aux_leaving_dates[pos_min]

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
        logger.info("Added Adjacency: bay {} is now blocked by bay {}".format(blocked_bay_name, blocking_bay_name))

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

    def BLK_export_adjacency_map(self):
        print(self.adjacency_blocking_map)
        print(self.invert_adjacency_blocking_map)

class ContainerYard:
    '''
    The Container Yards
    
    A container yard is a set of blocks and bays in with containers are stored.
    
    Attributes:
        block_num (int): number of blocks in the yard
        block_list (list) : a list of the blocks in the yard.
        transfer_cost (list,list)
    '''

    def __init__ (self, block_num, block_names=None, relocation_criteria=RELOCATION_CRITERIA):
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
        global RELOCATION_CRITERIA
        RELOCATION_CRITERIA = relocation_criteria

        for i in range(block_num):
            if block_names==None:
                self.block_list.append(Block(i))
            else:
                self.block_list.append(Block(block_names[i]))

        self.movement_distance = {}

    def setRelocationCriteria(self, relocation_criteria):
        global RELOCATION_CRITERIA
        RELOCATION_CRITERIA = relocation_criteria

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

    def YRD_BoxAllocation(self, box, criteria="RELOCATION_CRITERIA"):
        '''
        Function to find a new container position.Returns the block and bay index and name were the new container should
        be located.

        :returns: block, bay : First argument is the destiny block and second return argument is de destiny bay.
        '''
        r_bay = False
        r_block = False

        origin_bay = box.bay
        logger.info("Buscando lugar para {}".format(box))
        # 1) Find all accesible Bays
        accessible_bay_list = self.YRD_findAccessileBays(box)
        # 2) Call for the new position evaluation rule
        selected_bay, other_selected_bays, decision_string = self.YRD_evaluateBoxNewBay(box, accessible_bay_list,
                                                                                        RELOCATION_CRITERIA, ALL_DECISIONS)

        return selected_bay.BAY_getBlock(), selected_bay, decision_string

    def DEP_YRD_findBoxNewPosition(self, box): #TODO esta función de nuevo
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
                logger.info("Intento mover {} a {} pero es inaccesible".format(box.BOX_getName(), str(r_bay)))
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
            self.YRD_printYard(4, 12)
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
            if blocking_bay.BAY_getSize() > 1:
                if blocking_bay.BAY_getSize() >= box_index + 1: ##Criterio para que esté blockeado lateralmente
                    n_blocking_box = -box_bay.BAY_findBoxIndex(box.BOX_getName()) + blocking_bay.BAY_getSize()
                    for side_blocking_box in blocking_bay.BAY_getBoxList()[-n_blocking_box:]:
                        list_of_blockers.append(side_blocking_box)
        return list_of_blockers[::-1]

    def DEP_YRD_ReshuffleIndexList(self, new_box, target_bay):
        '''
        Returns a list of the containers that would be time-blocked if [new_box] is placed a top of [target_bay]. A
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
            distance = "I"
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
        return False, blocking_containers

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
            logger.info("Error: block_name {} not found".format(block_name))
            return False

        bay = block.BLK_getBayByName(bay_name)
        if not(bay):
            logger.info("Error: bay name {} not found".format(bay_name))
            return False

        box_added_ok = bay.BAY_addBox(box)
        if box_added_ok:
            box.BOX_setPosition(block, bay)
            logger.info("{} added to bay {}".format(box, bay))
            return True

        raise Exception("Error: box {} not added, please check".format(box))

    def YRD_findAccessileBays(self, box, other_boxes=None):
        '''
        Finds all accessible bays for (re)locating box. This checks for non-full bays that can be accessed from a crane.
        It also discards all bays where other_boxes are located, as they may be needed to be accessed in future
        relocations. Note this method enforces the pyramid rule when neceserary. But will disable it if no other options
        are available.

        :param box: the container box that will be allocated
        :param other_boxes: other container boxes involved in the same movement (default [])
        :return: the list of all accessible bays.
        '''
        #Declarations and safe default value for empty other_boxes.
        if other_boxes is None: other_boxes = []
        accessible_bay_list = []
        barely_accessible_list = []  # List of accessible bays that do not comply with piramid rule.
        rejection_list = []
        if other_boxes:
            lowest_box_name = other_boxes[numpy.argmin([i.bay.BAY_findBoxIndex(i.BOX_getName()) for i in other_boxes])]
            lowest_box_index = numpy.min([i.bay.BAY_findBoxIndex(i.BOX_getName()) for i in other_boxes])
            #print("lowest box is {} at index {}".format(lowest_box_index, lowest_box_index))
        else:
            lowest_box_index = 99
            #print("No other boxes")

        # Find all accessible bays
        for target_block in self.YRD_getBlockList():
            for target_bay in target_block.BLK_getBayList():  # Recorremos todas las bahias del patio.
                valid_bay = True
                rejection_reason = "{} Not Accessible because: ".format(target_bay)
                #   0) Check if target_bay is not full
                if target_bay.BAY_isFull():
                    valid_bay = False
                    rejection_reason = rejection_reason + "Full "

                #   1) Check if Bay is accessible (block_list is empty). If it is blocked, check if only blocking box is
                #   the box that is moving.
                boxes_blocking_target_bay = self.YRD_isBayBlocked(target_bay)
                if boxes_blocking_target_bay:
                    if boxes_blocking_target_bay[0] == box and boxes_blocking_target_bay[-1] == box:
                        logger.info("bay {} is not accessible, it will be available after {} is removed".format(target_bay, box))
                    else:
                        #print("bay {} is not accessible, is blocked by {}".format(target_bay, boxes_blocking_target_bay))
                        valid_bay = False
                        rejection_reason = rejection_reason + "Blocked by {} ".format(boxes_blocking_target_bay)
                #   2) Check if the target bay is not the same bay of the moving box.
                if target_bay == box.bay:
                    valid_bay = False
                    rejection_reason = rejection_reason + "Same Bay "
                #   3) Check if target bay is not the same bay of other boxes that would be moved in this relocation.
                for b in other_boxes:
                    if b.bay == target_bay:
                        valid_bay = False
                        #print("bay {} is the bay of {}".format(target_bay, b))
                        rejection_reason = rejection_reason + "Same bay as {} ".format(b)
                    # 3b) Check if target bay would block the access to other boxes
                    elif b.bay in target_block.BLK_getInvertedBlockingBaysList(target_bay):
                        if lowest_box_index == 0 and target_bay.BAY_getSize() < 0:
                            valid_bay = False
                            rejection_reason = rejection_reason + "Will block other {} ".format(lowest_box_name)
                        elif lowest_box_index <= target_bay.BAY_getSize():
                            valid_bay = False
                            rejection_reason = rejection_reason + "Will block other {} ".format(lowest_box_name)

                #   4)  Check if target_bay complies with PIRAMID RULE. If it does not, it will me assigned to the
                #       Alternative accessible list
                if target_bay.BAY_getSize() > 0: #Bays de tamaño 1 nunca bloquean.
                    target_bay_blocked_bays_list = target_block.BLK_getInvertedBlockingBaysList(target_bay)
                    for blocked_bay in target_bay_blocked_bays_list:
                        future_size_of_target_bay = target_bay.BAY_getSize() + 1
                        # Box comes from the a blocked bay
                        if blocked_bay == box.bay and future_size_of_target_bay > blocked_bay.BAY_getSize() - 1:
                            if valid_bay:
                                barely_accessible_list.append(target_bay)
                                valid_bay = False
                                rejection_reason = rejection_reason + "Pyramid (side bay)"
                        # Box come from another place
                        elif future_size_of_target_bay > blocked_bay.BAY_getSize():
                            if valid_bay:
                                barely_accessible_list.append(target_bay)
                                valid_bay = False
                                rejection_reason = rejection_reason + "Pyramid "

                # If target_bay does not check any flag is accessible.
                if valid_bay:
                    accessible_bay_list.append(target_bay)
                else:
                    rejection_list.append(rejection_reason)

        if not accessible_bay_list and barely_accessible_list:
            logger.error("No good relocaction bays, disabling pyramid rule")
            accessible_bay_list = barely_accessible_list
        #elif not accessible_bay_list:
        #    for i in rejection_list: logger.error(i)
        #    #self.YRD_printYard(4,12)
         #   raise Exception("No accessible bays available")
        elif not accessible_bay_list and not barely_accessible_list:
            raise Exception("There are not accessible bays for (re)locating {}".format(box))

        return accessible_bay_list

    def YRD_findRelocationPosition(self, box, other_boxes):
        '''
        Returns the most convenient location for a box that is being relocated.
        :param box: the container that is being relocated
        :param other_boxes: list of all the other boxes involved in the relocation.
        :return: the bay that is going to be destiny.
        '''

        origin_bay = box.bay
        logger.info("FIND_RELOC_POS: buscando lugar para {} desde {}, otros {}".format(box,origin_bay, other_boxes))

        # 1) Find all accesible Bays
        accessible_bay_list = self.YRD_findAccessileBays(box, other_boxes)

        # 2)

        # 2) Call for the new position evaluation rule
        selected_bay, other_selected_bays, decision_string = self.YRD_evaluateBoxNewBay(box, accessible_bay_list,
                                                                                        RELOCATION_CRITERIA,
                                                                                        ALL_DECISIONS)


        return selected_bay, decision_string


    def YRD_evaluateBoxNewBay(self, box, accessible_bays, criteria, alldecisions=False):
        '''
        Find witch bay is the best new position for box among the list of candidate bays accordding to criteria (RI,
        RIL, Min-Max) returns a list of all bays that are good choices.
        :param box:
        :param accessible_bays:
        :param criteria:
        :return choosen_bay, all_candidate_bays:
        '''

        accepted_criteria_list = ["ALL", "RI", "RI-C", "RI-S", "RIL", "RIL-C", "RIL-S", "MM", "MM-S"]
        box_get_out_date = box.BOX_getDateOut()

        #   Return Variables forward declaraion
        selected_bay = None
        all_selected_bays = None
        return_selected_bay = None

        #list with all decisions (
        if isinstance(box.bay, str):
            decisions_string = str(box) + ";" + box.bay
        else:
            decisions_string = str(box) + ";" + str(box.bay.BAY_getName())

        #   Check if criteria corrsponds to an implemented one.
        if criteria not in accepted_criteria_list:
            raise Exception("Wrong criteria {}, must be on of {}".format(criteria, accepted_criteria_list))

        if criteria in ["ALL", "RI", "RI-C", "RI-S", "RIL", "RIL-C", "RIL-S", "MM", "MM-S"]:

            #   Calculate the reshuffle index (number of blocked containers) for each accessible bay
            rs_list = [] #a list for all the reshuffle index, populated in the same order that accessible bays.
            rs_earliest_leaving_time = [] #list with the earliest leave time for each candidate bays

            for bay_s in accessible_bays:
                boxes_blocked_by_box_if_moved_to_bay_s = [] #Initialize B_{cs}^{-1}=\phi
                for boxes in bay_s.BAY_getBoxList():
                    if boxes.BOX_getDateOut() <= box_get_out_date:
                        boxes_blocked_by_box_if_moved_to_bay_s.append(boxes)
                for bay_blocked_by_bay_s in bay_s.BAY_getBlock().BLK_getInvertedBlockingBaysList(bay_s):
                    if bay_blocked_by_bay_s.BAY_getSize() > 1:
                        for box_in_blocked_bay in bay_blocked_by_bay_s.BAY_getBoxList():
                            if box_in_blocked_bay.BOX_getDateOut() <= box_get_out_date:
                                if bay_s.BAY_getSize() >= bay_blocked_by_bay_s.BAY_findBoxIndex(box_in_blocked_bay.BOX_getName()):
                                    boxes_blocked_by_box_if_moved_to_bay_s.append(box_in_blocked_bay)
                rs_list.append(len(boxes_blocked_by_box_if_moved_to_bay_s))
                #print(boxes_blocked_by_box_if_moved_to_bay_s)
                leave_time_aux = []
                for i in boxes_blocked_by_box_if_moved_to_bay_s:
                    leave_time_aux.append(i.BOX_getDateOut())
                #print(leave_time_aux)
                if leave_time_aux:
                    rs_earliest_leaving_time.append([boxes_blocked_by_box_if_moved_to_bay_s[numpy.argmin(leave_time_aux)],
                                                    numpy.min(leave_time_aux)])
                else:
                    rs_earliest_leaving_time.append([0,0])

            '''
            ### DEBUG RELOCATION 1###
            logger.debug("ACCESSIBLE BAYS \t NUMBER OF BLOCKS")
            for i in range(len(accessible_bays)):
                logger.debug("{} \t {}".format(accessible_bays[i], rs_list[i]))
            ### END DEBUG RELOCATION 1 #####
            '''
            if criteria in ["RI", "RIL", "MM", "ALL"] or alldecisions is True:
                #   First create a candidate list with all stacks with the minimun number of future relocarions.
                min_rs = numpy.min(rs_list)
                candidate_list = []     #Lista de todos las BAY con menos bloqueos futuros
                candidate_first_leaving_time_list = []  #Hora de salida de la primera box en salir de la bays
                candidate_first_leaving_box_list = []   #Primera BOX en salir.
                candidate_list_stack_size = []      #Stack size of each candidate bay
                for it in range(len(accessible_bays)):
                    if rs_list[it] == min_rs:
                        candidate_list.append(accessible_bays[it])
                        candidate_first_leaving_time_list.append(rs_earliest_leaving_time[it][1])
                        candidate_first_leaving_box_list.append(rs_earliest_leaving_time[it][0])
                        candidate_list_stack_size.append((accessible_bays[it].BAY_getSize()))
                '''
                #### DEBUG RELOCATION 2 ####
                logger.debug("CANDIDATE BAYS \t FIRST BOX LEAVING \t EARLIST LEAVE TIME")
                for i in range(len(candidate_list)):
                    logger.debug("{}\t{}\t{}".format(candidate_list[i],
                                              candidate_first_leaving_time_list[i],
                                              candidate_first_leaving_box_list[i]))
                ### END DEBUG RELOCATION 2 ####
                '''
                if criteria in ["RI"] or alldecisions is True:
                    #Buscamos todas las de stack size
                    min_stack_size = numpy.min(candidate_list_stack_size)
                    min_stack_candidate_list = []
                    for j in candidate_list:
                        if j.BAY_getSize() == min_stack_size:
                            min_stack_candidate_list.append(j)

                    selected_bay = min_stack_candidate_list[0]
                    all_selected_bays = min_stack_candidate_list

                    logger.info("RI choosed {} [{}], Other options are {}".format(selected_bay, min_rs, all_selected_bays))
                    decisions_string = decisions_string + ";" + "RI:" + str(selected_bay.BAY_getName())
                    if criteria in ["RI"]:
                        return_selected_bay = selected_bay

                if criteria in ["RIL"] or alldecisions is True:
                    #Elegimos la que tiene el mayor tiempo de salida
                    selected_bay= candidate_list[numpy.argmax(candidate_first_leaving_time_list)]
                    all_selected_bays = candidate_list

                    logger.info("RIL would choose {}, [{}], Other options are {}".format(selected_bay, min_rs, all_selected_bays))
                    decisions_string = decisions_string + ";" + "RIL:" + str(selected_bay.BAY_getName())
                    if criteria in ["RIL"]:
                        return_selected_bay = selected_bay

                if criteria in ["MM"] or alldecisions is True:
                    bays_with_no_relocation_list_leavetime = []
                    bays_with_relocations_list_leavetime = []
                    for it in range(len(accessible_bays)):
                        earliest_box, earliest_time = accessible_bays[it].Bay_getFirstRetrieval()
                        if rs_list[it] == 0:
                           bays_with_no_relocation_list_leavetime.append([earliest_time, accessible_bays[it], earliest_box])
                        else:
                            bays_with_relocations_list_leavetime.append([earliest_time, accessible_bays[it], earliest_box])

                    # Si existen bay sin relocacioes, entonces tomamos la que salga antes:

                    if bays_with_no_relocation_list_leavetime:
                        #### DEBUG MM ###
                        #print("Bays with no relocation")
                        #for a in bays_with_no_relocation_list_leavetime:
                        #    print(a)

                        selected_bay = bays_with_no_relocation_list_leavetime[numpy.argmin([i[0] for i in bays_with_no_relocation_list_leavetime])][1]
                        all_selected_bays = bays_with_no_relocation_list_leavetime
                        logger.info("MM would choose {} (No future relocations)".format(selected_bay))

                    elif bays_with_relocations_list_leavetime:
                        #print("No bays without relocations available")
                        #for a in bays_with_relocations_list_leavetime:
                        #    print(a)
                        selected_bay = bays_with_relocations_list_leavetime[numpy.argmax([i[0] for i in bays_with_relocations_list_leavetime])][1]
                        all_selected_bays = bays_with_relocations_list_leavetime
                        logger.info("MM would choose {} (With future relocations)".format(selected_bay))
                    decisions_string = decisions_string + ";" + "MM:" + str(selected_bay.BAY_getName())
                    if criteria in ["MM"]:
                        return_selected_bay = selected_bay


            #Criterias with additive movement cost:
            if criteria in ["RI-C", "RIL-C"] or alldecisions is True:
                # First we create a cost candidate list for each accesible bay. cost = movement + relocations
                additive_cost_list = []
                for it in range(len(accessible_bays)):
                    additive_cost_list.append(rs_list[it] + self.YRD_calculateMovementCost(box.bay, accessible_bays[it]))
                # Create a candidate list with only the minumin cost options
                min_cost_rs = numpy.min(additive_cost_list)
                cost_candidate_list = []  # Lista de todos las BAY con menor costo + relocaciones
                cost_candidate_first_leaving_time_list = []  # Hora de salida de la primera box en salir de la bays
                cost_candidate_first_leaving_box_list = []  # Primera BOX en salir.
                cost_candidate_list_stack_size = []  # Stack size of each candidate bay
                for it in range(len(accessible_bays)):
                    if additive_cost_list[it] == min_cost_rs:
                        cost_candidate_list.append(accessible_bays[it])
                        cost_candidate_first_leaving_time_list.append(rs_earliest_leaving_time[it][1])
                        cost_candidate_first_leaving_box_list.append(rs_earliest_leaving_time[it][0])
                        cost_candidate_list_stack_size.append((accessible_bays[it].BAY_getSize()))

                if criteria in ["RI-C"] or alldecisions is True:
                    min_stack_size = numpy.min(cost_candidate_list_stack_size)
                    min_stack_candidate_list = []
                    for j in cost_candidate_list:
                        if j.BAY_getSize() == min_stack_size:
                            min_stack_candidate_list.append(j)

                    selected_bay = min_stack_candidate_list[0]
                    all_selected_bays = min_stack_candidate_list

                    logger.info("RI-C choosed {} [{}-{}], Other options are {}".format(selected_bay,
                                                                                        self.YRD_calculateMovementCost(
                                                                                            box.bay, selected_bay),
                                                                                        min_cost_rs,
                                                                                        all_selected_bays))
                    decisions_string = decisions_string + ";" + "RIC:" + str(selected_bay.BAY_getName())
                    if criteria in ["RI-C"]:
                        return_selected_bay = selected_bay

                if criteria in ["RIL-C"] or alldecisions is True:
                    # Elegimos la que tiene el mayor tiempo de salida desde la lista con costos
                    selected_bay = cost_candidate_list[numpy.argmax(cost_candidate_first_leaving_time_list)]
                    all_selected_bays = cost_candidate_list

                    logger.info("RIL-C would choose {}, [{}-{}], Other options are {}".format(selected_bay, self.YRD_calculateMovementCost(box.bay, selected_bay), min_cost_rs,
                                                                                         all_selected_bays))
                    decisions_string = decisions_string + ";" + "RIL-C:" + str(selected_bay.BAY_getName())
                    if criteria in ["RIL-C"]:
                        return_selected_bay = selected_bay

            ## CRITERIA WITH STAGGERED COSTS
            if criteria in ["RI-S", "RIL-S", "MM-S"] or alldecisions is True:
                # Create Staggered accessible bay list. [(cost, list_of_bays)]
                staggered_accessible_bay_index_list = []

                for cost_id in COST_TABLE.keys():
                    staggered_accessible_bay_index_list.append((COST_TABLE[cost_id], []))
                for it in range(len(accessible_bays)):
                    acc_bay_cost = self.YRD_calculateMovementCost(box.bay, accessible_bays[it])
                    for i in staggered_accessible_bay_index_list:
                        if i[0] == acc_bay_cost:
                            i[1].append(it)

                #print("For {} in {}".format(box, box.bay))
                #for i in staggered_accessible_bay_index_list:
                #    print(i[0], [accessible_bays[j] for j in i[1]])

                # create a candidate list using the lowest available tier only
                staggered_lower_tier_accessible_index_list = []
                for i in staggered_accessible_bay_index_list:
                    if len(i[1]) != 0:
                        staggered_lower_tier_accessible_index_list = i[1]
                        break
                #print([accessible_bays[j] for j in staggered_lower_tier_accessible_index_list])

                #   Now create a candidate list with all stacks with the minimun number of future relocarions.
                staggered_min_rs = numpy.min([rs_list[j] for j in staggered_lower_tier_accessible_index_list])
                #print("Lowest rs is {}".format(staggered_min_rs))

                staggered_candidate_list = []  # Lista de todos las BAY con menos bloqueos futuros en el menor tier
                staggered_candidate_first_leaving_time_list = []  # Hora de salida de la primera box en salir de la bays
                staggered_candidate_first_leaving_box_list = []  # Primera BOX en salir.
                staggered_candidate_list_stack_size = []  # Stack size of each candidate bay
                for jt in staggered_lower_tier_accessible_index_list:
                    if rs_list[jt] == staggered_min_rs:
                        staggered_candidate_list.append(accessible_bays[jt])
                        staggered_candidate_first_leaving_time_list.append(rs_earliest_leaving_time[jt][1])
                        staggered_candidate_first_leaving_box_list.append(rs_earliest_leaving_time[jt][0])
                        staggered_candidate_list_stack_size.append((accessible_bays[jt].BAY_getSize()))

                if criteria in ["RI-S"] or alldecisions is True:
                    min_stack_size = numpy.min(staggered_candidate_list_stack_size)
                    min_stack_candidate_list = []
                    for j in staggered_candidate_list:
                        if j.BAY_getSize() == min_stack_size:
                            min_stack_candidate_list.append(j)

                    selected_bay = min_stack_candidate_list[0]
                    all_selected_bays = min_stack_candidate_list

                    logger.info("RI-S choosed {} [{}], Other options are {}".format(selected_bay,
                                                                                       self.YRD_calculateMovementCost(
                                                                                           box.bay, selected_bay),
                                                                                       all_selected_bays))
                    decisions_string = decisions_string + ";" + "RI-S:" + str(selected_bay.BAY_getName())
                    if criteria in ["RI-S"]:
                        return_selected_bay = selected_bay

                if criteria in ["RIL-S"] or alldecisions is True:
                    # Elegimos la que tiene el mayor tiempo de salida desde la lista con costos
                    selected_bay = staggered_candidate_list[numpy.argmax(staggered_candidate_first_leaving_time_list)]
                    all_selected_bays = staggered_candidate_list

                    logger.info("RIL-S would choose {}, [{}], Other options are {}".format(selected_bay, self.YRD_calculateMovementCost(box.bay, selected_bay),
                                                                                         all_selected_bays))
                    decisions_string = decisions_string + ";" + "RIL-S:" + str(selected_bay.BAY_getName())
                    if criteria in ["RIL-S"]:
                        return_selected_bay = selected_bay

                if criteria in ["MM-S"] or alldecisions is True:
                    bays_with_no_relocation_list_leavetime = []
                    bays_with_relocations_list_leavetime = []
                    for it in staggered_lower_tier_accessible_index_list:
                        earliest_box, earliest_time = accessible_bays[it].Bay_getFirstRetrieval()
                        if rs_list[it] == 0:
                            bays_with_no_relocation_list_leavetime.append(
                                [earliest_time, accessible_bays[it], earliest_box])
                        else:
                            bays_with_relocations_list_leavetime.append(
                                [earliest_time, accessible_bays[it], earliest_box])

                    # Si existen bay sin relocacioes, entonces tomamos la que salga antes:

                    if bays_with_no_relocation_list_leavetime:
                        #### DEBUG MM ###
                        #print("Bays with no relocation")
                        #for a in bays_with_no_relocation_list_leavetime:
                        #    print(a)

                        selected_bay = bays_with_no_relocation_list_leavetime[
                            numpy.argmin([i[0] for i in bays_with_no_relocation_list_leavetime])][1]
                        all_selected_bays = bays_with_no_relocation_list_leavetime
                        logger.info("MM-S would choose {} (No future relocations)".format(selected_bay))

                    elif bays_with_relocations_list_leavetime:
                        # print("No bays without relocations available")
                        # for a in bays_with_relocations_list_leavetime:
                        #    print(a)
                        selected_bay = bays_with_relocations_list_leavetime[
                            numpy.argmax([i[0] for i in bays_with_relocations_list_leavetime])][1]
                        all_selected_bays = bays_with_relocations_list_leavetime
                        logger.info("MM-S would choose {} (With future relocations)".format(selected_bay))
                    decisions_string = decisions_string + ";" + "MM-S:" + str(selected_bay.BAY_getName())
                    if criteria in ["MM-S"]:
                        return_selected_bay = selected_bay

        #RETURN choosen bay and all other candidate bays.
        decisions_string = decisions_string + ";" + "F:" + str(criteria) +":" + str(return_selected_bay)
        logger.info("Choosed BAY {} using {}".format(selected_bay, criteria))
        return return_selected_bay, all_selected_bays, decisions_string

    def YRD_relocateBox(self, box, destiny_bay):
        if self.YRD_isBoxBlocked(box):
            raise Exception("Relocating a blocked BOX {}, Check code!!".format(box))
        boxes_blocking_target_bay = self.YRD_isBayBlocked(destiny_bay)
        if self.YRD_isBayBlocked(destiny_bay):
            if not (boxes_blocking_target_bay[0] == box and boxes_blocking_target_bay[-1] == box):
            #warnings.warn("WARNING: Relocating BOX {}, from {} to a blocked Bay {}. It may be possible that the bay was cleared when BOX was moved".format(box, box.bay, destiny_bay))
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
        :return: yard string
        '''
        for block in self.YRD_getBlockList():
            logger.info(block.BLK_getName())
            for i in range(long_number):
                aux_string = ""
                for j in range(wide_number):
                    aux_string = aux_string + str(block.BLK_getBay(i+long_number*j))
                logger.info(aux_string)

    def YRD_exportYardSnapShot(self, wide_number, long_number):
        '''
        Returns a string with current status of the container yard
        :param wide_number:
        :param long_number:
        :return: yard string
        '''
        logger.info("SNAPSHOT GENERATED")
        snapshot_string = ""
        for block in self.YRD_getBlockList():
            snapshot_string = snapshot_string + block.BLK_getName() + "\n"
            for i in range(long_number):
                aux_string = ""
                for j in range(wide_number):
                    aux_string = aux_string + str(block.BLK_getBay(i+long_number*j))
                snapshot_string = snapshot_string + aux_string + "\n"
        #print(snapshot_string)
        return snapshot_string

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
                logger.info("{} is in service area".format(box))
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
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   