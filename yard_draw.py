from matplotlib import pyplot as plt
from matplotlib import patches
from matplotlib.collections import PatchCollection
import json
import yard_class
import mplcursors

YARD_BLOCKS_NAMES = ["LU", "RU", "LD", "RD"]
BAYS_WIDE_NAMES = ["A", "B", "X", "Y"]
BAYS_LONG_SIZE = 12
BAYS_HIGH_SIZE = 4
ancho = 10
alto = 50


def draw(yard, save_file, cont_status=None, sol_file=None):

    cont_list = []
    if cont_status is not None:
        cont_list = get_cont_status(cont_status)

    sol_cont_list = {}
    if sol_file is not None:
        with sol_file.open() as data:
            sol_cont_list = json.load(data)

    pos_anchor_points = {}

    fig, ax = plt.subplots(figsize=(10, 10))
    #Dibujo cada block
    for block in yard.YRD_getBlockList():
        bays_list = []
        for bay in block.BLK_getBayList():
            name = bay.BAY_getName()
            col_name = name[2]
            if col_name == 'A':
                col = 1
            elif col_name == 'B':
                col = 2
            elif col_name == 'X':
                col = 3
            elif col_name == 'Y':
                col = 4

            b = {
                'name': name,
                'conts': bay.BAY_getBoxList(),
                'row': int(name[3:]) - 1,
                'col': col
            }
            bays_list.append(b)
        # Set BLOCK ANCHORS POINT
        if block.BLK_getName() == 'LU':
            block_anchor = {'x': 0, 'y': 0}
        elif block.BLK_getName() == 'LD':
            block_anchor = {'x': 0, 'y': 0 - BAYS_LONG_SIZE * alto - alto}
        elif block.BLK_getName() == 'RU':
            block_anchor = {'x': BAYS_HIGH_SIZE * ancho + ancho, 'y': 0}
        elif block.BLK_getName() == 'RD':
            block_anchor = {'x': BAYS_HIGH_SIZE * ancho + ancho, 'y': 0 - BAYS_LONG_SIZE * alto - alto}

        for p in range(0, BAYS_LONG_SIZE):
            ax.annotate(p+1, (block_anchor['x'] + ancho / 2, block_anchor['y'] - p * alto - alto / 2))

        if block.BLK_getName() in ['LD', 'RD']:
            ax.annotate('A', (block_anchor['x'] + ancho + ancho / 2, block_anchor['y'] + alto / 2))
            ax.annotate('B', (block_anchor['x'] + 2 * ancho + ancho / 2, block_anchor['y'] + alto / 2))
            ax.annotate('X', (block_anchor['x'] + 3 * ancho + ancho / 2, block_anchor['y'] + alto / 2))
            ax.annotate('Y', (block_anchor['x'] + 4 * ancho + ancho / 2, block_anchor['y'] + alto / 2))

        artists = []
        for b in bays_list:
            bay_anchor_x = block_anchor['x'] + (b['col'] * ancho)
            bay_anchor_y = block_anchor['y'] - (b['row'] * alto) - alto

            pos_anchor_points[b['name']] = {'x': bay_anchor_x, 'y': bay_anchor_y}

            ax.scatter(bay_anchor_x, bay_anchor_y, facecolor='white')
            ax.add_patch(patches.Rectangle((bay_anchor_x, bay_anchor_y), ancho, alto, linewidth=1, fill=False))


            for i in range(len(b['conts'])):
                if cont_list:
                    status = cont_list[b['conts'][i].BOX_getName()]

                    if status == 'fijo':
                        rec_color = 'grey'
                    elif status == 'sale':
                        rec_color = 'green'
                    elif status == 'mover':
                        rec_color = 'yellow'
                    else:
                        rec_color = 'white'

                box = patches.Rectangle((bay_anchor_x,
                                         bay_anchor_y + i * alto / 4),
                                        ancho, alto / 4,
                                        linewidth=0.5,
                                        ec='black',
                                        fc=rec_color)



                artists.append(box)

                ax.text(bay_anchor_x + ancho / 2,
                        bay_anchor_y + i * alto / 4,
                        b['conts'][i],
                        color='black',
                        fontsize=6,
                        ha='center')

        # Se pasa el bloque a
        collection = PatchCollection(artists, match_original=True, alpha=0.5)
        ax.add_collection(collection)

    #Dibujar subbloque de soluciones
    if sol_file is not None:
        # Los que llegab
        for etapa, vals in sol_cont_list.items():
            tipo = vals['tipo']
            cont = vals['cont']
            orig = vals['orig']
            dest = vals['dest']
            if vals['tipo'] == 'V':
                tokens = vals['dest'].split('-')
                bay_name = tokens[0]
                altura = int(tokens[1])

                ax.add_patch(patches.Rectangle((pos_anchor_points[bay_name]['x'],
                                                pos_anchor_points[bay_name]['y'] + altura * alto / 4),
                                               ancho, alto / 4,
                                               linewidth=0.5,
                                                ec='black',
                                                fc='lightblue'))

    #Crear la Figura
    plt.tight_layout()
    plt.xlim(0, 110)
    plt.ylim(-1310, 0)
    plt.axis('off')
    plt.show()
#    plt.savefig(save_file)
    plt.close()



def get_cont_status(contenedores_file):
    cont = {}
    with open(contenedores_file) as json_file:
        data = json.load(json_file)
        for c, [tc, pos, status] in data['contenedores'].items():  # val=[t_salida, posicion, status]
            cont[c] = status
    return cont

