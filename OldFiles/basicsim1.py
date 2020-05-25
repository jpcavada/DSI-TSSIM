# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 16:37:23 2019
Este ejemplo trae 3 contenederos que llegan y se van 

@author: jpcavada
"""

import simpy
import random

import yard_class as yard

def main():
    contenedores = []
    for i in range(0,12):
        contenedores.append(yard.Box("Cont "+str(i),date_in=random.randint(1,50)))
   
    env = simpy.Environment()
    cranes_res = simpy.Resource(env, 1)
    env.process(box_llegadas(env,contenedores,cranes_res))
    env.process(box_salidas(env,contenedores, cranes_res))
    
    env.run(until=150)
    
def box_llegadas(env,contenedores,cranes_res):
    for i in contenedores:
        yield env.timeout(i.date_in - env.now)
        print("Llego "+str(i.name)+" a las "+str(env.now))
        env.process(movimientos(env, i, cranes_res))
        
def box_salidas(env,contenedores,cranes_res):
    for i in contenedores:
        yield env.timeout(i.date_out - env.now)
        print("%s quiere salir a las %i" %(i.name, env.now))
        env.process(movimientos(env,i,cranes_res))
        
def movimientos(env, box, cranes):
    with cranes.request() as req:
        yield req # pide una gra
        print('%s recibio grua a las %i' % (str(box.name), env.now))
        #movmineto
        yield env.timeout(15)
        print("Grua se liberó a las %i" %env.now)

if __name__ ==  '__main__':
    main()
    