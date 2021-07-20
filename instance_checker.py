INPUT = 'INSTANCES/INSTANCES_180D_F2_100/arrivals_13.ini'
OUTPUT = 'INSTANCES/INSTANCES_180D_F2_100/arrivals_14.ini'


f = open(INPUT)

dates = set()
original = {}
to_change = {}

for line in f.readlines():
    tokens = line.strip().split(" ")
    original[tokens[0]] = [int(tokens[1]), int(tokens[2])]
    if int(tokens[1]) in dates:
        to_change[tokens[0]] = 0
    if int(tokens[2]) in dates:
        to_change[tokens[0]] = 1
    dates.add(int(tokens[1]))
    dates.add(int(tokens[2]))

for cont, i in to_change.items():
    print(cont, i, "a cambiar", original[cont][i], original[cont])
    j = original[cont][i]
    while j in dates:
        j += 1
    original[cont][i] = j
    print("nuevo {}".format(original[cont]))

n = open(OUTPUT, 'w+')
for i,j in original.items():
    n.write("{} {} {}\n".format(i, j[0], j[1]))


