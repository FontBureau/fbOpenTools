# OVERLAY UFOS

"""
In the current glyph window, this will presenteview the same glyph from a separate UFO or set of UFOs.

This does NOT import the UFO into a background layer. Instead, it renders a outline directly from the UFO into the glyph window view.

- There is no need to import duplicate data into a background layer.

- The source outline is always live; when changes are made to the source, they will automatically appear in the current without re-importing.

- The source font does not need to be opened with a UI.

DIALOG:
    
A floating dialog is present to let you open and select source fonts, fill, stroke, color.

Source Fonts: The default source font list is AllFonts(). The refresh button will return this list to AllFonts().

Adding Fonts: You can manually add fonts by selecting a UFO file. The UFO file will open without an interface.

Removing Fonts: There are buttons for removing selected fonts and for clearing the source font list. 

BUGS/IMPROVEMENTS:

Known Issue: The source font is drawn on top of the current font, instead of behind it. So, it is good to select a color with a low opacity.

Known Bug: If the glyph window for both source and current fonts are open, it is possible to select and inadvertently edit the source outline in the current window. I don't know how to solve this.

Improvement?: Add options to scale the source font.

Improvement?: Set different colors, fill settings for each font?


"""

from mojo.drawingTools import *
from mojo.events import addObserver, removeObserver
from fontTools.pens.transformPen import TransformPen
from vanilla import *
from AppKit import *
from mojo.UI import UpdateCurrentGlyphView
from defconAppKit.windows.baseWindow import BaseWindowController
import os


from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor

class MojoDrawingToolsPen(object):
    def __init__(self, g, f):
        self.g = g
        self.f = f
        newPath()
    def moveTo(self, pt):
        x, y = pt
        moveTo((x, y))
    def lineTo(self, pt):
        x, y = pt
        lineTo((x, y))
    def curveTo(self, pt1, pt2, pt3):
        h1x, h1y = pt1
        h2x, h2y = pt2
        x, y = pt3
        curveTo((h1x, h1y), (h2x, h2y), (x, y))
    def closePath(self):
        closePath()
    def endPath(self):
        closePath()
    def draw(self):
        drawPath()
    def addComponent(self, baseName, transformation):
        try:
            glyph = self.f[baseName]
            tPen = TransformPen(self, transformation)
            glyph.draw(tPen)
        except:
            pass


class ViewSourceFonts(object):
    def __init__(self):
        ## add an observer for the draw event
        self.addObserver()
        self.cacheCopy = None

    def addObserver(self):
        addObserver(self, "drawSourceFonts", "draw")

    def removeObserver(self):
        removeObserver(self, "draw")

    def getSources(self):
        sources = AllFonts()
        if sources:
            sources.pop(sources.index(CurrentFont()))
            return sources
        else:
            return []
    
    def getAlignment(self):
        return 'left'
    
    def drawSourceFonts(self, info):
        glyph = info['glyph']
        ## draw something the glyph view
        
        self.setStroke()
        self.setFill()
                
        for source in self.getSources():
            if source != CurrentFont():
                if source.has_key(glyph.name):
                    sourceGlyph = source[glyph.name]
                    sourceFont = sourceGlyph.getParent()
                    """
                    if self.cacheCopy and self.cacheCopy.name == sourceGlyph.name:
                        sourceGlyphCopy = self.cacheCopy
                    else:
                        sourceGlyphCopy = sourceGlyph.copy()
                        self.cacheCopy = sourceGlyphCopy
                    """
                    sourceGlyphCopy = sourceGlyph.copy()
                    
                    align = self.getAlignment()
                    if align == 'left':
                        pass
                    elif align == 'center':
                        destCenter = int(glyph.width/2)
                        sourceCenter = int(sourceGlyphCopy.width/2)
                        widthDiff = destCenter-sourceCenter
                        sourceGlyphCopy.move((widthDiff, 0))
                    elif align == 'right':
                        widthDiff = glyph.width-sourceGlyphCopy.width
                        sourceGlyphCopy.move((widthDiff, 0))                        	

                    mPen = MojoDrawingToolsPen(sourceGlyphCopy, sourceFont)
                                        
                    sourceGlyphCopy.draw(mPen)
                    mPen.draw()
                    self.updateView()

    def setStroke(self, value=.5):
        strokeWidth(value)
    
    def setFill(self, rgba=(.2, 0, .2, .2)):
        r, g, b, a = rgba
        fill(r, g, b, a)
    
    def getColor(self):
        return NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, .5, .2)

defaultKey = "com.fontbureau.viewSourceFonts"

class ViewSourceFontsDialog(BaseWindowController, ViewSourceFonts):
    def __init__(self):
        ViewSourceFonts.__init__(self)
        
        self.sources = []
        self.w = FloatingWindow((400, 200), "Overlay UFOs", minSize=(400, 200))

        x = 10
        y = 10

        self.w.view = CheckBox((x, y, -10, -10), "Show Overlays", 
                                             callback=self.viewCallback, 
                                             value=True)


        self.w.defaultPaths = Button((-230, y, 30, 22), unichr(8634), callback=self.defaultPathsCallback)

        self.w.addPath = Button((-200, y, 30, 22), '+', callback=self.addPathCallback)
        self.w.removePath = Button((-170, y, 30, 22), '-', callback=self.removePathCallback)
        self.w.clearPaths = Button((-140, y, 30, 22), 'x', callback=self.clearPathsCallback)

        self.w.fontList = List((10, 40, -110, -10), self.getDefaultSources(), 
                               drawFocusRing=True, 
                               enableDelete=True, 
                               otherApplicationDropSettings=dict(type=NSFilenamesPboardType, operation=NSDragOperationCopy, callback=self.dropCallback) 
                               ) 

                
        y = 40
        
        self.w.fill = CheckBox((-100, y, 60, 22), "Fill", 
                               #value=getExtensionDefault("%s.%s" %(defaultKey, "fill"), True),
                               value = True,
                               callback=self.fillCallback)
        y += 30
        self.w.stroke = CheckBox((-100, y, 60, 22), "Stroke", 
                               #value=getExtensionDefault("%s.%s" %(defaultKey, "stroke"), False),
                               value = False, 
                               callback=self.strokeCallback)
        
        y += 30
        color = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, .5, .1)

        self.w.color = ColorWell((-100, y, 60, 22), 
                                 color=color,
                                 callback=self.colorCallback)
        
        
        y += 30
        self.w.alignText = TextBox((-100, y, 90, 50), 'Alignment')
        y += 10

        self.w.align = RadioGroup((-100, y, 60, 50), ['L', 'C', 'R'], isVertical=False, callback=self.alignCallback)
        self.w.align.set(0)
        
        self.setUpBaseWindowBehavior()
        
        self.w.open()
        self.updateView()


    def dropCallback(self, sender, dropInfo): 
        acceptedFonts = [".ufo", ".ttf", ".otf"] 
        isProposal = dropInfo["isProposal"] 
        paths = dropInfo["data"]
        paths = [path for path in paths if os.path.splitext(path)[-1].lower() in acceptedFonts] 
        fonts = []
        for path in paths:
            if path:
                font = RFont(path, showUI=False)
                fonts.append(font)
        fonts = [font for font in fonts if font not in self.w.fontList] 
        if not fonts: 
            return False 
        if not isProposal and fonts:
            self.extendSources(fonts)
        return True 

    def viewCallback(self, sender):
        if sender.get():
            self.addObserver()
        else:
            self.removeObserver()
        self.updateView()
    
    def getSources(self):
        return self.w.fontList.get()
        
    def setSources(self, fontList):
        self.w.fontList.set(fontList)
        self.updateView()
    
    def extendSources(self, fontList):
        self.w.fontList.extend(fontList)
        self.updateView()
    
    def getDefaultSources(self):
        sources = AllFonts()
        return sources
    
    def addPathCallback(self, sender):
        f = OpenFont(None, showUI=False)
        sources = self.getSources()
        if type(f) is not list:
            f = [f]
        if f:
            self.extendSources(f)
            self.updateView()
        
    def removePathCallback(self, sender):
        selection = self.w.fontList.getSelection()
        selection.reverse()
        for item in selection:
            self.w.fontList.remove(self.w.fontList[item])
        self.updateView()
        
    def clearPathsCallback(self, sender):
        self.setSources([])
        self.updateView()
        
    def defaultPathsCallback(self, sender):
        self.setSources(self.getDefaultSources())
        self.updateView()
        
    def colorCallback(self, sender):
        setExtensionDefaultColor("%s.%s" %(defaultKey, "color"), sender.get())
        self.updateView()
    
    def fillCallback(self, sender):
        setExtensionDefault("%s.%s" %(defaultKey, "fill"), sender.get())
        self.setFill()
        self.updateView()
    
    def strokeCallback(self, sender):
        setExtensionDefault("%s.%s" %(defaultKey, "stroke"), sender.get())
        self.setStroke()
        self.updateView()
        
    def alignCallback(self, sender):
        self.updateView()
    
    def getAlignment(self):
        index = self.w.align.get()
        if index == 0:
            return 'left'
        elif index == 1:
            return 'center'
        elif index == 2:
            return 'right'

    def updateView(self, sender=None):
        UpdateCurrentGlyphView()

    def windowCloseCallback(self, sender):
        self.removeObserver()
        self.updateView()
        BaseWindowController.windowCloseCallback(self, sender)
        
    def getColor(self):
        c = self.w.color.get()
        return c.getRed_green_blue_alpha_(None, None, None, None)

    def setStroke(self):
        if self.w.stroke.get():
            strokeWidth(.5)
            r,g,b,a = self.getColor()
            a += .3
            if a > 1:
                a = 1
            stroke(r, g, b, a)
        else:
            strokeWidth(0)
            stroke(1, 1, 1, 0)
    
    def setFill(self):
        if self.w.fill.get():
            r,g,b,a = self.getColor()
            fill(r,g,b,a)
        else:
            fill(1, 1, 1, 0)
    
        
ViewSourceFontsDialog()