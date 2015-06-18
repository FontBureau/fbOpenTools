# -*- coding: UTF-8 -*-
# -----------------------------------------------------------------------------
#     The MIT License
#     http://opensource.org/licenses/MIT
#
#     Copyright (c) 2015+ Font Bureau
#
#    Permission is hereby granted, free of charge, to any person obtaining a copy
#    of this software and associated documentation files (the "Software"), to deal
#    in the Software without restriction, including without limitation the rights
#    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the Software is
#    furnished to do so, subject to the following conditions:
#    
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#    
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#    THE SOFTWARE.
#    
# -----------------------------------------------------------------------------
#
#    OverlayUFOs2.py

from AppKit import NSTextFieldCell, NSSmallControlSize, NSFont, NSColor, NSBezierPath, NSMakeRect, NSNormalWindowLevel, NSFloatingWindowLevel
from vanilla import Button, CheckBox, ColorWell, EditText, FloatingWindow, List, RadioGroup, TextBox
from defconAppKit.tools.textSplitter import splitText
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.drawingTools import save, restore, translate, scale
from mojo.events import addObserver, removeObserver
from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor
from mojo.UI import UpdateCurrentGlyphView
from lib.tools.defaults import getDefault
from lib.tools.drawing import strokePixelPath
from os.path import commonprefix

def SmallTextListCell(editable=False):
    cell = NSTextFieldCell.alloc().init()
    size = NSSmallControlSize
    cell.setControlSize_(size)
    font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(size))
    cell.setFont_(font)
    cell.setEditable_(editable)
    return cell

class OverlayUFOs(BaseWindowController):
    
    DEFAULTKEY = "com.fontbureau.overlayUFO"
    DEFAULTKEY_DRAW = "%s.draw" % DEFAULTKEY
    DEFAULTKEY_FILL = "%s.fill" % DEFAULTKEY
    DEFAULTKEY_FILLCOLOR = "%s.fillColor" % DEFAULTKEY
    DEFAULTKEY_STROKE = "%s.stroke" % DEFAULTKEY
    DEFAULTKEY_STROKECOLOR = "%s.strokeColor" % DEFAULTKEY
    DEFAULTKEY_POINTS = "%s.points" % DEFAULTKEY
    DEFAULTKEY_POINTSCOLOR = "%s.pointsColor" % DEFAULTKEY
    DEFAULTKEY_ALIGNMENT = "%s.alignment" % DEFAULTKEY
    DEFAULTKEY_KERNING = "%s.kerning" % DEFAULTKEY
    DEFAULTKEY_FLOATING = "%s.floating" % DEFAULTKEY
    
    FALLBACK_FILLCOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0.3, 1, .1)
    FALLBACK_STROKECOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0.3, 1, .5)
    FALLBACK_POINTSCOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0.3, 1, .5)
    
    def getListDescriptor(self): 
        return [
            dict(title="Status", key="status", width=10, cell=SmallTextListCell(), editable=False), 
            dict(title="Name", key="name", width=230, cell=SmallTextListCell(), editable=False), 
        ]
    
    def __init__(self):
        
        # Preferences
        self._drawing = getExtensionDefault(self.DEFAULTKEY_DRAW, True)
        self._fill = getExtensionDefault(self.DEFAULTKEY_FILL, True)
        self._stroke = getExtensionDefault(self.DEFAULTKEY_STROKE, True)
        self._points = getExtensionDefault(self.DEFAULTKEY_POINTS, True)
        
        self._fillColor = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)
        self._strokeColor = getExtensionDefaultColor(self.DEFAULTKEY_STROKECOLOR, self.FALLBACK_STROKECOLOR)
        self._pointsColor = getExtensionDefaultColor(self.DEFAULTKEY_POINTSCOLOR, self.FALLBACK_POINTSCOLOR)
        
        self._alignment = getExtensionDefault(self.DEFAULTKEY_ALIGNMENT, 0)
        self._kerning = getExtensionDefault(self.DEFAULTKEY_KERNING, 1)
        self._floating = getExtensionDefault(self.DEFAULTKEY_FLOATING, 1)
        
        # User preferences
        self._onCurvePointsSize = getDefault("glyphViewOncurvePointsSize") # typo, should be: OnCurve
        self._offCurvePointsSize = getDefault("glyphViewOffCurvePointsSize")
        self._strokeWidth = getDefault("glyphViewStrokeWidth")
        
        w, h = 400, 195
        x = y = 10
        
        self.initAllFonts()
        
        self.w = FloatingWindow((w, h), "Overlay UFOs")
        self.w.draw = CheckBox((x, y, 95, 18), "Draw", callback=self.drawCallback, value=self._drawing, sizeStyle="small")
        x += 60
        self.w.fill = CheckBox((x, y, 95, 18), "Fill", callback=self.fillCallback, value=self._fill, sizeStyle="small")
        x += 40
        self.w.fillColor = ColorWell((x, y, 45, 20), callback=self.fillColorCallback, color=self._fillColor)
        x += 60
        self.w.stroke = CheckBox((x, y, 95, 18), "Stroke", callback=self.strokeCallback, value=self._stroke, sizeStyle="small")
        x += 60
        self.w.strokeColor = ColorWell((x, y, 45, 20), callback=self.strokeColorCallback, color=self._strokeColor)
        x += 60
        self.w.points = CheckBox((x, y, 95, 18), "Points", callback=self.pointsCallback, value=self._points, sizeStyle="small")
        x += 60
        self.w.pointsColor = ColorWell((x, y, 45, 20), callback=self.pointsColorCallback, color=self._pointsColor)
        x, y = 10, 40
        self.w.alignText = TextBox((x, y, 250, 15), "Alignment:", sizeStyle="small")
        y += 18
        self.w.alignment = RadioGroup((x, y, 80, 55), ['Left', 'Center', 'Right'], isVertical=True, callback=self.alignmentCallback, sizeStyle="small")
        self.w.alignment.set(self._alignment)
        y += 62
        self.w.kerning = CheckBox((x, y, 100, 10), "Show kerning", callback=self.kerningCallback, value=self._kerning, sizeStyle="mini")
        y += 18
        self.w.floating = CheckBox((x, y, 100, 10), "Floating Window", callback=self.floatingCallback, value=self._floating, sizeStyle="mini")
        y += 25
        self.w.resetDefaults = Button((x, y, 85, 14), "Reset settings", callback=self.resetSettingsCallback, sizeStyle="mini")
        x, y = 110, 40
        self.w.fontList = List((x, y, 240, 55), self.getFontItems(), 
            columnDescriptions=self.getListDescriptor(), showColumnTitles=False,
            selectionCallback=None, doubleClickCallback=self.fontListCallback,
            allowsMultipleSelection=True, allowsEmptySelection=True,
            drawVerticalLines=False, drawHorizontalLines=True,
            drawFocusRing=False, rowHeight=16
        )
        y += 55
        self.w.hiddenFontList = List((x, y, 240, 55), self.getHiddenFontItems(), 
            columnDescriptions=self.getListDescriptor(), showColumnTitles=False,
            selectionCallback=None, doubleClickCallback=self.hiddenFontListCallback,
            allowsMultipleSelection=True, allowsEmptySelection=True,
            drawVerticalLines=False, drawHorizontalLines=True,
            drawFocusRing=False, rowHeight=16
        )
        self._selectionChanging = False
        self.w.fontList.setSelection([]) # unselect
        y += 65
        self.w.contextLeft = EditText((x, y, 90, 20), callback=self.contextCallback, continuous=True, placeholder="Left", sizeStyle="small")
        self.w.contextCurrent = EditText((x+95, y, 50, 20), callback=self.contextCallback, continuous=True, placeholder="?", sizeStyle="small")
        self.w.contextRight = EditText((x+150, y, 90, 20), callback=self.contextCallback, continuous=True, placeholder="Right", sizeStyle="small")
        x, y = 360, 100
        self.w.addFonts = Button((x, y, 30, 20), "+", callback=self.addHiddenFontsCallback, sizeStyle="regular")
        y += 25
        self.w.removeFonts = Button((x, y, 30, 20), unichr(8722), callback=self.removeHiddenFontsCallback, sizeStyle="regular")
                
        # Observers
        addObserver(self, "fontDidOpen", "fontDidOpen")
        addObserver(self, "fontWillClose", "fontWillClose") # fontDidClose?
        addObserver(self, "draw", "drawInactive")
        addObserver(self, "draw", "draw")
        
        # Prepare and open window
        self.setWindowLevel()
        self.setUpBaseWindowBehavior()
        self.w.open()
    
    def setWindowLevel(self):
        if self._floating:
            self.w._window.setLevel_(NSFloatingWindowLevel)
        else:
            self.w._window.setLevel_(NSNormalWindowLevel)
            
    def windowCloseCallback(self, sender):
        removeObserver(self, "fontDidOpen")
        removeObserver(self, "fontWillClose")
        removeObserver(self, "drawInactive")
        removeObserver(self, "draw")
        self.updateView()
        super(OverlayUFOs, self).windowCloseCallback(sender)
    
    def updateView(self):
        UpdateCurrentGlyphView()
    
    def initAllFonts(self):
        fonts = []
        for font in AllFonts():
            fonts.append({"font": font, "status": u"•"})
        self.fonts = fonts
        self.hiddenFonts = []
            
    def getFontName(self, font):
        if font.document():
            name = font.document().displayName()
        else:
            name = font.fileName.split("/")[-1]
        return name
    
    def getHiddenFontItems(self):
        hiddenFonts = self.hiddenFonts
        hiddenFontItems = self.getItems(hiddenFonts)
        return hiddenFontItems
    
    def getFontItems(self):
        fonts = self.fonts
        fontItems = self.getItems(fonts)
        return fontItems
    
    def getItems(self, fonts):
        items = []
        uniqueNames = {}
        for f in fonts:
            font = f["font"]
            status = f["status"]
            path = font.path
            name = self.getFontName(font)
            if not uniqueNames.has_key(name):
                uniqueNames[name] = []
            uniqueNames[name].append(path)
            paths = uniqueNames[name]
            if len(paths) > 1:
                prefix = commonprefix(paths)
                if prefix:
                    suffix = " ...%s" % path[len(prefix):]
                else:
                    suffix = " %s" % path
                name += suffix
            items.append({"status": status, "name": name})
        return items
    
    def getActiveFonts(self):
        fonts = self.fonts + self.hiddenFonts
        activeFonts = []
        for font in fonts:
            if font["status"]:
                activeFonts.append(font["font"])
        return activeFonts
    
    def getContexts(self):
        return self.w.contextLeft.get(), self.w.contextCurrent.get(), self.w.contextRight.get()
    
    def getAlignment(self):
        index = self._alignment
        if index == 0:
            return 'left'
        elif index == 1:
            return 'center'
        elif index == 2:
            return 'right'
    
    def getKernValue(self, nakedFont, leftGlyph, rightGlyph):
        if not leftGlyph or not rightGlyph:
            return 0
        if not self._kerning:
            return 0
        return nakedFont.flatKerning.get((leftGlyph.name, rightGlyph.name)) or 0
    
    def draw(self, info):
        
        if not self._drawing:
            return
            
        glyph = info.get("glyph")
        drawingScale = info.get('scale')
        
        if glyph is None:
            return
            
        current = glyph.getParent()
        fonts = self.getActiveFonts()
        
        for font in fonts:
            
            nakedFont = font.naked()
            
            contextLeft, contextCurrent, contextRight = self.getContexts()
            contextLeft = splitText(contextLeft or '', nakedFont.unicodeData or '')
            contextLeft = [font[gname] for gname in contextLeft if gname in font.keys()]
            contextRight = splitText(contextRight or '', nakedFont.unicodeData or '')
            contextRight = [font[gname] for gname in contextRight if gname in font.keys()]
            contextCurrent = splitText(contextCurrent or '', nakedFont.unicodeData or '')
            if len(contextCurrent) > 0:
                contextCurrent = [font[gname] for gname in [contextCurrent[0]] if gname in font.keys()]
                if len(contextCurrent) > 0:
                    sourceGlyph = contextCurrent[0]
                else:
                    sourceGlyph = None
            elif glyph.name in font.keys():
                sourceGlyph = font[glyph.name]
                contextCurrent = [sourceGlyph]
            else:
                sourceGlyph = None
                contextCurrent = []
            
            save()
            
            self._fillColor.setFill()
            self._strokeColor.setStroke()
            scale(current.info.unitsPerEm/float(font.info.unitsPerEm))
            
            # Draw left context
            previousGlyph = sourceGlyph
            contextLeft.reverse()
            totalWidth = 0
            for i, cbGlyph in enumerate(contextLeft):
                kernValue = self.getKernValue(nakedFont, cbGlyph, previousGlyph) # right to left
                translate(-cbGlyph.width-kernValue, 0)
                totalWidth += cbGlyph.width + kernValue
                glyphBezierPath = cbGlyph.naked().getRepresentation("defconAppKit.NSBezierPath")
                if self._fill:
                    glyphBezierPath.fill()
                if self._stroke:
                    glyphBezierPath.setLineWidth_(self._strokeWidth*drawingScale)
                    strokePixelPath(glyphBezierPath)
                previousGlyph = cbGlyph
            translate(totalWidth, 0)
            
            # Draw current context or current glyph 
            if contextCurrent:
                previousGlyph = None
                alignment = self.getAlignment()
                if alignment == 'left':
                    offset = 0
                elif alignment == 'center':
                    offset = (glyph.width - contextCurrent[0].width)/2                                        
                elif alignment == 'right':
                    offset = glyph.width - contextCurrent[0].width                                     
                totalWidth = offset
                translate(totalWidth, 0)
            
            for i, cbGlyph in enumerate(contextCurrent):
                #if cbGlyph == glyph:
                #    continue # Don't show if is current glyph
                kernValue = self.getKernValue(nakedFont, previousGlyph, cbGlyph)
                translate(kernValue, 0)
                glyphBezierPath = cbGlyph.naked().getRepresentation("defconAppKit.NSBezierPath")
                if self._fill:
                    glyphBezierPath.fill()
                if self._stroke:
                    glyphBezierPath.setLineWidth_(self._strokeWidth*drawingScale)
                    strokePixelPath(glyphBezierPath)
                if self._points:
                    self.drawPoints(cbGlyph, info['scale'])
                translate(cbGlyph.width, 0)
                totalWidth += cbGlyph.width + kernValue
                previousGlyph = cbGlyph
            translate(-totalWidth, 0)
            
            # Draw right context
            translate(glyph.width)
            totalWidth = glyph.width
            for i, cbGlyph in enumerate(contextRight):
                kernValue = self.getKernValue(nakedFont, previousGlyph, cbGlyph)
                translate(kernValue, 0)
                glyphBezierPath = cbGlyph.naked().getRepresentation("defconAppKit.NSBezierPath")
                if self._fill:
                    glyphBezierPath.fill()
                if self._stroke:
                    glyphBezierPath.setLineWidth_(self._strokeWidth*drawingScale)
                    strokePixelPath(glyphBezierPath)
                translate(cbGlyph.width, 0)
                totalWidth += cbGlyph.width + kernValue
                previousGlyph = cbGlyph
                
            restore()
    
    def drawPoints(self, glyph, scale):
        save()
        _onCurveSize = self._onCurvePointsSize * scale
        _offCurveSize = self._offCurvePointsSize * scale
        _strokeWidth = self._strokeWidth * scale
        
        self._pointsColor.set()
        
        path = NSBezierPath.bezierPath()
        offCurveHandlesPath = NSBezierPath.bezierPath()
        pointsData = glyph.getRepresentation("doodle.OutlineInformation")
        
        for point1, point2 in pointsData["bezierHandles"]:
            offCurveHandlesPath.moveToPoint_(point1)
            offCurveHandlesPath.lineToPoint_(point2)

        for point in pointsData.get("offCurvePoints"):
            (x, y) = point["point"]
            path.appendBezierPathWithOvalInRect_(NSMakeRect(x - _offCurveSize, y - _offCurveSize, _offCurveSize * 2, _offCurveSize * 2))
            
        for point in pointsData.get("onCurvePoints"):
            (x, y) = point["point"]
            path.appendBezierPathWithRect_(NSMakeRect(x - _onCurveSize, y - _onCurveSize, _onCurveSize * 2, _onCurveSize * 2))
            
        path.fill()
        offCurveHandlesPath.setLineWidth_(_strokeWidth)
        strokePixelPath(offCurveHandlesPath)
        restore()

    def fontDidOpen(self, event):
        font = event["font"]
        self.fonts.append({"font": font, "status": u"•"})
        self.w.fontList.set(self.getFontItems())
        self.updateView()
    
    def fontWillClose(self, event):
        # not always working... try from path or name?
        closingFont = event["font"]
        for i, font in enumerate(self.fonts):
            if font["font"] == closingFont:
                del self.fonts[i]
                item = self.w.fontList.get()[i]
                self.w.fontList.remove(item)
                break
        self.updateView()
    
    def fontListCallback(self, sender):
        fonts = self.fonts
        self.listCallback(sender, fonts)

    def hiddenFontListCallback(self, sender):
        fonts = self.hiddenFonts
        self.listCallback(sender, fonts)
            
    def listCallback(self, sender, fonts):
        for index in sender.getSelection():
            item = sender.get()[index]
            font = fonts[index]
            if item["status"]:
                item["status"] = font["status"] = ""
            else:
                item["status"] = font["status"] = u"•"
        self.updateView()
    
    def contextCallback(self, sender):
        self.updateView()
    
    def drawCallback(self, sender):
        drawing = sender.get()
        setExtensionDefault(self.DEFAULTKEY_DRAW, drawing)
        self._drawing = drawing
        self.updateView()
    
    def fillCallback(self, sender):
        fill = sender.get()
        setExtensionDefault(self.DEFAULTKEY_FILL, fill)
        self._fill = fill
        self.updateView()
    
    def fillColorCallback(self, sender):
        fillColor = sender.get()
        setExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, fillColor)
        self._fillColor = fillColor
        self.updateView()
    
    def strokeCallback(self, sender):
        stroke = sender.get()
        setExtensionDefault(self.DEFAULTKEY_STROKE, stroke)
        self._stroke = stroke
        self.updateView()
    
    def strokeColorCallback(self, sender):
        strokeColor = sender.get()
        setExtensionDefaultColor(self.DEFAULTKEY_STROKECOLOR, strokeColor)
        self._strokeColor = strokeColor
        self.updateView()
    
    def pointsCallback(self, sender):
        points = sender.get()
        setExtensionDefault(self.DEFAULTKEY_POINTS, points)
        self._points = points
        self.updateView()
    
    def pointsColorCallback(self, sender):
        pointsColor = sender.get()
        setExtensionDefaultColor(self.DEFAULTKEY_POINTSCOLOR, pointsColor)
        self._pointsColor = pointsColor
        self.updateView()
    
    def alignmentCallback(self, sender):
        alignment = sender.get()
        setExtensionDefault(self.DEFAULTKEY_ALIGNMENT, alignment)
        self._alignment = alignment
        self.updateView()
    
    def kerningCallback(self, sender):
        kerning = sender.get()
        setExtensionDefault(self.DEFAULTKEY_KERNING, kerning)
        self._kerning = kerning
        self.updateView()

    def floatingCallback(self, sender):
        floating = sender.get()
        setExtensionDefault(self.DEFAULTKEY_FLOATING, floating)
        self._floating = floating
        self.setWindowLevel()
        
    def resetSettingsCallback(self, sender):
        drawing = True
        fill = True
        fillColor = self.FALLBACK_FILLCOLOR
        stroke = True
        strokeColor = self.FALLBACK_STROKECOLOR
        points = True
        pointsColor = self.FALLBACK_POINTSCOLOR
        alignment = 0
        kerning = True
        floating = True
        
        setExtensionDefault(self.DEFAULTKEY_DRAW, drawing)
        setExtensionDefault(self.DEFAULTKEY_FILL, fill)
        setExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, fillColor)
        setExtensionDefault(self.DEFAULTKEY_STROKE, stroke)
        setExtensionDefaultColor(self.DEFAULTKEY_STROKECOLOR, strokeColor)
        setExtensionDefault(self.DEFAULTKEY_POINTS, points)
        setExtensionDefaultColor(self.DEFAULTKEY_POINTSCOLOR, pointsColor)
        setExtensionDefault(self.DEFAULTKEY_ALIGNMENT, alignment)
        setExtensionDefault(self.DEFAULTKEY_KERNING, kerning)
        setExtensionDefault(self.DEFAULTKEY_FLOATING, floating)
        
        self.w.draw.set(drawing)
        self.w.fill.set(fill)
        self.w.fillColor.set(fillColor)
        self.w.stroke.set(stroke)
        self.w.strokeColor.set(strokeColor)
        self.w.points.set(points)
        self.w.pointsColor.set(strokeColor)
        self.w.alignment.set(alignment)
        self.w.kerning.set(kerning)
        self.w.floating.set(floating)
        
        self._drawing = drawing
        self._fill = fill
        self._fillColor = fillColor
        self._stroke = stroke
        self._strokeColor = strokeColor
        self._points = points
        self._pointsColor = strokeColor
        self._alignment = alignment
        self._kerning = kerning
        self._floating = floating
        
        self.updateView()

    def addHiddenFontsCallback(self, sender):
        fonts = OpenFont(None, False)
        if fonts is None:
            return
        if not isinstance(fonts, list): # make sure it's a list
            fonts = [fonts] 
        paths = [font["font"].path for font in self.hiddenFonts]
        for font in fonts:
            if font.path in paths:
                continue # already open
            self.hiddenFonts.append({"font": font, "status": u"•"})
        self.w.hiddenFontList.set(self.getHiddenFontItems())
        self.updateView()
    
    def removeHiddenFontsCallback(self, sender):
        hiddenFontList = self.w.hiddenFontList.get()
        selection = self.w.hiddenFontList.getSelection()
        for i in reversed(selection):
            del self.hiddenFonts[i]
            item = hiddenFontList[i]
            self.w.hiddenFontList.remove(item)
        self.updateView()


if __name__ == "__main__":
    OverlayUFOs()
