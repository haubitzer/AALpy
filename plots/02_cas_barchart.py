# Import libraries
import matplotlib.pyplot as plt
import numpy as np
import tikzplotlib

N = 3
steps = (1311+1270, 1414+1356, 6322)
listen = (1329+1236, 1433+1347, 4385)
stepsStd = (57, 0, 777)
listenStd = (48, 0, 517)
ind = np.arange(N)
width = 0.35

fig = plt.subplots(figsize =(10, 7))
p1 = plt.bar(ind, steps, width, yerr = stepsStd)
p2 = plt.bar(ind, listen, width, bottom = steps, yerr = listenStd)

plt.ylabel('# of interaction wiht \\SUL')
plt.title('\\SUL interaction with certainty 90%')
plt.xticks(ind, ('T1', 'T2', 'T3'))
plt.legend((p1[0], p2[0]), ('Steps', 'Listens'))

####################

# Save to file
tikzplotlib.save("./data_02_cas_barchart.tex")

# show plot
plt.show()
