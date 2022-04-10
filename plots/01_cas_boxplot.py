# Import libraries
import matplotlib.pyplot as plt
import tikzplotlib

data_90 = [51799, 26566, 28878, 49909, 27589, 36800, 40501, 89121, 25877, 28057, 23199, 27650, 57735, 64014, 27482, 58066, 25702, 33540, 117724, 33626]
data_95 = [39880, 62517, 26546, 40432, 25297, 20136, 27196, 54652, 73114, 29862, 77047, 80039, 38111, 45524, 45595, 39312, 49708, 26967, 26995, 53883]
data_99 = [31073, 34874, 44069, 44296, 35355, 26870, 29994, 35205, 53866, 69094, 75039, 34955, 33438, 55264, 69364, 27292, 63133, 30596, 29227, 63158]
data_99999 = [133675, 68714, 48044, 45698, 51889, 56501, 63307, 76517, 49015, 49839, 47314, 43454, 84641, 154667, 51671, 100996, 65322, 66219, 87129, 46214]
data = [data_90, data_95, data_99, data_99999]

plt.boxplot(data, showfliers=True, medianprops=dict(color='black'))
plt.xticks([1, 2, 3, 4], ['90%', '95%', '99%', '99.999%'])

plt.xlabel("Certainty and Failure Rate")
plt.title('\\SUL interaction to learn a correct\nNon-deterministic Model of the Car Alarm System')
plt.ylabel("# of interaction with \\SUL")

####################

# Save to file
tikzplotlib.save("./plots/01_cas_data.tex")

# show plot
plt.show()
