#coding=utf-8
from fontTools.pens.basePen import BasePen
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.events import addObserver, removeObserver
from AppKit import * #@PydevCodeAnalysisIgnore
from vanilla import * #@PydevCodeAnalysisIgnore 
from mojo.drawingTools import *
from mojo.UI import UpdateCurrentGlyphView, CurrentGlyphWindow
from mojo.extensions import getExtensionDefault, setExtensionDefault
from fontTools.misc.transform import Identity
import math

class M:
    ##################
    # ITALIC OFFSET MATH
    ##################
    
    @classmethod
    def getItalicOffset(cls, yoffset, italicAngle):
        '''
        Given a y offset and an italic angle, calculate the x offset.
        '''
        from math import radians, tan
        ritalicAngle = radians(italicAngle)
        xoffset = int(round(tan(ritalicAngle) * yoffset))
        return xoffset*-1

    @classmethod
    def getItalicRise(cls, xoffset, italicAngle):
        '''
        Given a x offset and an italic angle, calculate the y offset.
        '''
        from math import radians, tan
        if italicAngle == 0:
            return 0
        ritalicAngle = radians(italicAngle)
        yoffset = int(round( float(xoffset) / tan(ritalicAngle) ))
        return yoffset

    @classmethod
    def getItalicCoordinates(cls, coords, italicAngle):
        """
        Given (x, y) coords and an italic angle, get new coordinates accounting for italic offset.
        """
        x, y = coords
        x += cls.getItalicOffset(y, italicAngle)
        return x, y
        
class DrawingToolsPen(BasePen):
    """
    A quick and easy pen that converts to DrawBot/Mojo Drawing Tools.
    """
    def _moveTo(self, p1):
        moveTo(p1)
    def _lineTo(self, p1):
        lineTo(p1)
    def _curveToOne(self, p1, p2, p3):
        curveTo(p1, p2, p3)
    def _closePath(self):
        closepath()

class Italicalc:
    """
    Some classmethods for doing Italic calculations.
    """
    
    @classmethod
    def drawItalicBowtie(cls, italicAngle=0, crossHeight=0, italicSlantOffset=0, ascender=0, descender=0, xoffset=0):
        """
        Draw an italic Bowtie.
        """
        topBowtie = ascender
        topBowtieOffset = M.getItalicOffset(topBowtie, italicAngle)
        bottomBowtie = descender
        bottomBowtieOffset = M.getItalicOffset(bottomBowtie, italicAngle)
        path = DrawingToolsPen(None)
        newPath()
        path.moveTo((xoffset, descender))
        path.lineTo((xoffset+bottomBowtieOffset+italicSlantOffset, descender))
        path.lineTo((xoffset+topBowtieOffset+italicSlantOffset, ascender))
        path.lineTo((xoffset, ascender))
        closePath()
        drawPath()
    
    @classmethod
    def calcItalicSlantOffset(cls, italicAngle=0, crossHeight=0):
        """
        Get italic slant offset.
        """
        return M.getItalicOffset(-crossHeight, italicAngle)
    
    @classmethod
    def calcCrossHeight(cls, italicAngle=0, italicSlantOffset=0):
        return M.getItalicRise(italicSlantOffset, italicAngle)        
    
    @classmethod
    def makeReferenceLayer(cls, source, italicAngle, backgroundName='com.fontbureau.italicReference'):
        """
        Store a vertically skewed copy in the mask.
        """
        italicSlant = abs(italicAngle)
        g = source.getLayer(backgroundName)
        g.decompose()
        source.copyToLayer(backgroundName)
        #use for vertical offset later
        top1 = g.box[3]
        bottom1 = g.box[1]
        height1 = top1 + abs(bottom1)
        #vertical skew
        m = Identity
        dx = 0
        dy = italicSlant/2.0 # half the italic angle
        x = math.radians(dx)
        y = math.radians(dy)
        m = m.skew(x,-y)
        g.transform(m)
        top2 = g.box[3]
        bottom2 = g.box[1]
        height2 = top2 + abs(bottom2)
        dif = (height1-height2) / 2
        yoffset = (abs(bottom2)-abs(bottom1)) + dif
        g.move((0,yoffset))

    @classmethod
    def italicize(cls, g, 
        italicAngle=None, 
        offset=0, 
        doContours = True,
        doAnchors = True,
        doGuides = True,
        doComponents = True,
        doImage = True,
        makeReferenceLayer=True,
        DEBUG=False,
        ):
        """
        Oblique a glyph using cap height and italic angle.
        """
        g.prepareUndo()
        f = g.getParent()
        xoffset = offset
        # skew the glyph horizontally
        g.skew(-italicAngle, (0, 0))
        g.prepareUndo()
        if doContours:
            for c in g.contours:
                c.move((xoffset, 0))
                if DEBUG: print('\t\t\t', c)
        # anchors
        if doAnchors:
            for anchor in g.anchors:
                anchor.move((xoffset, 0))
                if DEBUG: print('\t\t\t', anchor)
        # guides
        if doGuides:
            for guide in g.guides:
                guide.x += xoffset
                if DEBUG: print('\t\t\t', guide, guide.x)
                # image
                if doImage:
                    if g.image:
                        g.image.move((xoffset, 0))
                        if DEBUG: print('\t\t\t', image)
        if doComponents:
            for c in g.components:
                cxoffset = M.getItalicOffset(c.offset[1], italicAngle)
                c.offset = (c.offset[0]-cxoffset, c.offset[1])
        
        if not g.components and makeReferenceLayer:
            cls.makeReferenceLayer(g, italicAngle)
        g.mark = (0, .1, 1, .2)
        g.performUndo()

class Tool():
    """
    The tool object manages the font list. This is a simplification.
    """
    
    def addObserver(self, target, method, action):
        addObserver(target, method, action)

    def removeObserver(self, target, method, action):
        removeObserver(target, method, action)


class ItalicBowtie(BaseWindowController, Italicalc):
    DEFAULTKEY = 'com.fontbureau.italicBowtie'
    DEFAULTKEY_REFERENCE = DEFAULTKEY + '.drawReferenceGlyph'
    italicSlantOffsetKey = 'com.typemytype.robofont.italicSlantOffset'
    
    def activateModule(self):
        self.tool.addObserver(self, 'drawInactive', 'drawInactive')
        self.tool.addObserver(self, 'drawBackground', 'drawBackground')

    def deactivateModule(self):
        removeObserver(self, 'drawBackground')
        removeObserver(self, 'drawInactive')

    def __init__(self):
        self.tool = Tool()
        self.w = FloatingWindow((325, 250), "Italic Bowtie")
        self.populateView()
        self.getView().open()
        
    def getView(self):
        return self.w
        
    def populateView(self):
        lineHeight = 30
        view = self.getView()
        y = 10
        x = 10
        view.italicAngleLabel = TextBox((x, y+4, 100, 22), 'Italic Angle', sizeStyle="small")
        x += 100
        view.italicAngle = EditText((x, y, 40, 22), '', sizeStyle="small", callback=self.calcItalicCallback)

        y += 30
        x = 10
        view.crossHeightLabel = TextBox((x, y+4, 95, 22), 'Cross Height', sizeStyle="small")
        x += 100
        view.crossHeight = EditText((x, y, 40, 22), '', sizeStyle="small", callback=self.calcItalicCallback)
        x += 50
        view.crossHeightSetUC = Button((x, y, 65, 22), 'Mid UC', sizeStyle="small", callback=self.calcItalicCallback)
        x += 75
        view.crossHeightSetLC = Button((x, y, 65, 22), 'Mid LC', sizeStyle="small", callback=self.calcItalicCallback)
        
        
        y += 30
        x = 10        
        view.italicSlantOffsetLabel = TextBox((x, y+4, 100, 22), 'Italic Slant Offset', sizeStyle="small")
        x += 100
        view.italicSlantOffset = EditText((x, y, 40, 22), '', sizeStyle="small", callback=self.calcItalicCallback)
        x += 60

        y += 30
        x = 10
        view.refresh = Button((x, y, 140, 22), u'Values from Current', callback=self.refresh, sizeStyle="small")
        
        y += 30
        
        view.fontSelection = RadioGroup((x, y, 120, 35), ['Current Font', 'All Fonts'], sizeStyle="small")
        view.fontSelection.set(0)
        

        x += 160
        view.glyphSelection = RadioGroup((x, y, 120, 55), ['Current Glyph', 'Selected Glyphs', 'All Glyphs'], sizeStyle="small")
        view.glyphSelection.set(0)
        y += 60
        x = 10
        view.setInFont = Button((x, y, 140, 22), 'Set Font Italic Values', sizeStyle="small", callback=self.setInFontCallback)       
        x += 160
        view.italicize = Button((x, y, 140, 22), 'Italicize Glyphs', sizeStyle="small", callback=self.italicizeCallback)
        y += 25
        view.makeReferenceLayer = CheckBox((x, y, 145, 22), 'Make Reference Layer', value=getExtensionDefault(self.DEFAULTKEY_REFERENCE, False), sizeStyle="small", callback=self.makeReferenceLayerCallback)
        x = 10

        self.refresh()
        if self.getItalicAngle() == 0 and CurrentFont() is not None:
            self.setCrossHeight((CurrentFont().info.capHeight or 0) / 2)
        self.activateModule()
        self.setUpBaseWindowBehavior()
        self.updateView()

    def makeReferenceLayerCallback(self, sender):
        setExtensionDefault(self.DEFAULTKEY_REFERENCE, sender.get())
        
    def italicizeCallback(self, sender=None):
        view = self.getView()
        italicAngle = self.getItalicAngle()
        italicSlantOffset = self.getItalicSlantOffset()
        if view.fontSelection.get() == 0:
            if CurrentFont() is not None:
                fonts = [CurrentFont()]
            else:
                fonts = []
        else:
            fonts = AllFonts()
        
        if view.glyphSelection.get() == 0 and CurrentGlyph() is not None:
            glyphs = [CurrentGlyph()] 
        elif view.glyphSelection.get() == 1:
            glyphs = []
            for f in fonts:
                for gname in CurrentFont().selection:
                    if f.has_key(gname):
                        glyphs.append(f[gname])
        else:
            glyphs = []
            for f in fonts:
                for g in f:
                    glyphs.append(g.name)
        
        for glyph in glyphs:
            Italicalc.italicize(glyph, italicAngle, offset=italicSlantOffset, makeReferenceLayer=view.makeReferenceLayer.get())
                
    
    def refresh(self, sender=None):
        f = CurrentFont()
        if f:
            view = self.getView()
            italicSlantOffset = f.lib.get(self.italicSlantOffsetKey) or 0
            italicAngle = f.info.italicAngle or 0
            crossHeight = Italicalc.calcCrossHeight(italicAngle=italicAngle, italicSlantOffset=italicSlantOffset)
            self.setItalicSlantOffset(italicSlantOffset)
            self.setItalicAngle(italicAngle)
            self.setCrossHeight(crossHeight)
        else:
            self.setItalicSlantOffset(0)
            self.setItalicAngle(0)
            self.setCrossHeight(0)
        self.updateView()

    def setInFontCallback(self, sender):
        view = self.getView()
        if view.fontSelection.get() == 0:
            if CurrentFont() is not None:
                fonts = [CurrentFont()]
            else:
                fonts = []
        else:
            fonts = AllFonts()
        for f in fonts:
            f.prepareUndo()
            f.info.italicAngle = self.getItalicAngle()
            f.lib[self.italicSlantOffsetKey] = self.getItalicSlantOffset()
            f.performUndo()
        try:
            window = CurrentGlyphWindow()
            window.setGlyph(CurrentGlyph().naked())
        except:
            print(self.DEFAULTKEY, 'error resetting window, please refresh it')
        self.updateView()
    
    def calcItalicCallback(self, sender):
        view = self.getView()
        italicAngle = self.getItalicAngle()
        italicSlantOffset = self.getItalicSlantOffset()
                
        if sender == view.crossHeightSetUC and CurrentFont() is not None:
            crossHeight = ( CurrentFont().info.capHeight or 0 ) / 2.0
            sender = view.crossHeight
        elif sender == view.crossHeightSetLC and CurrentFont() is not None:
            crossHeight = ( CurrentFont().info.xHeight or 0 ) / 2.0        
            sender = view.crossHeight
        else:
            crossHeight = self.getCrossHeight()
        if sender == view.italicAngle or sender == view.italicSlantOffset:
            self.setCrossHeight(Italicalc.calcCrossHeight(italicAngle=italicAngle, italicSlantOffset=italicSlantOffset))
        elif sender == view.crossHeight:
            self.setItalicSlantOffset(Italicalc.calcItalicSlantOffset(italicAngle=italicAngle, crossHeight=crossHeight))
            self.setCrossHeight(crossHeight)    
        self.updateView()
    
    def updateView(self, sender=None):
        UpdateCurrentGlyphView()

    def windowCloseCallback(self, sender):
        self.deactivateModule()
        self.updateView()
        BaseWindowController.windowCloseCallback(self, sender)
    
    ################################
    ################################
    ################################
    
    def getItalicAngle(self):
        a = self.getView().italicAngle.get()
        try:
            return float(a)
        except:
            return 0
    
    def getItalicSlantOffset(self):
        a = self.getView().italicSlantOffset.get()
        try:
            return float(a)
        except:
            return 0
            
    def getCrossHeight(self):
        a = self.getView().crossHeight.get()
        try:
            return float(a)
        except:
            print('error', a)
            return 0
            
    def setItalicAngle(self, italicAngle):
        view = self.getView()
        view.italicAngle.set(str(italicAngle))

    def setItalicSlantOffset(self, italicSlantOffset):
        view = self.getView()
        view.italicSlantOffset.set(str(italicSlantOffset))

    def setCrossHeight(self, crossHeight):
        view = self.getView()
        view.crossHeight.set(str(crossHeight))
        
    def drawBackground(self, info):
        view = self.getView()
        g = info.get('glyph')
        scale = info.get('scale') or 1
        if g is None:
            return
        fill(.2, .1, .5, .05)
        #lineDash(2)
        stroke(.2, .1, .5, .5)
        strokeWidth(.5*scale)
        dashLine(0)
        f = g.getParent()
        italicAngle = self.getItalicAngle()
        italicSlantOffset = self.getItalicSlantOffset()
        crossHeight = self.getCrossHeight()
        ascender = f.info.ascender
        descender = f.info.descender
        italicSlantOffsetOffset = italicSlantOffset
        for xoffset in (0, g.width):
            self.drawItalicBowtie(italicAngle=italicAngle, crossHeight=crossHeight, ascender=ascender, descender=descender, italicSlantOffset=italicSlantOffsetOffset, xoffset=xoffset)
        dashLine(2)
        strokeWidth(1*scale)
        line((0, crossHeight), (g.width, crossHeight))        



    
    drawInactive = drawBackground
    
ItalicBowtie()
