import subprocess
import os
import threading

name = "F18_MM_"
direc = "INSTANCES\INSTANCES_18D_F18\\"
criteria = "MM"
output_dir = "INSTANCES\INSTANCES_18D_F18\Salidas\\MM\\"
N = 1

#Threading Config


class Runner():
    def __init__(self):
        MAX_THREADS = 4
        self.sema = threading.Semaphore(MAX_THREADS)

    def caller(self, cmd,esc_num):
        self.sema.acquire()
        print("Running Sim {} of {}".format(esc_num, N))
        #with open(os.devnull, "w") as f:
         #   a = subprocess.call(cmd, stderr=f)
         #   print(a)
        print(subprocess.call(cmd))
        print("Finished Escenario {}".format(esc_num))
        self.sema.release()

    def runner(self):
        threads = []
        for i in range(1,N+1):
            cmd = "python Sim_entradas_salidas_2.py --name=" + name + str(i) + " --arrivals=" + direc + "arrivals_"+ str(i) +".ini" + " --criteria=" + criteria + " --outputdir=" + output_dir
            threads.append(threading.Thread(name='TLSSIM_{}'.format(i), target=self.caller, args=[cmd, i]))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print("Simulation Complete")

if __name__ == '__main__':
    r = Runner()
    r. runner()
