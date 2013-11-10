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

from mojo.drawingTools import stroke, fill, strokeWidth
from vanilla import Button, CheckBox, ColorWell, FloatingWindow, List, RadioGroup, TextBox
from AppKit import NSFilenamesPboardType, NSDragOperationCopy, NSColor
from mojo.UI import UpdateCurrentGlyphView
from defconAppKit.windows.baseWindow import BaseWindowController
from os.path import splitext
from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor

from ViewSourceFonts import ViewSourceFonts

defaultKey = "com.fontbureau.viewSourceFonts"

class ViewSourceFontsDialog(BaseWindowController, ViewSourceFonts):
    def __init__(self):
        ViewSourceFonts.__init__(self)
        
        self.sources = []
        self.color = getExtensionDefaultColor("%s.%s" %(defaultKey, "color"), NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, .5, .1))
        self.stroke = getExtensionDefault("%s.%s" %(defaultKey, "stroke"), False)
        self.fill = getExtensionDefault("%s.%s" %(defaultKey, "fill"), True)
        
        self.w = FloatingWindow((300, 184), "Overlay UFOs", minSize=(300, 184))

        x = 10
        y = 10

        self.w.view = CheckBox((x, y, -10, -10), "Overlays", 
                                             callback=self.viewCallback, 
                                             value=True)


        self.w.defaultPaths = Button((-210, y, 30, 22), unichr(8634), callback=self.defaultPathsCallback)

        self.w.addPath = Button((-180, y, 30, 22), '+', callback=self.addPathCallback)
        self.w.removePath = Button((-150, y, 30, 22), '-', callback=self.removePathCallback)
        self.w.clearPaths = Button((-120, y, 30, 22), 'x', callback=self.clearPathsCallback)

        self.w.fontList = List((10, 40, -90, -10), self.getDefaultSources(), 
                               drawFocusRing=True, 
                               enableDelete=True, 
                               otherApplicationDropSettings=dict(type=NSFilenamesPboardType, operation=NSDragOperationCopy, callback=self.dropCallback) 
                               ) 

                
        y = 40
        
        self.w.fill = CheckBox((-80, y, 60, 22), "Fill", 
                               value = self.fill,
                               callback=self.fillCallback)
        y += 30
        self.w.stroke = CheckBox((-80, y, 60, 22), "Stroke", 
                               value = self.stroke, 
                               callback=self.strokeCallback)
        
        y += 30
        self.w.color = ColorWell((-80, y, 60, 22), 
                                 color=self.color,
                                 callback=self.colorCallback)
        
        y += 30
        self.w.alignText = TextBox((-80, y, 90, 50), 'Alignment')
        y += 10

        self.w.align = RadioGroup((-80, y, 60, 50), ['L', 'C', 'R'], isVertical=False, callback=self.alignCallback)
        self.w.align.set(0)
        
        self.setUpBaseWindowBehavior()
        self.w.open()
        self.updateView()


    def dropCallback(self, sender, dropInfo): 
        acceptedFonts = [".ufo", ".ttf", ".otf"] 
        isProposal = dropInfo["isProposal"] 
        paths = dropInfo["data"]
        paths = [path for path in paths if splitext(path)[-1].lower() in acceptedFonts] 
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
        return AllFonts()
    
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
        self.color = sender.get()
        self.updateView()
    
    def fillCallback(self, sender):
        self.fill = sender.get()
        self.updateView()
    
    def strokeCallback(self, sender):
        self.stroke = sender.get()
        self.updateView()
        
    def alignCallback(self, sender):
        self.alignment = self.w.align.get()
        self.updateView()

    def updateView(self, sender=None):
        UpdateCurrentGlyphView()

    def windowCloseCallback(self, sender):
        if self.w.view.get():
            self.removeObserver()
        self.updateView()
        setExtensionDefaultColor("%s.%s" %(defaultKey, "color"), (self.color))
        setExtensionDefault("%s.%s" %(defaultKey, "stroke"), self.stroke)
        setExtensionDefault("%s.%s" %(defaultKey, "fill"), self.fill)
        BaseWindowController.windowCloseCallback(self, sender)
        
    def getColor(self):
        return self.color.getRed_green_blue_alpha_(None, None, None, None)

    def setStroke(self):
        if self.stroke:
            strokeWidth(.5)
            r,g,b,a = self.getColor()
            a += .3
            if a > 1:
                a = 1
            stroke(r, g, b, a)
        else:
            #strokeWidth(0)
            stroke(None)
    
    def setFill(self):
        if self.fill:
            r,g,b,a = self.getColor()
            fill(r,g,b,a)
        else:
            fill(None)
    
        
ViewSourceFontsDialog()