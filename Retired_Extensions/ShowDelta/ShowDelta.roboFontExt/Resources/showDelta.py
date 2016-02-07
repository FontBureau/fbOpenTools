from mojo.events import BaseEventTool, installTool
from AppKit import *
from mojo.events import addObserver, removeObserver
from lib.eventTools.eventManager import getActiveEventTool


fontSize = 9
textAttributes = {
                  NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
                  NSForegroundColorAttributeName : NSColor.grayColor()
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
        self.drawAtPoint = (info['point'].x+10, info['point'].y + 10)

    def _mouseUp(self, info):
        self.drawAtPoint = None
    
    def _draw(self, info):
        currentTool = getActiveEventTool()
        view = currentTool.getNSView()
        if self.drawAtPoint:
            view._drawTextAtPoint("%i %i" %(self.x, self.y), textAttributes, self.drawAtPoint, yOffset=fontSize)
        else:
            print 'mouse is up'
        
ShowDelta()