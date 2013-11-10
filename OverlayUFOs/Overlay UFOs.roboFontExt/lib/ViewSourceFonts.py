from AppKit import NSColor
from mojo.drawingTools import save, restore, fill, strokeWidth, translate
from mojo.events import addObserver, removeObserver
#from time import time

from MojoDrawingToolsPen import MojoDrawingToolsPen

class ViewSourceFonts(object):
    def __init__(self):
        self.addObserver()
        self.cacheCopy = None
        self.alignment = 0

    def addObserver(self):
        addObserver(self, "drawSourceFonts", "drawBackground")
        #addObserver(self, "drawSourceFonts", "drawInactive")

    def removeObserver(self):
        removeObserver(self, "drawBackground")
        #removeObserver(self, "drawInactive")

    def getSources(self):
        return AllFonts()
    
    def drawSourceFonts(self, info):
        #start_time = time()
        glyph = info["glyph"]
        if glyph is not None:
            name = glyph.name
        
            save()
            self.setStroke()
            self.setFill()
                
            for source in self.getSources():
                if source != glyph.getParent():
                    if name in source.keys():
                        sourceGlyph = source[name]
                        sourceFont = sourceGlyph.getParent()
                        if self.alignment == 1:
                            translate(round((glyph.width/2.0 - sourceGlyph.width/2.0)/2.0), 0)
                        elif self.alignment == 2:
                            translate(round(glyph.width-sourceGlyph.width), 0)
                        mPen = MojoDrawingToolsPen(sourceGlyph, sourceFont)
                        sourceGlyph.draw(mPen)
                        mPen.draw()
            restore()
        #stop_time = time()
        #print "Draw: %.4f seconds." % (stop_time - start_time)

    def setStroke(self, value=.5):
        strokeWidth(value)
    
    def setFill(self, rgba=(.2, 0, .2, .2)):
        r, g, b, a = rgba
        fill(r, g, b, a)
    
    def getColor(self):
        return NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, .5, .2)