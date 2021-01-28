from multiprocessing import Pool
import threading
import tqdm
import subprocess
import os
import Sim_entradas_salidas_2 as sim
import time
import sys

#INS_NAME = "180D_MM_"
#INS_DIR = "INSTANCES\INSTANCES_180D_F18\\"
#CRITERIA = "MM"
#OUT_DIR = "INSTANCES\INSTANCES_180D_F18\Salidas\\MM\\"

A = [
    ["180D_F18_100_MM_", "INSTANCES\Resultados\F18_100\Versus\MM\\", "MM", "INSTANCES\INSTANCES_180D_F18_100\\"],
 #   ["180D_F18_100_RI_", "INSTANCES\Resultados\F18_100\Versus\RI\\", "RI", "INSTANCES\INSTANCES_180D_F18_100\\"],
 #   ["180D_F18_100_RIL_", "INSTANCES\Resultados\F18_100\Versus\RIL\\", "RIL", "INSTANCES\INSTANCES_180D_F18_100\\"],
  #  ["180D_F18_100_MM_", "INSTANCES\Resultados\F18_100\Versus\MM\\", "MM", "INSTANCES\INSTANCES_180D_F18_100\\"],
   # ["180D_F18_100_RI-C_", "INSTANCES\Resultados\F18_100\Versus\RI-C\\", "RI-C", "INSTANCES\INSTANCES_180D_F18_100\\"],
    #["180D_F18_100_RIL-C_", "INSTANCES\Resultados\F18_100\Versus\RIL-C\\", "RIL-C", "INSTANCES\INSTANCES_180D_F18_100\\"],
    #["180D_F18_100_RI-S_", "INSTANCES\Resultados\F18_100\Versus\RI-S\\", "RI-S", "INSTANCES\INSTANCES_180D_F18_100\\"],
    #["180D_F18_100_RIL-S_", "INSTANCES\Resultados\F18_100\Versus\RIL-S\\", "RIL-S", "INSTANCES\INSTANCES_180D_F18_100\\"],
    #["180D_F18_100_MM-S_", "INSTANCES\Resultados\F18_100\Versus\MM-S\\", "MM-S", "INSTANCES\INSTANCES_180D_F18_100\\"],

    #["180D_F3_MM_", "INSTANCES\INSTANCES\Salidas\\MM\\", "MM", "INSTANCES\INSTANCES_180D_F3\\"],
   # ["180D_F17_MM_", "INSTANCES\INSTANCES\Salidas\MM\F17\\", "MM", "INSTANCES\INSTANCES_180D_F17\\"],
    #["180D_F175_MM_", "INSTANCES\INSTANCES\Salidas\\MM\\", "MM", "INSTANCES\INSTANCES_180D_F175\\"],
    
]


#Threading Config
MAX_THREADS = 4
N=1
sema = threading.Semaphore(MAX_THREADS)

def caller(main):
    sema.acquire()
    start_time = time.time()
    main.runSimulation(quiet=True)
    end_time = time.time()
    delta = end_time - start_time
    print("total time {}".format(delta))
    print(main.run_status)
    sema.release()

def ProccesCall(name, outputdir, criteria, arrival):
    start_time = time.time()
    newsim = sim.TLSSIM(name=name, outputdir=outputdir, criteria=criteria, arrivals=arrival)
    newsim.runSimulation(quiet=True)
    end_time = time.time()
    delta = end_time - start_time
    print("total time {}".format(delta))
    return newsim.run_status

threads = []
replicas = []

print("Loaded {} scenarios".format(len(A)))
for j in A:
    run_results = ""
    print("Running {} replicas for scenario {}".format(N, j[0][:-1]))
    for i in tqdm.tqdm(range(1, N+1)):
        tqdm.desc = j[0]
        name = j[0] + str(i)
        arrival = j[3] + "arrivals_" + str(i) + ".ini"
        criteria = j[2]
        outputdir = j[1]
    #    rep = sim.TLSSIM(name=name, outputdir=outputdir, criteria=criteria, arrivals=arrival)
        rep = sim.TLSSIM(name=name, outputdir=outputdir, criteria=criteria, arrivals=arrival)

        #print("\r"+"["+name+"] : " + "Running" )
        start_time = time.time()
        rep.runSimulation(quiet=True)
        end_time = time.time()
        delta = end_time - start_time
        run_results = run_results + "{} \t {} \t ({} s) \n".format(name, rep.run_status, delta)
    print("---===---")
    print(run_results)
    print("---===---")

'''    
   
    replicas.append(rep)
    threads.append(threading.Thread(name='TLSSIM_{}'.format(i), target=caller, args=[rep]))

for t in threads:
    t.start()

for t in threads:
    t.join()
'''

'''
VISUALIZACION
#fin = False
#while not fin:
#while any(t.is_alive() for t in threads):

    fin = True
    for m in replicas:
        fin = fin and (m.run_status in [100, "Unable to complete","COMPLETE"])
        #sys.stdout.write("\r" + str(m.run_status) + "\n")
    #sys.stdout.flush()
        print("[" + str(m.rep_name) + "]: " + str(m.run_status) + "%")
    print("-----====-----")
    if not fin:
        time.sleep(5)
'''
print("Simulation Complete")

