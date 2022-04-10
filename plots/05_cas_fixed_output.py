# Import libraries
import matplotlib.pyplot as plt
import numpy as np
import tikzplotlib

N = 4
learning = (5418, 5159, 4900, 4677)
completeness = (858, 1287, 1716, 2574)
learningStd = (0, 0, 0, 0)
completenessStd = (0, 0, 0, 0)
ind = np.arange(N)
width = 0.35

fig = plt.subplots(figsize =(10, 7))
p1 = plt.bar(ind, learning, width, yerr = learningStd)
p2 = plt.bar(ind, completeness, width, bottom = learning, yerr = completenessStd)

plt.ylabel('Interactions wiht \\SUL')
plt.title('Interactions with fixed completeness certainty  99%')
plt.xticks(ind, ('80%', '90%', '95%', '99%'))
plt.xlabel('Output certainty ')
plt.legend((p2[0], p1[0]), ('Completeness Query', 'Output query',))

####################

# Save to file
tikzplotlib.save("./05_cas_data.tex")

# show plot
plt.show()
