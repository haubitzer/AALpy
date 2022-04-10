# Import libraries
import matplotlib.pyplot as plt
import numpy as np
import tikzplotlib

N = 3
steps = (2792, 2586, 15728)
listen = (5465, 4665, 24740)
stepsStd = (0, 0, 5104)
listenStd = (0, 0, 7849)
ind = np.arange(N)
width = 0.35

fig = plt.subplots(figsize =(10, 7))
p1 = plt.bar(ind, steps, width, yerr = stepsStd)
p2 = plt.bar(ind, listen, width, bottom = steps, yerr = listenStd)

plt.ylabel('# of interaction wiht \\SUL')
plt.title('\\SUL interaction with certainty 99%')
plt.xticks(ind, ('M1', 'M2', 'M3'))
plt.legend((p1[0], p2[0]), ('Steps', 'Listens'))

####################

# Save to file
tikzplotlib.save("./02_cas_data.tex")

# show plot
plt.show()
