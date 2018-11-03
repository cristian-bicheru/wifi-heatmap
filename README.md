# wifi-heatmap
WiFi Heat Map Simulator

## CSV Format:
### Data:
d,xMeters,yMeters,resX,resY
### Transmitters:
t,x1,y1,TXPower(mW),gain(dBi),frequency(hz)
### Obstacles:
o,x1,y1,x2,y2,{Amount of Signal Loss}

## Other Details:
This script uses the Friis Transmission Equation to calculate signal strength and outputs a strict heatmap based on the received dBm.

### Requirements:
* **Matplotlib**
* **Numpy**
* **PIL**
