from mojo.events import BaseEventTool, installTool
from AppKit import *
from mojo.events import addObserver, removeObserver
from lib.eventTools.eventManager import getActiveEventTool


fontSize = 9
bgColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, .2)
textAttributes = {
                  NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
                  NSForegroundColorAttributeName : NSColor.whiteColor()
                  }

class ShowDelta(object):
    def __init__(self):
        addObserver(self, "_mouseDragged", "mouseDragged")
        addObserver(self, "_mouseUp", "mouseUp")
        addObserver(self, "_draw", "draw")
        self.drawAtPoint = None

    def _mouseDragged(self, info):
        self.x = round(info['delta'].x)
        self.y = round(info['delta'].y)
        self.drawAtPoint = (info['point'].x+40, info['point'].y+fontSize)

    def _mouseUp(self, info):
        self.drawAtPoint = None
    
    def _draw(self, info):
        currentTool = getActiveEventTool()
        view = currentTool.getNSView()
        if self.drawAtPoint:
            view._drawTextAtPoint("%i %i" %(self.x, self.y), textAttributes, self.drawAtPoint, yOffset=0, backgroundColor=bgColor, drawBackground=True, roundBackground=True)
        
ShowDelta()