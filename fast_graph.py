import numpy as np
import matplotlib.pyplot as plt

"Total Relocaciones"
total_RI = [1350, 1182, 1481, 1419, 1384, 1457, 1488, 1254, 1370, 1215, 1402, 1248, 1088, 1299, 1341, 1199, 1444, 1154, 1255, 1188, 1518, 1465, 1521, 1179]
total_RIL = [390, 389, 375, 508, 367, 474, 535, 351, 404, 392, 406, 361, 338, 346, 484, 467, 502, 293, 455, 355, 600, 558, 535, 373]
total_MM = [50, 12, 58, 94, 88, 123, 83, 25, 34, 5, 62, 48, 35, 55, 93, 44, 119, 66, 44, 11, 180, 159, 103, 51]

plt.figure()

plt.title("Total Relocaciones")
plt.boxplot([total_RI, total_RIL, total_MM], labels=["RI", "RIL", "MM"])
plt.show()