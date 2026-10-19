import sys
import os
import argparse
import pandas as pd
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QPixmap, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QSlider,
    QHBoxLayout, QVBoxLayout, QGridLayout
)


class PictureCanvas(QWidget):
    '''
    Designed to allow the display and replacement of small pictures on screen
    (like a D3 canvas)
    url is a location on disk
    '''
    def __init__(self, url, width=800, height=533, parent=None):
        super().__init__(parent)
        self.set_pixmap(url, width, height)

    def set_pixmap(self, url, width=800, height=533):
        self.setGeometry(0, 0, width, height)
        self.layout = QVBoxLayout()
        self.label = QLabel(self)
        self.pixmap = QPixmap(url)
        self.label.setPixmap(self.pixmap)
        self.label.setScaledContents(True)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def new_pixmap(self, url, width=800, height=533):
        self.setGeometry(0, 0, width, height)
        new_pixmap = QPixmap(url)
        self.label.setPixmap(new_pixmap)        


class StepThroughApp(QWidget):
    '''
    Runs the navigation system, allowing button nav and WASD (and Q for back button)
    '''
    def __init__(self, node):
        super().__init__()
        self.basedir = './'
        # allow the script to be in a different location than the target images and node description
        if os.path.isfile(self.basedir + 'basedir.txt'):
            with open(self.basedir + 'basedir.txt', 'r') as fh:
                self.basedir = fh.readline().rstrip()
        # image numbers are integers.  That also means no images < 1000
        self.picList = pd.read_csv(f'{self.basedir}botanicalstep.csv', low_memory=False, dtype={'Node': 'Int64', 'Forward': 'Int64', 'Back': 'Int64', 'Left': 'Int64', 'Right': 'Int64'}).fillna(0)
        self.locn = 0
        self.prevchain = [0]
        self.node = self.picList.at[self.locn, "Node"]
        # don't worry about things that aren't int's, just ignore them
        if isinstance(node, str) and node.isdigit():
            self.findnode(int(node))

        self.setWindowTitle(f"Botanical Gardens Path Walkthrough -- Node {self.node}")

        # set the starting image
        self.canvas = PictureCanvas(f"{self.basedir}Botanical_Garden_StepThrough/IMG_{self.node}.jpg", width=800, height=533)

        self.buttons_layout = QHBoxLayout()
        self.btn = {}
        self.buttons_setup()

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.canvas)
        self.main_layout.addLayout(self.buttons_layout)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setLayout(self.main_layout)

    def reload(self):
        '''
        Allow re-reading the node list (not advertised)
        '''
        print("reload")
        self.picList = pd.read_csv(f'{self.basedir}botanicalstep.csv', low_memory=False, dtype={'Node': 'Int64', 'Forward': 'Int64', 'Back': 'Int64', 'Left': 'Int64', 'Right': 'Int64'}).fillna(0)
        # move to where you currently are, to reset the buttons, in case they changed
        self.set_movement('Node')

    def keyPressEvent(self, event: QKeyEvent):
        '''
        Overrides a Qt function.  Allows WASD navigation.
        '''
        if event.key() == Qt.Key.Key_W:
            self.set_movement('Forward')
        if event.key() == Qt.Key.Key_Q:
            self.set_movement('Previous')
        if event.key() == Qt.Key.Key_S:
            self.set_movement('Back')
        if event.key() == Qt.Key.Key_A:
            self.set_movement('Left')
        if event.key() == Qt.Key.Key_D:
            self.set_movement('Right') 
        if event.key() == Qt.Key.Key_R:
            self.reload()                                               

    def buttons_setup(self):
        '''
        Set up the buttons.  Disable any not available at this node.
        '''
        mybuttons = ['Previous', 'Left', 'Forward', 'Back', 'Right']
        for name in mybuttons:
            # need different treatment if the button doesn't already exist
            firstround = False
            if name not in self.btn:
                self.btn[name] = QPushButton(name)
                firstround = True
            # connect to the movement function
            self.btn[name].clicked.connect(lambda _, col=name: self.set_movement(col))
            # clear any previous disablement
            self.btn[name].setEnabled(True)
            # now disable if it's not used for this node
            if name != 'Previous' and self.picList.at[self.locn, name] == 0:
                self.btn[name].setEnabled(False)
            if name == 'Previous' and len(self.prevchain) < 2:
                self.btn[name].setEnabled(False)
            if firstround:
                self.buttons_layout.addWidget(self.btn[name])

    def findnode(self, newnode):
        '''
        Given the self.node, find the row in the dataframe (the self.locn) that represents that node
        Leave self.foundit false if the node doesn't match anything
        '''
        self.foundit = False
        for index, row in self.picList.iterrows():
            if row['Node'] == newnode:
                self.prevchain.append(self.locn)
                self.locn = index
                self.node = newnode
                self.foundit = True
                break

    def set_movement(self, direction):
        '''
        Switch nodes at the user's request
        Return silently for invalid requests
        '''
        # avoid double tapping
        if direction == 'Previous' or (self.picList.at[self.locn, direction] > 0 and direction != 'Node'):
            self.btn[direction].clicked.disconnect()
        if direction == 'Previous':
            if len(self.prevchain) < 2:
                return
            self.locn = self.prevchain[-1]
            self.prevchain = self.prevchain[:-1]
            self.node = self.picList.at[self.locn, 'Node']
        elif self.picList.at[self.locn, direction] > 0:
            newnode = self.picList.at[self.locn, direction]
            self.findnode(newnode)
            if not self.foundit:
                return
        else:
            return
        # reflect the new node
        if direction != 'Node':
            self.canvas.new_pixmap(f"{self.basedir}Botanical_Garden_StepThrough/IMG_{self.node}.jpg")
        self.buttons_setup()
        self.setWindowTitle(f"Botanical Gardens Path Walkthrough -- Node {self.node}")


def main():
    app = QApplication(sys.argv)
    # allow the user to start at a different node than start
    parser = argparse.ArgumentParser()
    parser.add_argument("-node", help="start at a non-default node")
    args = parser.parse_args()
    w = StepThroughApp(args.node)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
