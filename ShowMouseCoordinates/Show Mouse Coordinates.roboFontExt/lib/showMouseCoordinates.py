#coding=utf-8
"""
SHOW MOUSE COORDINATES
2013-04-16 DJR

In the current glyph window, this extension will provide a readout of information about the mouse: its current position, how far it has been dragged, the dragging angle, and the dragging distance. Installing this extension will activate it; it doesn’t appear in menus.</p>

Theoretically it should work alongside any tool: edit, pen, knife, measure, etc. For some reason I have been getting weird results with the Shape Tool though.</p>

Released under MIT license.

## Future improvements?

- Adjust readout position when window is resized?
- Remove display when in preview mode?
- Add info relative to a given reference point? Perhaps it could look for an anchor called "reference" and use that?
- Detect when rulers are on? Too complicated, probably...

"""

from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.events import addObserver, removeObserver
import math

class ShowMouseCoordinatesTextBox(TextBox):
    """
    A vanilla text box with some goodies about the mouse.
    """
    def __init__(self, *args, **kwargs):
        super(ShowMouseCoordinatesTextBox, self).__init__(*args, **kwargs)
        addObserver(self, "mouseMoved", "mouseMoved")
        addObserver(self, "mouseDragged", "mouseDragged")
        addObserver(self, "mouseUp", "mouseUp")
    
    def mouseMoved(self, info):
        point = info["point"]
        text = u"⌖ %.0f %.0f" % (point.x, point.y)
        self.set(text)

    def mouseDragged(self, info):
        point = info["point"]
        positionSymbol = unichr(8982)
        deltaPoint = info["delta"]
        angle = math.degrees(math.atan2(deltaPoint.y, deltaPoint.x))
        distance = math.hypot(deltaPoint.x, deltaPoint.y)
        text = u"⌖ %.0f %.0f  Δ %.0f %.0f  ∠ %.2f°  ↔ %.0f" % (point.x, point.y, deltaPoint.x, deltaPoint.y, angle, distance)
        self.set(text)
        
    def mouseUp(self, info):
        point = info["point"]
        text = u"⌖ %.0f %.0f" % (point.x, point.y)
        self.set(text)

    def _breakCycles(self):
        super(ShowMouseCoordinatesTextBox, self)._breakCycles()
        removeObserver(self, "mouseMoved")
        removeObserver(self, "mouseDragged")
        removeObserver(self, "mouseUp")

class ShowMouseCoordinates(BaseWindowController):
    """
    Attach a vanilla text box to a window.
    """
    def __init__(self):
        addObserver(self, "glyphWindowDidOpen", "glyphWindowDidOpen")

    def glyphWindowDidOpen(self, info):
        window = info["window"]
        vanillaView = ShowMouseCoordinatesTextBox((20, 10, -20, 22), "", alignment="left", sizeStyle="mini")
        #vanillaView = ShowMouseCoordinatesTextBox((-300, -40, -20, 22), "", alignment="right", sizeStyle="small")
        superview = window.w.editScrollView.getNSScrollView()
        view = vanillaView.getNSTextField()
        frame = superview.frame()
        vanillaView._setFrame(frame)
        superview.addSubview_(view)
        
    def windowCloseCallback(self, sender):
        super(ShowMouseCoordinatesTextBox, self).windowCloseCallback(sender)
        removeObserver(self, "glyphWindowDidOpen")

ShowMouseCoordinates()