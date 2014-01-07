# Nina's customized version – also gives width/height of bounding box when subdiv=1 selected
# eh plus a different color ^^

from mojo.events import BaseEventTool, installTool, EditingTool
from AppKit import *
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.drawingTools import *
from mojo.extensions import ExtensionBundle
from vanilla import *

bundle = ExtensionBundle("BoundingTool")
toolbarIcon = bundle.getResourceImage("boundingtool")
toolbarIcon.setSize_((16, 16))

class BoundingTool(EditingTool, BaseWindowController):
    u"""
    Shows the bounding box and useful divisions.
    """
    color = (1, 0, .2)
    alpha = 1
    divisionsStringList = ['1', '2', '3', '4']
    divisionsList = [1, 2, 3, 4]
    
    def getToolbarTip(self):
        return "bounding edit"
        
    def getToolbarIcon(self):
        return toolbarIcon

    def getSelectedBox(self):
        g = self.getGlyph()
        hasSelection = False
        if g is not None:
            xmin = 9999999999
            xmax = -9999999999
            ymin = 9999999999
            ymax = -9999999999
            for p in g.selection:
                hasSelection = True
                if p.x < xmin:
                    xmin = p.x
                if p.x > xmax:
                    xmax = p.x
                if p.y < ymin:
                    ymin = p.y
                if p.y > ymax:
                    ymax = p.y
            for c in g.components:
                if c.selected and c.box:
                    hasSelection = True
                    cxmin, cymin, cxmax, cymax = c.box
                    if cxmin < xmin:
                        xmin = cxmin
                    if cxmax > xmax:
                        xmax = cxmax
                    if cymin < ymin:
                        ymin = cymin
                    if cymax > ymax:
                        ymax = cymax
        if hasSelection:
            return xmin, ymin, xmax, ymax
        elif g.box:
            return g.box
    
    def drawBackground(self, scale):
        g = self.getGlyph()
        if self.w.viewOptions.get() == 0:
            selectedBox = self.getSelectedBox()
        else:
            selectedBox = g.box

        if selectedBox:
            xmin, ymin, xmax, ymax = selectedBox
            width = xmax - xmin
            height = ymax - ymin
            # draw a rectangle around the box    
            fill(1, 1, 1, 0)
            stroke(self.color[0], self.color[1], self.color[2], self.alpha)
            dashLine(1)
            rect(xmin, ymin, width, height)
            # calculate the number of x and y divisions
            divisionsX = self.divisionsList[self.w.divisionsRadioX.get()]
            divisionsY = self.divisionsList[self.w.divisionsRadioY.get()]
            # draw a bit beyond the bbox
            extra = 20
            offset = xmin
            advance = float(width) / divisionsX
            for i in range(divisionsX-1): #subdivisions
                xmid = offset + advance
                offset += advance
                newPath()
                moveTo((xmid, ymin - extra))
                lineTo((xmid, ymax + extra))
                closePath()
                drawPath()
                fontSize(9)
                fill(self.color[0], self.color[1], self.color[2], self.alpha)
                text(str(int(xmid)), (xmid + 4, ymin - extra))
            if divisionsX == 1: # width of bounding box
                xmid = offset + float(width) / 2
                fontSize(11)
                fill(self.color[0], self.color[1], self.color[2], self.alpha)
                text("w: "+str(width), (xmid-20, ymax + 10))             
            #if self.w.viewY.get():
            #fontSize(8)
            #fill(self.color[0], self.color[1], self.color[2], self.alpha)
            #text(str(int(ymax)), (xmin - extra, ymax))
            offset = ymin
            advance = float(height) / divisionsY
            for i in range(divisionsY-1): # subdivisions
                ymid = offset + advance
                offset += advance
                newPath()
                moveTo((xmin - extra, ymid))
                lineTo((xmax + extra, ymid))
                closePath()
                drawPath()
                fontSize(9)
                fill(self.color[0], self.color[1], self.color[2], self.alpha)
                text(str(int(ymid)), (xmin - extra, ymid + 4)) 
            if divisionsY == 1: # height of bounding box
                ymid = offset + float(height) / 2
                fontSize(12)
                fill(self.color[0], self.color[1], self.color[2], self.alpha)
                text("h: "+str(height), (xmax+10, ymid-10))      
                
    def becomeActive(self):
        """
        Boot up the dialog.
        """
        self.w = FloatingWindow((260, 130), "Bounding Options", minSize=(100, 100), closable=False)

        self.w.viewOptions = RadioGroup((10, 10, 220, 20),
                                        ['Selection', 'All'],
                                        callback=self.callback, isVertical=False)
        self.w.viewOptions.set(0)

        self.w.xLabel = TextBox((10, 40, 100, 20), "X Divisions")
        #self.w.viewX = CheckBox((10, 40, 100, 20), "X Divisions",
        #                           callback=self.callback, value=True)
        self.w.divisionsRadioX = RadioGroup((110, 40, 140, 20),
                                        self.divisionsStringList,
                                        callback=self.callback, isVertical=False)
        self.w.divisionsRadioX.set(0)

        self.w.yLabel = TextBox((10, 70, 100, 20), "Y Divisions")
        #self.w.viewY = CheckBox((10, 70, 100, 20), "Y Divisions",
        #                           callback=self.callback, value=True)
        self.w.divisionsRadioY = RadioGroup((110, 70, 140, 20),
                                        self.divisionsStringList,
                                        callback=self.callback, isVertical=False)
        self.w.divisionsRadioY.set(0)

        self.w.drawGuidesButton = Button((10, 100, 90, 20), 'Div Guides', callback=self.drawDivGuides)
        self.w.drawBoxGuidesButton = Button((120, 100, 90, 20), 'Box Guides', callback=self.drawBoxGuides)
            

        self.setUpBaseWindowBehavior()
        self.w.open()
        
    def becomeInactive(self):
        """
        Remove the dialog when the tool is inactive.
        """
        self.windowCloseCallback(None)
        self.w.close()
        
    def callback(self, sender):
        self.refreshView()

    def drawDivGuides(self, sender):
        """
        Draw guidelines for the current divisions.
        """
        g = self.getGlyph()
        if self.w.viewOptions.get() == 0:
            selectedBox = self.getSelectedBox()
        else:
            selectedBox = g.box
        if selectedBox:
            g.prepareUndo()
            xmin, ymin, xmax, ymax = selectedBox
            width = xmax - xmin
            height = ymax - ymin
            divisionsX = self.divisionsList[self.w.divisionsRadioX.get()]
            divisionsY = self.divisionsList[self.w.divisionsRadioY.get()]
            #if self.w.viewX.get():
            offset = xmin
            advance = float(width) / divisionsX
            for i in range(divisionsX-1):
                xmid = offset + advance
                g.addGuide((xmid, ymin), 90)
                offset += advance
            #if self.w.viewY.get():
            offset = ymin
            advance = float(height) / divisionsY
            for i in range(divisionsY-1):
                ymid = offset + advance
                g.addGuide((xmin, ymid), 0)
                offset += advance
            g.performUndo()
                    
    def drawBoxGuides(self, sender):
        """
        Draw guidelines for the current box.
        """
        g = self.getGlyph()
        selectedBox = self.getSelectedBox()
        if selectedBox:
            g.prepareUndo()
            xmin, ymin, xmax, ymax = selectedBox
            #if self.w.viewX.get():
            g.addGuide((xmin, ymin), 90)
            g.addGuide((xmax, ymax), 90)
            #if self.w.viewY.get():
            g.addGuide((xmin, ymin), 0)
            g.addGuide((xmax, ymax), 0)
            g.performUndo()


    
installTool(BoundingTool())