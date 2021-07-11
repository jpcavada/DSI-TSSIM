import pathlib as pl
import export_JSON_data
import subprocess
import os


class Controller:

    def __init__(self, yard):
        self.yard = yard
        self.status = 0  # 0 = deactivated 1 = engaged
        self.movements = []
        self.model_life = 0
        self.needUpdate = True
        self.modelPath = pl.Path("optimiza/modelo.py")
        self.tempPath = pl.Path("optimiza/temp")
        self.look_ahead_time = 120
        self.name = 'test'

    def CheckModelStatus(self):
        print("HP : {}/{}".format(len(self.movements), self.model_life))
        if not self.needUpdate:
            if (len(self.movements) / self.model_life) < 0.5:
                print("modelo desactualizado")
                self.needUpdate = True
        else:
            self.needUpdate = False

    def runModel(self, simtime, arrivals):
        """
        Exporta el modelo, ejecuta el modelo y crea la lista de movimientos
        :param simtime:
        :param arrivals:
        :return:
        """
        self.name = str(simtime)
        self.movements = []
        status = 0
        print("ASSUMMING DIRECT CONTROL")
        print(self.tempPath)
        # Delete all temporary files before proceeding
        for child in self.tempPath.iterdir():
            if child.is_file():
                pl.Path.unlink(child)

        # Export current simulation status
        export_JSON_data.export_JSON_status(simtime, self.yard, arrivals, self.look_ahead_time,
                                            self.tempPath,
                                            self.name,
                                            export_positions=True
                                            )

        contenedores_file = pl.Path.joinpath(self.tempPath, self.name + '_contenedores.json')
        posiciones_file = pl.Path.joinpath(self.tempPath, self.name + '_posiciones.json')

        # print("model", str(self.modelPath))
        # print("conts", str(contenedores_file))
        # print("pos", str(posiciones_file))
        # print("out", str(self.tempPath))

        # Run optimization modelo
        command = "python3 /optimiza/modelo.py"
        # print(command)
        pl.Path.mkdir(pl.Path.joinpath(self.tempPath, 'model_logs'), exist_ok=True)
        model_log = open(pl.Path.joinpath(self.tempPath, 'model_logs', self.name + '.log'), 'w')
        resumen = subprocess.run(["python3",
                                  str(self.modelPath),
                                  str(contenedores_file),
                                  str(posiciones_file),
                                  "-n", str(self.name),
                                  "-o", str(self.tempPath) + os.path.sep,
                                  "-s", "Resumen"],
                                 stdout=model_log, stderr=model_log)
        # ["python3", "modelo.py", contenedores_file, posiciones_file, "-n "+i, "-o="+out_PATH, "-s=RESUMEN"]

        print(resumen)

        with open(pl.Path.joinpath(self.tempPath, 'status')) as sf:
            for line in sf.readlines():
                if line == 'OPTIMAL' or 'TIME_LIMIT':
                    model_status = 1

        # Si el modelo se completo
        if model_status == 1:
            self.needUpdate = False
            x_file = pl.Path.joinpath(self.tempPath, self.name + '_x')

            with open(x_file) as fx:
                lines_x = fx.readlines()
                relocaciones = []
                for line in lines_x:
                    tokens = line.split()
                    if tokens[0] != 'E':
                        move = {
                            'sec': tokens[0],
                            'tipo': tokens[1],
                            'cont': tokens[2],
                            'orig': tokens[3],
                            'dest': tokens[4],
                        }
                        if move['tipo'] == 'V':
                            self.movements.append(move)
                        elif move['tipo'] in ['XC', 'XM', 'EX']:
                            relocaciones.append(move)
                        elif move['tipo'] == 'W':
                            move['relocs'] = relocaciones
                            relocaciones = []
                            self.movements.append(move)

            self.model_life = len(self.movements)
        else:
            self.movements = []
            self.needUpdate = True
            self.model_life = 0

        # for m in self.movements:
        #   print(m)

    def getArrivalPosition(self, box_name, simtime, arrivals):
        print("[{}] Arrival buscanco posicion para {}".format(simtime, box_name))
        self.CheckModelStatus()
        if self.needUpdate:
            print("Modelo desactualizado...corriendo")
            self.runModel(simtime, arrivals)
        nextMove = self.getNextMove(box_name, 'V')
        if nextMove is not None:
            return nextMove['dest']
        else:
            print("{} Arrival no encontrado...corriendo modelo de nuevo".format(box_name))
            self.runModel(simtime, arrivals)
            nextMove = self.getNextMove(box_name, 'V')
            if nextMove is not None:
                return nextMove['dest']
            else:
                print("{} no encontrada de nuevo...dejo al sim decider este".format(box_name))
                return 0

    def getRemovalMoves(self, box_name, simtime, arrivals):
        self.CheckModelStatus()
        blocker_moves = []
        if self.needUpdate:
            print("Modelo desactualizado...corriendo")
            self.runModel(simtime, arrivals)
        nextMove = self.getNextMove(box_name, "W")
        if nextMove is not None:
            for bm in nextMove['relocs']:
                blocker_moves.append([bm['cont'], bm['dest']])
            print('{} Removal encontrado, con {}'.format(box_name, blocker_moves))
            return blocker_moves
        else:
            print("{} Removal no encontrado...corriendo modelo de nuevo".format(box_name))
            self.runModel(simtime, arrivals)
            nextMove = self.getNextMove(box_name, "W")
            if nextMove is not None:
                for bm in nextMove['relocs']:
                    blocker_moves.append([bm['cont'], bm['dest']])
                print('{} Removal encontrado, con {}'.format(box_name, blocker_moves))
                return blocker_moves
            else:
                print("{} Removal no encontrado de nuevo...dejo al sim decidir este".format(box_name))
                return 0

    def getNextMove(self, cont, tipo):
        nextMove = None
        for move_index in range(len(self.movements)):
            move = self.movements[move_index]
            if move['cont'] == cont and move['tipo'] == tipo:
                nextMove = self.movements.pop(move_index)
                print("encontre el movimiento para {}".format(cont))
                break
        return nextMove
