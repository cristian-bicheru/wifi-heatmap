from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pickle

### Config

rgain = 2                           # Receiver Gain (dBi)
render = 1                          # Render (1) or use prerendered data (0)

### End Config

wificmap = matplotlib.colors.LinearSegmentedColormap.from_list('Wifi Signal Strength', ['grey', 'red', 'green', 'blue'], N=128)
wifinorm = matplotlib.colors.BoundaryNorm([-90, -80, -70, -67, -30], wificmap.N)

raw = Image.open("raw.png")

with open("rawdata.csv", "r") as f:
    rawdata = f.readlines()[1:]
    f.close()

transmitters = []
obstacles = []

class obstacle(object):
    def __init__(self, x1, y1, x2, y2, signalLoss):
        self.coords = ((float(x1), float(y1)), (float(x2), float(y2)))
        self.signalLoss = float(signalLoss)

class transmitter(object):
    def __init__(self, x1, y1, TXpower, gain, freq):
        self.coords = (float(x1), float(y1))
        self.txpower = float(TXpower)
        self.gain = float(gain)
        self.freq = float(freq)

def xconv(x): # Converts x (pixels) to x (meters)
    global dM
    return dM[0]*x

def yconv(y): # Converts y (pixels) to y (meters)
    global dM
    return dM[1]*y

for each in rawdata:
    temp = each.split(",")
    vtype = temp[0]
    if vtype == 'o':
        obstacles.append(obstacle(temp[1], temp[2], temp[3], temp[4], temp[5]))
    elif vtype == 't':
        transmitters.append(transmitter(temp[1], temp[2], temp[3], temp[4], temp[5]))
    else:
        resx = int(temp[3])
        resy = int(temp[4])
        dM = (float(temp[1])/raw.size[0], float(temp[2])/raw.size[1])

def isIntersect(x, y, tx, ty, m, b, c1, c2):
    if m != "v":                    # if the ray is not vertical
        x1, y1 = c1
        x2, y2 = c2
        if x2 != x1:                # if the obstacle is not vertical
            m2 = (y2-y1)/(x2-x1)
            b2 = y2-m2*x2
            if m == m2:             # if the lines are parallel
                if b != b2:         # if the lines are not colinear
                    return False
                else:
                    return True
            xsol = (b2-b)/(m-m2)    # x coordinate of the intersection
            ysol = m*xsol+b         # y coordinate of the intersection
            if x >= xsol >= tx or x <= xsol <= tx:          # testing to see if the solution is within the points,
                if y1 >= ysol >= y2 or y1 <= ysol <= y2:    # since the solution could be anywhere on the plane
                    return True
                else:
                    return False
            else:
                return False
        else:                       # otherwise, if it is vertical
            if x >= x1 >= tx or x <= x1 <= tx:
                ysol = m*x1+b
                if y1 >= ysol >= y2 or y1 <= ysol <= y2:
                    return True
                else:
                    return False
            else:
                return False           
    else:                           # otherwise, if the ray is vertical
        x1, y1 = c1
        x2, y2 = c2
        if x2 != x1:
            m2 = (y2-y1)/(x2-x1)
            b2 = y2-m2*x2
            ysol = m2*x+b2
            if y >= ysol >= ty or y <= ysol <= ty:
                return True
            else:
                return False
        else:
            return False

def idealStrength(x, y, tx, ty, txpower, tgain, rgain, freq):
    dist = np.linalg.norm(np.array([x-tx, y-ty]))
    mWReceived = txpower*1000*0.627107*tgain*rgain*((299792458)/(4*np.pi*dist*freq))**2
    return 10*np.log10(mWReceived)

def maxStrength(x, y, transmitters, obstacles):
    strengths = []
    for each in transmitters:
        signalLoss = 0
        tx, ty = each.coords
        if x != tx or y != ty:
            if x != tx:
                m = (y-ty)/(x-tx)
                b = y-m*x
            else:
                m = "v"
                b = x
            
            for each2 in obstacles:
                intsct = isIntersect(x, y, tx, ty, m, b, each2.coords[0], each2.coords[1])
                if intsct == True:
                    signalLoss += each2.signalLoss
            ideal = idealStrength(x, y, tx, ty, each.txpower, each.gain, rgain, each.freq)
            strengths.append(ideal-signalLoss)
        else:
            strengths.append(0)
    return max(strengths)

if render == 1:
    z = np.array(np.zeros(shape=(raw.size[0], raw.size[1])))
    print('rendering..')
    cpct = 0
    xsize = raw.size[0]
    for x in range(0, xsize, resx):
        pct = x/xsize*100
        if pct >= cpct:
            print(str(round(pct, 2))+"%")
            cpct += 5
        for y in range(0, raw.size[1], resy):
            cz = maxStrength(x, y, transmitters, obstacles)
            for i in range(0, resx):
                for i2 in range(0, resy):
                    z[y+i2][x+i] = cz
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
draw = ImageDraw.Draw(plot)
for each in transmitters:
    x, y = each.coords
    draw.ellipse((x-4, y-4, x+4, y+4), fill = 'black', outline ='black')
    draw.ellipse((x-1, y-1, x+1, y+1), fill = 'yellow')
plot.save('heatmap.png')
print('done')
