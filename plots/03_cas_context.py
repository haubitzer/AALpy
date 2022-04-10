# Import libraries
import matplotlib.pyplot as plt
import numpy as np
import tikzplotlib

N = 3
learning = (5257, 4677, 20620)
completeness = (3000, 2574, 10453)
learningStd = (0, 0, 0)
completenessStd = (0, 0, 0)
ind = np.arange(N)
width = 0.35

fig = plt.subplots(figsize =(10, 7))
p1 = plt.bar(ind, learning, width, yerr = learningStd)
p2 = plt.bar(ind, completeness, width, bottom = learning, yerr = completenessStd)

plt.ylabel('Interactions wiht \\SUL')
plt.title('Interactions with fixed completeness certainty  99%')
plt.xticks(ind, ('M1', 'M2', 'M3'))
plt.xlabel('Output certainty ')
plt.legend((p2[0], p1[0]), ('Completeness Query', 'Output query',))

####################

# Save to file
tikzplotlib.save("./03_cas_data.tex")

# show plot
plt.show()
