#!/usr/bin/python

import random
from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
import csv
import os
import sys

import numpy as np
from matplotlib.animation import FuncAnimation

plt.style.use('dark_background')

x_vals = []
y_vals = []

w = 4
h = 3
d = 70

plt.figure(figsize=(w,h), dpi=d)	

axes = plt.gca()
axes.set_ylim(0,5)
axes.set_ylabel("MOS")

axes.yaxis.set_ticks(range(6))
axes.yaxis.set_ticklabels(['N/A', 'Bad', "Poor", "Acceptable", "Good","Excellent"], fontsize=8)

axes.plot(x_vals, y_vals)

def animate(i):
	data = pd.read_csv(sys.argv[1])
	x = data['x_value']
	y1 = data['mos']

	plt.cla()	

	axes = plt.gca()
	axes.grid(True, which='both')
	axes.set_ylim(0,5)
	axes.set_ylabel("MOS", fontsize=14)

	axes.yaxis.set_ticks(range(6))
	axes.yaxis.set_ticklabels(['N/A', 'Bad', "Poor", "Acceptable", "Good","Excellent"], fontsize=10 )

	axes.xaxis.set_ticklabels(x, rotation=90)
	
	axes.yaxis.grid(True, linewidth=1, color='orange', linestyle='dashed')
	axes.xaxis.grid(True, linewidth=1, color='orange', linestyle='dashed')
	axes.plot_date(x,y1,'b-', color="green", label='MOS as a function of time')
	
	plt.legend(loc='lower right')
	plt.tight_layout()
	
	os.system(window)

# add new value to MOS graph
ani = FuncAnimation(plt.gcf(),animate,interval=sys.argv[2])

window = "wmctrl -r Figure 1 -e 1,100,300,400,350"

plt.tight_layout()
plt.show()

