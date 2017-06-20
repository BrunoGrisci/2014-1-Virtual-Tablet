import cv2
import numpy as np
import time
from PyQt4 import QtGui, QtCore
import sys

def getthresholdedimg(hsv, minH, minS, minV, maxH, maxS, maxV):
    mask = cv2.inRange(hsv,np.array((minH, minS, minV)),np.array((maxH, maxS, maxV)))
    return mask

def getmask(img):
    erode = cv2.erode(img,None,iterations = 10)
    dilate = cv2.dilate(erode,None,iterations = 10)
    return dilate

def biggest_contour(contours):
    biggest_area = 0
    found = False
    if (contours):
        for cnt in contours:
            if cv2.contourArea(cnt) > biggest_area:
                biggest_area = cv2.contourArea(cnt)
                biggest_cnt = cnt
                found = True
        if (found):
            return (biggest_cnt, biggest_area)
        else:
            return(None,0)
    else:
        return (None, 0)


def draw_square(contour, f, color):
    cx = -1
    cy = -1
    if(contour != None):
        x,y,w,h = cv2.boundingRect(contour)
        cx,cy = x+w/2, y+h/2
        if (cx > 0 and cy > 0):
            cv2.rectangle(f,(x,y),(x+w,y+h),color,2)
            cv2.circle(f,(cx,cy),5,[0,0,0],thickness=-1)
    return cx, cy

def cmp_contours(contours, target):
    biggest_area = biggest_contour(contours)[1]
    bingos = []
    if (contours):
        for cnt in contours:
            if (cv2.contourArea(cnt) > biggest_area/4):
                diff = cv2.matchShapes(cnt, target, cv2.cv.CV_CONTOURS_MATCH_I3, 0.0)
                if (diff < 0.3):
                    bingos.append(cnt)
    for i in range(4):
        bingos.append(None)
    return bingos

def marker_contours(filename):
    marker = cv2.imread(filename, 0)
    ret, thresh = cv2.threshold(marker, 127, 255,0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    return contours[0]

def getCorners(coordinates, width, height):
    topleft = (-1, -1)
    topright = (-1, -1)
    bottomleft = (-1, -1)
    bottomright = (-1, -1)
    for coord in coordinates:
        if coord[0] < width/2 and coord[1] < height/2:
            topleft = coord
        elif coord[0] >= width/2 and coord[1] < height/2:
            topright = coord
        elif coord[0] < width/2 and coord[1] >= height/2:
            bottomleft = coord
        elif coord[0] >= width/2 and coord[1] >= height/2:
            bottomright = coord

    return topleft, topright, bottomleft, bottomright

def posConv(pos, tl, tr, bl, br, width, height, hand):
    x, y = 0,0
    if (hand):
        if(tr[0] > 0 and bl[0] > 0):
            realw = tr[0] - bl[0]
            realh = bl[1] - tr[1]
            x = int((width * (pos[0] - bl[0]))/realw)
            y = int((height * (pos[1] - tr[1]))/realh)
        elif(tl[0] > 0 and br[0] > 0):
            realw = br[0] - tl[0]
            realh = br[1] - tl[1]
            x = int((width * (pos[0] - tl[0]))/realw)
            y = int((height * (pos[1] - tl[1]))/realh)
    else:
        if(tl[0] > 0 and br[0] > 0):
            realw = br[0] - tl[0]
            realh = br[1] - tl[1]
            x = int((width * (pos[0] - tl[0]))/realw)
            y = int((height * (pos[1] - tl[1]))/realh)
        elif(tr[0] > 0 and bl[0] > 0):
            realw = tr[0] - bl[0]
            realh = bl[1] - tr[1]
            x = int((width * (pos[0] - bl[0]))/realw)
            y = int((height * (pos[1] - tr[1]))/realh)

    return x, y

def nothing(x):
    pass

class Window(QtGui.QWidget):

    thickness = 1
    pause = True
    col = QtGui.QColor(0, 0, 0)
    backcol = QtGui.QColor(255, 255, 255)
    flip = True
    save = False
    fname = ""
    tracker = [20, 100, 100,  40, 255, 255]
    hand = True

    def __init__(self):
        super(Window, self).__init__()
        self.initUI()

    def initUI(self):

        #RESTART BUTTON
        self.restartButton = QtGui.QPushButton('Restart', self)
        self.restartButton.clicked.connect(self.handleRestartButton)
        self.restartButton.move(20, 10)

        #PAUSE BUTTON
        self.pauseButton = QtGui.QPushButton('Unpause', self)
        self.pauseButton.clicked.connect(self.handlePauseButton)
        self.pauseButton.move(20, 40)

        #FLIP BUTTON
        self.flipButton = QtGui.QPushButton('Flip camera', self)
        self.flipButton.clicked.connect(self.handleFlipButton)
        self.flipButton.move(20, 70)

        #HAND BUTTON
        self.handButton = QtGui.QPushButton('Right-handed', self)
        self.handButton.clicked.connect(self.handleHandButton)
        self.handButton.move(20, 100)

        #LINE COLOR SELECTION
        self.colorButton = QtGui.QPushButton('Select color', self)
        self.colorButton.move(20, 130)
        self.colorButton.clicked.connect(self.showDialog)

        self.frm = QtGui.QFrame(self)
        self.frm.setStyleSheet("QWidget { background-color: %s }"
            % self.col.name())
        self.frm.setGeometry(130, 130, 50, 20)

        #BACKGROUND COLOR SELECTOR
        self.backgroundButton = QtGui.QPushButton('Select background', self)
        self.backgroundButton.move(20, 160)
        self.backgroundButton.clicked.connect(self.showBackgroundDialog)

        self.frmback = QtGui.QFrame(self)
        self.frmback.setStyleSheet("QWidget { background-color: %s }"
            % self.backcol.name())
        self.frmback.setGeometry(130, 160, 50, 20)

        #THICKNESS SELECTOR
        self.thicknessSlider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.thicknessSlider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.thicknessSlider.setMinimum(1)
        self.thicknessSlider.setMaximum(40)
        self.thicknessSlider.setGeometry(20, 190, 100, 30)
        self.thicknessSlider.valueChanged[int].connect(self.handleThicknessSlider)

        self.thicknessLabel = QtGui.QLabel(self)
        self.thicknessLabel.setGeometry(130, 190, 80, 30)
        self.thicknessLabel.setText("Thickness: "+str(self.thickness))

        #SAVE BUTTON
        self.saveButton = QtGui.QPushButton('Save', self)
        self.saveButton.move(20, 230)
        self.saveButton.clicked.connect(self.showSaveDialog)

        #WINDOW CONFIGURATION
        self.setGeometry(300, 300, 260, 260)
        self.setWindowTitle('Control')
        self.show()

    def showDialog(self):
        self.col = QtGui.QColorDialog.getColor()
        if self.col.isValid():
            self.frm.setStyleSheet("QWidget { background-color: %s }"
                % self.col.name())

    def showBackgroundDialog(self):
        self.backcol = QtGui.QColorDialog.getColor()
        if self.backcol.isValid():
            self.frmback.setStyleSheet("QWidget { background-color: %s }"
                % self.backcol.name())

    def showSaveDialog(self):
        self.fname = QtGui.QFileDialog.getSaveFileName(self, 'Save file', '/draft.png')
        self.save = True

    def getFileName(self):
        return str(self.fname)

    def getColor(self):
        return self.col.getRgb()

    def getBackgroundColor(self):
        return self.backcol.getRgb()

    def handlePauseButton(self):
        self.pause = not self.pause
        self.backgroundButton.setEnabled(False)
        self.handButton.setEnabled(False)
        if (self.pause):
            self.pauseButton.setText("Unpause")
        else:
            self.pauseButton.setText("Pause")

    def handleRestartButton(self):
        self.pause = True
        self.pauseButton.setText("Unpause")
        self.backgroundButton.setEnabled(True)
        self.handButton.setEnabled(True)

    def handleFlipButton(self):
        self.flip = not self.flip

    def handleThicknessSlider(self, value):
        self.thickness = value
        self.thicknessLabel.setText("Thickness: "+str(value))

    def handleHandButton(self):
        self.hand = not self.hand
        if(self.hand):
            self.handButton.setText("Right-handed")
        else:
            self.handButton.setText("Left-handed")

    def getThickness(self):
        return self.thickness

def main():

    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()

    colors = [[255,0,0],
              [0,255,0],
              [0,0,255],
              [0,0,0],
              [255,255,0],
              [255,0,255],
              [0,255,255],
              [255,255,255]]

    marker = marker_contours('squaremask.jpg')
    print(marker)

    c = cv2.VideoCapture(666)
    c = cv2.VideoCapture(0)
    width,height = c.get(3),c.get(4)
    print "Frame width and height : ", width, height

    #canvas = np.zeros((c.get(4),c.get(3),3), np.uint8)
    canvas = np.zeros((594,420,3), np.uint8)
    r = window.getBackgroundColor()[0]
    g = window.getBackgroundColor()[1]
    b = window.getBackgroundColor()[2]
    canvas[:] = (b,g,r)      # (B, G, R)

    points = []

    time.sleep(1) # delays for 1 second

    while(True):

        _,f = c.read()
        if (window.flip):
            f = cv2.flip(f,-1)
        blur = cv2.medianBlur(f,5)
        hsv = cv2.cvtColor(blur,cv2.COLOR_BGR2HSV)
        grayscale = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
        codes = cv2.adaptiveThreshold(grayscale, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 7, 7)

        yellow = getthresholdedimg(hsv, window.tracker[0], window.tracker[1], window.tracker[2], window.tracker[3], window.tracker[4], window.tracker[5])
        ymask = getmask(yellow)
        ycontours,yhierarchy = cv2.findContours(ymask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        cntcodes, codesh = cv2.findContours(codes, cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        ycnt = biggest_contour(ycontours)[0]

        #Draw quadrant lines
        cv2.line(f, (int(width/2),0), (int(width/2),int(height)), [0,0,0], 1)
        cv2.line(f, (0, int(height/2)), (int(width),int(height/2)), [0,0,0], 1)

        if(cntcodes):
            coord = []
            ci = 0
            for square in cmp_contours(cntcodes, marker):
                ax, ay = draw_square(square, f, colors[ci])
                if(ax > 0 and ay > 0):
                    #cv2.putText(f, "("+str(ax)+","+str(ay)+")", (ax,ay), cv2.FONT_HERSHEY_COMPLEX, 0.7, colors[ci], 2)
                    coord.append((ax,ay))
                    ci = ci + 1
                    if (ci > len(colors) - 1):
                        ci = 0

            #Finds the corners
            topleft, topright, bottomleft, bottomright = getCorners(coord, width, height)
            cv2.putText(f, "TOP LEFT", topleft, cv2.FONT_HERSHEY_COMPLEX, 0.5, [0,0,200], 2)
            cv2.putText(f, "TOP RIGHT", topright, cv2.FONT_HERSHEY_COMPLEX, 0.5, [0,0,200], 2)
            cv2.putText(f, "BOTTOM LEFT", bottomleft, cv2.FONT_HERSHEY_COMPLEX, 0.5, [0,0,200], 2)
            cv2.putText(f, "BOTTOM RIGHT", bottomright, cv2.FONT_HERSHEY_COMPLEX, 0.5, [0,0,200], 2)

            inside = False
            if(ycontours):
                cx, cy = draw_square(ycnt, f, [0, 0, 255])
                if (cx > 0 and cy > 0 and
                    ((topleft[0] > 0 and topleft[1] > 0 and bottomright[0] > 0 and bottomright[1] > 0) or
                    (bottomleft[0] > 0 and bottomleft[1] > 0 and topright[0] > 0 and topright[1] > 0)) and
                    ((cx > topleft[0] and cx < bottomright[0] and cy > topleft[1] and cy < bottomright[1]) or
                     (cx > bottomleft[0] and cx < topright[0] and cy > topright[1] and cy < bottomleft[1]))):

                    dx, dy = posConv((cx, cy), topleft, topright, bottomleft, bottomright, 420, 594, window.hand)

                    if not points:
                        points.append((dx, dy))
                        points.append((dx, dy))
                    else:
                        points.append((dx, dy))
                    inside = True

                    r = window.getColor()[0]
                    g = window.getColor()[1]
                    b = window.getColor()[2]
                    t = window.getThickness()
                    paused = window.pause

                    if(paused == 1):
                        cv2.putText(f, "| |", (int(width/2),int(height/2)), cv2.FONT_HERSHEY_COMPLEX, 1.0, [0,0,0], 5)
                    else:
                        cv2.line(canvas, points[len(points)-2], points[len(points)-1], [b,g,r], t)
                    cv2.putText(f, "("+str(cx)+","+str(cy)+")", (cx,cy), cv2.FONT_HERSHEY_COMPLEX, 0.7, [0,0,0], 2)
                else:
                    cv2.putText(f, "| |", (int(width/2),int(height/2)), cv2.FONT_HERSHEY_COMPLEX, 1.0, [0,0,0], 5)
            else:
                cv2.putText(f, "| |", (int(width/2),int(height/2)), cv2.FONT_HERSHEY_COMPLEX, 1.0, [0,0,0], 5)

            #Prints the edges of the painting area
            if(topleft[0] > 0):
                if(topright[0] > 0):
                    cv2.line(f, topleft, topright, [0,0,0], 2)
                if(bottomleft[0] > 0):
                    cv2.line(f, bottomleft, topleft, [0,0,0], 2)
            if(bottomright[0] > 0):
                if(topright[0] > 0):
                    cv2.line(f, topright, bottomright, [0,0,0], 2)
                if(bottomleft[0] > 0):
                    cv2.line(f, bottomright, bottomleft, [0,0,0], 2)

            #Prints the tracker of the brush
            if(ycontours and inside):
                if(topleft[0] > 0):
                    cv2.line(f, topleft, (cx, cy), [90,60,90], 2)
                if(topright[0] > 0):
                    cv2.line(f, topright, (cx, cy), [90,60,90], 2)
                if(bottomleft[0] > 0):
                    cv2.line(f, bottomleft, (cx, cy), [90,60,90], 2)
                if(bottomright[0] > 0):
                    cv2.line(f, bottomright, (cx, cy), [90,60,90], 2)

        if(window.backgroundButton.isEnabled()):
            r = window.getBackgroundColor()[0]
            g = window.getBackgroundColor()[1]
            b = window.getBackgroundColor()[2]
            canvas[:] = (b,g,r)      # (B, G, R)

        if(window.save):
            cv2.imwrite(window.getFileName(), canvas)
            window.save = False

        cv2.imshow('Virtual Tablet',f)
        cv2.imshow('Canvas',canvas)
        #cv2.imshow('Markers',codes)
        #cv2.imshow('Mask', yellow)

        if cv2.waitKey(25) == 27:
            break

    cv2.destroyAllWindows()
    c.release()

if __name__ == '__main__':
    main()