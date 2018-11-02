from PIL import Image, ImageDraw, ImageFont
import scipy.optimize
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pickle
import warnings

### Config

rgain = 2                           # Receiver Gain (dBi)
dimMeters = (1000, 1000)            # Dimensions of the data in meters
warnings.filterwarnings("ignore")   # Don't print slow convergence warning
render = 0                          # Render or use existing renderedData.pickle

### End Config

wificmap = matplotlib.colors.LinearSegmentedColormap.from_list('Wifi Signal Strength', ['grey', 'red', 'green', 'blue'], N=128)
wifinorm = matplotlib.colors.BoundaryNorm([-90, -80, -70, -67, -30], wificmap.N)

raw = Image.open("raw.png")
dM = (dimMeters[0]/raw.size[0], dimMeters[1]/raw.size[1])

with open("rawdata.csv", "r") as f:
    rawdata = f.readlines()
    f.close()

transmitters = []
obstacles = []

class obstacle(object):
    def __init__(self, c1, c2, signalLoss):
        self.coords = [c1, c2]
        self.signalLoss = signalLoss

class transmitter(object):
    def __init__(self, c1, TXpower, gain, freq):
        self.coords = c1
        self.txpower = TXpower
        self.gain = gain
        self.freq = freq

def xconv(x): # Converts x (pixels) to x (meters)
    global dM
    return dM[0]*x

def yconv(y): # Converts y (pixels) to y (meters)
    global dM
    return dM[1]*y

for each in rawdata:
    temp = each.split(", ")
    if "(" in temp[1]:
        obstacles.append(obstacle(temp[0], temp[1], temp[2]))
    else:
        transmitters.append(transmitter(temp[0], temp[1], temp[2], temp[3]))

def isIntersect(x, y, tx, ty, m, b, c1, c2):
    if m != "v":
        x1, y1 = map(float, c1[1:][:-1].split(","))
        x2, y2 = map(float, c2[1:][:-1].split(","))
        if x2 != x1:
            m2 = (y2-y1)/(x2-x1)
            b2 = y2-m2*x2
            funcStr = str(m)+"*x+"+str(b)+"-("+str(m2)+"*x+"+str(b2)+")"
            def f(x):
                return eval(funcStr.replace("x", str(x[0])))
            sol = scipy.optimize.fsolve(f, x)
            ysol = m*sol+b
            if x>=sol>=float(tx) or x<=sol<=float(tx):
                if y1>=ysol>=y2 or y1<=ysol<=y2:
                    return True
                else:
                    return False
            else:
                return False
        else:
            if x>=x1>=float(tx) or x<=x1<=float(tx):
                ysol = m*x1+b
                if y1>=ysol>=y2 or y1<=ysol<=y2:
                    return True
                else:
                    return False
            else:
                return False           
    else:
        x1, y1 = map(float, c1[1:][:-1].split(","))
        x2, y2 = map(float, c2[1:][:-1].split(","))
        if x2 != x1:
            m2 = (y2-y1)/(x2-x1)
            b2 = y2-m2*x2
            ysol = m2*x+b2
            if y>=ysol>=float(ty) or y<=ysol<=float(ty):
                return True
            else:
                return False
        else:
            return False

def idealStrength(x, y, tx, ty, txpower, tgain, rgain, freq):
    dist = np.linalg.norm(np.array([x-float(tx), y-float(ty)]))
    mWReceived = txpower*1000*0.627107*tgain*rgain*((299792458)/(4*np.pi*dist*freq+0.001))**2
    return 10*np.log10(mWReceived)

def maxStrength(x, y, transmitters, obstacles):
    strengths = []
    for each in transmitters:
        signalLoss = 0
        tx, ty = each.coords[1:][:-1].split(',')
        if x != float(tx):
            m = (y-float(ty))/(x-float(tx))
            b = y-m*x
        else:
            m = "v"
            b = x
        
        for each2 in obstacles:
            intsct = isIntersect(x, y, tx, ty, m, b, each2.coords[0], each2.coords[1])
            if intsct == True:
                signalLoss += float(each2.signalLoss)

        ideal = idealStrength(x, y, tx, ty, float(each.txpower), float(each.gain), float(rgain), float(each.freq))
        strengths.append(ideal-signalLoss)
    return max(strengths)

if render == 1:
    z = np.array(np.zeros(shape=(raw.size[0], raw.size[1])))
    print('rendering..')
    cpct = 0
    xsize = raw.size[0]
    for x in range(0, xsize):
        pct = x/xsize*100
        if pct >= cpct:
            print(str(round(pct, 2))+"%")
            cpct += 5
        for y in range(0, raw.size[1]):
            z[y][x] = maxStrength(x, y, transmitters, obstacles)
    print('rendered')
    print("saving..")
    with open("renderedData.pickle", "wb") as f:
        pickle.dump(z, f)
        f.close()
    print("saved")
else:
    print('loading..')
    with open("renderedData.pickle", "rb") as f:
        z = pickle.load(f)
        f.close()
    print('loaded')
print("plotting..")
fig = plt.figure(figsize=(1, 1), dpi=100)
plt.gca().invert_yaxis()
plt.axis('off')
plt.gca().set_aspect('equal', adjustable='box')
cmsh = plt.pcolormesh(np.linspace(0, raw.size[0], raw.size[0]), np.linspace(0, raw.size[1], raw.size[1]), z, cmap=wificmap, norm=wifinorm)
fig.subplots_adjust(bottom = 0)
fig.subplots_adjust(top = 1)
fig.subplots_adjust(right = 1)
fig.subplots_adjust(left = 0)
plt.savefig('plot.png', dpi=1000)

plt.figure()
fig, axes = plt.subplots()
plt.colorbar(cmsh, ax=axes)
axes.remove()
plt.savefig('cbar.png', bbox_inches='tight')

plot = Image.open("plot.png")
plot.paste(raw, (0, 0), raw)
plot.save('heatmap.png')
print('done')
