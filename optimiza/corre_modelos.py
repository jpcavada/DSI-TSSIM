import os
import subprocess

in_PATH = 'inputs/'
out_PATH = 'outputs/'

scenarios = set()
for root, dir, files in os.walk(in_PATH):
    for names in files:
        key = names.split('_')[0]
        scenarios.add(key)

stats_file = open('stats.txt', 'a+')

for i in scenarios:

    print('Ejecutando = {}'.format(i))
    #contenedores_file = '84480_contenedores.json' #.format(in_PATH, i)
    #posiciones_file = '84480_posiciones.json' #.format(in_PATH, i)
    contenedores_file = '{}{}_contenedores.json'.format(in_PATH, i)
    posiciones_file = '{}{}_posiciones.json'.format(in_PATH, i)
    print(contenedores_file)
    print(posiciones_file)

    proc = subprocess.run(["python3", "modelo.py", contenedores_file, posiciones_file, "-n "+i, "-o="+out_PATH, "-s=RESUMEN"])
    #r = modelo.run(i, contenedores_file, posiciones_file, outpath=out_PATH, echo=False)

    '''
    try:
        r = proc.stdout
        stats_file.write(r)
        stats_file.write('\n')
        print(r)
    except:
        stats_file.write('{} No se puedo recuperar info\n'.format(i))
    '''
