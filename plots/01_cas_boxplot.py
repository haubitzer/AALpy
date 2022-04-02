# Import libraries
import matplotlib.pyplot as plt
import numpy as np
import tikzplotlib

data_90 = [29911, 27043, 23015, 32077, 27351, 24001, 24712, 53353, 16685, 35023, 22152] # 4 failed
data_95 = [17229, 11630, 27223, 33413, 43734, 40491, 26257, 40972] # 7 failed
data_99 = [31834, 37299, 36122, 31320, 34540, 35753, 30403, 35592, 39522, 39174, 34121, 35986, 21164, 30860, 41875, 49037, 47649, 30210, 38991, 36050]
data_99999 = [88976, 58092, 64295, 48205, 37933, 62402, 30093, 22887, 35997, 31016, 54027, 30675, 43697, 31408, 52619]
data = [data_90, data_95, data_99, data_99999]

plt.boxplot(data, showfliers=True, medianprops=dict(color='black'))
plt.xticks([1, 2, 3, 4], ['90% \n(Failed 4/15)', '95%\n(Failed 7/15)', '99%\n(Failed 0/20)', '99.999%\n(Failed 0/15)'])

plt.xlabel("Certainty and Failure Rate")
plt.title('\\SUL interaction to learn a correct\nNon-deterministic Model of the Car Alarm System')
plt.ylabel("# of interaction with \\SUL")

####################

# Save to file
tikzplotlib.save("./plots/data_01_cas_boxplot.tex")

# show plot
plt.show()
