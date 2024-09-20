#!/usr/bin/env python3

import math
from fontTools.misc.transform import Identity

from vanilla import FloatingWindow, TextBox, EditText
from vanilla import Button, RadioGroup, CheckBox

from mojo.roboFont import CurrentFont, AllFonts, CurrentGlyph
from mojo.UI import CurrentGlyphWindow, CurrentWindow
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.subscriber import WindowController, Subscriber, registerRoboFontSubscriber


######################
# ITALIC OFFSET MATH #
######################

def calcItalicOffset(yoffset, italicAngle):
    '''
    Given a y offset and an italic angle, calculate the x offset.
    '''
    from math import radians, tan
    ritalicAngle = radians(italicAngle)
    xoffset = int(round(tan(ritalicAngle) * yoffset))
    return xoffset*-1

def calcItalicRise(xoffset, italicAngle):
    '''
    Given a x offset and an italic angle, calculate the y offset.
    '''
    from math import radians, tan
    if italicAngle == 0:
        return 0
    ritalicAngle = radians(italicAngle)
    yoffset = int(round( float(xoffset) / tan(ritalicAngle) ))
    return yoffset

def calcItalicCoordinates(coords, italicAngle):
    """
    Given (x, y) coords and an italic angle, get new coordinates accounting for italic offset.
    """
    x, y = coords
    x += calcItalicOffset(y, italicAngle)
    return x, y

################
# ITALIC TOOLS #
################
def calcItalicSlantOffset(italicAngle=0, crossHeight=0):
    """
    Get italic slant offset.
    """
    return calcItalicOffset(-crossHeight, italicAngle)

def calcCrossHeight(italicAngle=0, italicSlantOffset=0):
    return calcItalicRise(italicSlantOffset, italicAngle)

def makeReferenceLayer(source, italicAngle, backgroundName='com.fontbureau.italicReference'):
    """
    Store a vertically skewed copy in the mask.
    """
    italicSlant = abs(italicAngle)
    g = source.getLayer(backgroundName)
    g.decompose()
    source.copyToLayer(backgroundName)
    # use for vertical offset later
    top1 = g.bounds[3]
    bottom1 = g.bounds[1]
    height1 = top1 + abs(bottom1)
    # vertical skew
    m = Identity
    dx = 0
    dy = italicSlant/2.0   # half the italic angle
    x = math.radians(dx)
    y = math.radians(dy)
    m = m.skew(x, -y)
    g.transformBy(m)
    top2 = g.bounds[3]
    bottom2 = g.bounds[1]
    height2 = top2 + abs(bottom2)
    dif = (height1-height2) / 2
    yoffset = (abs(bottom2)-abs(bottom1)) + dif
    g.moveBy((0, yoffset))

def italicize(glyph,
              italicAngle=None,
              offset=0,
              doContours = True,
              doAnchors = True,
              doGuides = True,
              doComponents = True,
              doImage = True,
              shouldMakeReferenceLayer=True,
              DEBUG=False):
    """
    Oblique a glyph using cap height and italic angle.
    """
    with glyph.undo("italicBowtie"):
        xoffset = offset
        # skew the glyph horizontally
        glyph.skewBy(-italicAngle, (0, 0))
        if doContours:
            for c in glyph.contours:
                c.moveBy((xoffset, 0))
                if DEBUG:
                    print(f'\t\t\t {c}')
        # anchors
        if doAnchors:
            for anchor in glyph.anchors:
                anchor.moveBy((xoffset, 0))
                if DEBUG:
                    print(f'\t\t\t {anchor}')
        # guides
        if doGuides:
            for guide in glyph.guidelines:
                guide.x += xoffset
                if DEBUG:
                    print(f'\t\t\t {guide} {guide.x}')
        # image
        if doImage:
            if glyph.image:
                glyph.image.moveBy((xoffset, 0))
                if DEBUG:
                    print(f'\t\t\t {glyph.image}')
        if doComponents:
            for c in glyph.components:
                cxoffset = calcItalicOffset(c.offset[1], italicAngle)
                c.offset = (c.offset[0]-cxoffset, c.offset[1])

        if not glyph.components and shouldMakeReferenceLayer:
            makeReferenceLayer(glyph, italicAngle)
        glyph.markColor = (0, .1, 1, .2)

############
# THE TOOL #
############
class ItalicBowtie(Subscriber, WindowController):
    DEFAULTKEY = 'com.fontbureau.italicBowtie'
    DEFAULTKEY_REFERENCE = DEFAULTKEY + '.drawReferenceGlyph'
    italicSlantOffsetKey = 'com.typemytype.robofont.italicSlantOffset'

    container = None
    currentGlyph = None
    currentFont = None

    debug = True

    def build(self):
        self.setUpContainers()
        self.w = FloatingWindow((325, 250), "Italic Bowtie")
        self.populateWindow()

    def started(self):
        self.w.open()

    def destroy(self):
        if self.container:
            self.container.clearSublayers()

    def roboFontDidSwitchCurrentGlyph(self, info):
        self.setState()
        
    def roboFontDidSwitchCurrentFont(self, info):
        self.setState()

    def glyphEditorDidSetGlyph(self, info):
        self.destroy()
        self.setState()
        self.setUpContainers()
        self.updateBowtie()
        
    def setState(self):
        currentWindow = CurrentWindow()
        if currentWindow:
            if hasattr(currentWindow, 'document'):
                self.currentGlyph = currentWindow.document.getCurrentGlyph()
                self.currentFont = currentWindow.document.getFont()
            elif hasattr(currentWindow, 'getGlyph'):
                self.currentGlyph = currentWindow.getGlyph()
                self.currentFont = self.currentGlyph.font
            else:
                self.currentGlyph = CurrentGlyph()
                self.currentFont = CurrentFont()
        else:
            self.currentGlyph = None
            self.currentFont = None
            
        if self.currentGlyph:
            self.currentGlyph = self.currentGlyph.asFontParts()
        
        if self.currentFont:
            self.currentFont = self.currentFont.asFontParts()
            self.w.setTitle(f"Italic Bowtie — {self.currentFont.fontWindow().window().getTitle()}")
        else:
            self.w.setTitle("Italic Bowtie")
            
    def setUpContainers(self):
        glyphEditor = CurrentGlyphWindow()
        if glyphEditor:
            self.container = glyphEditor.extensionContainer(
                identifier="com.roboFont.ItalicBowtie.background",
                location="background",
                clear=True)

            self.crossHeightLayer = self.container.appendLineSublayer(
                strokeWidth=1,
                strokeColor=(.2, .1, .5, .5),
                strokeDash=(2,)
            )

            fillColor = (.2, .1, .5, .05)
            strokeColor = (.2, .1, .5, .5)
            strokeWidth = 0.5
            self.leftBowtieLayer = self.container.appendPathSublayer(
                fillColor=fillColor,
                strokeColor=strokeColor,
                strokeWidth=strokeWidth
            )
            self.rightBowtieLayer = self.container.appendPathSublayer(
                fillColor=fillColor,
                strokeColor=strokeColor,
                strokeWidth=strokeWidth
            )

    def populateWindow(self):
        y = 10
        x = 10
        self.w.italicAngleLabel = TextBox((x, y+4, 100, 22), 'Italic Angle', sizeStyle="small")
        x += 100
        self.w.italicAngle = EditText((x, y, 40, 22), '', sizeStyle="small", callback=self.calcItalicCallback)

        y += 30
        x = 10
        self.w.crossHeightLabel = TextBox((x, y+4, 95, 22), 'Cross Height', sizeStyle="small")
        x += 100
        self.w.crossHeight = EditText((x, y, 40, 22), '', sizeStyle="small", callback=self.calcItalicCallback)
        x += 50
        self.w.crossHeightSetUC = Button((x, y, 65, 22), 'Mid UC', sizeStyle="small", callback=self.calcItalicCallback)
        x += 75
        self.w.crossHeightSetLC = Button((x, y, 65, 22), 'Mid LC', sizeStyle="small", callback=self.calcItalicCallback)

        y += 30
        x = 10
        self.w.italicSlantOffsetLabel = TextBox((x, y+4, 100, 22), 'Italic Slant Offset', sizeStyle="small")
        x += 100
        self.w.italicSlantOffset = EditText((x, y, 40, 22), '', sizeStyle="small", callback=self.calcItalicCallback)
        x += 60

        y += 30
        x = 10
        self.w.refresh = Button((x, y, 140, 22), u'Values from Current', callback=self.refresh, sizeStyle="small")

        y += 30

        self.w.fontSelection = RadioGroup((x, y, 120, 35), ['Current Font', 'All Fonts'], sizeStyle="small")
        self.w.fontSelection.set(0)

        x += 160
        self.w.glyphSelection = RadioGroup((x, y, 120, 55), ['Current Glyph', 'Selected Glyphs', 'All Glyphs'], sizeStyle="small")
        self.w.glyphSelection.set(0)
        y += 60
        x = 10
        self.w.setInFont = Button((x, y, 140, 22), 'Set Font Italic Values', sizeStyle="small", callback=self.setInFontCallback)
        x += 160
        self.w.italicize = Button((x, y, 140, 22), 'Italicize Glyphs', sizeStyle="small", callback=self.italicizeCallback)
        y += 25
        self.w.makeReferenceLayer = CheckBox((x, y, 145, 22), 'Make Reference Layer', value=getExtensionDefault(self.DEFAULTKEY_REFERENCE, False), sizeStyle="small", callback=self.makeReferenceLayerCallback)
        x = 10

        self.refresh()

    def makeReferenceLayerCallback(self, sender):
        setExtensionDefault(self.DEFAULTKEY_REFERENCE, sender.get())

    def italicizeCallback(self, sender=None):
        self.setState()
        italicAngle = self.getItalicAngle()
        italicSlantOffset = self.getItalicSlantOffset()
        
        fonts = []
        
        if self.w.fontSelection.get() == 0:
            if self.currentFont is not None:
                fonts.append(self.currentFont)
        else:
            fonts = AllFonts()

        glyphs = []
        if self.w.glyphSelection.get() == 0 and self.currentGlyph is not None:
            glyphs.append(self.currentGlyph)
        elif self.w.glyphSelection.get() == 1:
            for f in fonts:
                for gname in self.currentFont.selectedGlyphNames:
                    if gname in f:
                        glyphs.append(f[gname])
        elif self.w.glyphSelection.get() == 2:
            for f in fonts:
                for g in f:
                    glyphs.append(g)
        for glyph in glyphs:
            italicize(glyph, italicAngle,
                      offset=italicSlantOffset,
                      shouldMakeReferenceLayer=self.w.makeReferenceLayer.get())

    def refresh(self, sender=None):
        self.setState()
        if self.currentFont:
            italicSlantOffset = self.currentFont.lib.get(self.italicSlantOffsetKey) or 0
            italicAngle = self.currentFont.info.italicAngle or 0
            crossHeight = calcCrossHeight(italicAngle=italicAngle,
                                                    italicSlantOffset=italicSlantOffset)
            self.setItalicSlantOffset(italicSlantOffset)
            self.setItalicAngle(italicAngle)
            self.setCrossHeight(crossHeight)
        else:
            self.setItalicSlantOffset(0)
            self.setItalicAngle(0)
            self.setCrossHeight(0)
        self.updateBowtie()

    def setInFontCallback(self, sender):
        fonts = []
        if self.w.fontSelection.get() == 0:
            if self.currentFont is not None:
                fonts.append(self.currentFont)
        else:
            fonts = AllFonts()
        
        for f in fonts:
            # IMPORTANT: set the lib first, then the italic angle, to get the change to show
            f.lib[self.italicSlantOffsetKey] = self.getItalicSlantOffset()
            f.info.italicAngle = self.getItalicAngle()
            f.changed()
            
        self.updateBowtie()

    def drawItalicBowtie(self, layer,
                         italicAngle=0, crossHeight=0, italicSlantOffset=0,
                         ascender=0, descender=0, xoffset=0):
        """
        Draw an italic Bowtie.
        """
        topBowtie = ascender
        topBowtieOffset = calcItalicOffset(topBowtie, italicAngle)
        bottomBowtie = descender
        bottomBowtieOffset = calcItalicOffset(bottomBowtie, italicAngle)

        pen = layer.getPen()
        pen.moveTo((xoffset, descender))
        pen.lineTo((xoffset+bottomBowtieOffset+italicSlantOffset, descender))
        pen.lineTo((xoffset+topBowtieOffset+italicSlantOffset, ascender))
        pen.lineTo((xoffset, ascender))
        pen.closePath()

    def calcItalicCallback(self, sender):
        self.setState()
        italicAngle = self.getItalicAngle()
        italicSlantOffset = self.getItalicSlantOffset()

        if sender == self.w.crossHeightSetUC and self.currentFont is not None:
            crossHeight = ( self.currentFont.info.capHeight or 0 ) / 2.0
            sender = self.w.crossHeight
        elif sender == self.w.crossHeightSetLC and self.currentFont is not None:
            crossHeight = ( self.currentFont.info.xHeight or 0 ) / 2.0
            sender = self.w.crossHeight
        else:
            crossHeight = self.getCrossHeight()
        if sender == self.w.italicAngle or sender == self.w.italicSlantOffset:
            self.setCrossHeight(calcCrossHeight(italicAngle=italicAngle, italicSlantOffset=italicSlantOffset))
        elif sender == self.w.crossHeight:
            self.setItalicSlantOffset(calcItalicSlantOffset(italicAngle=italicAngle, crossHeight=crossHeight))
            self.setCrossHeight(crossHeight)
        self.updateBowtie()

    def updateBowtie(self):
        glyphEditor = CurrentGlyphWindow()
        if self.currentGlyph is not None and glyphEditor is not None:
            italicAngle = self.getItalicAngle()
            italicSlantOffset = self.getItalicSlantOffset()
            crossHeight = self.getCrossHeight()
            ascender = self.currentFont.info.ascender
            descender = self.currentFont.info.descender
            italicSlantOffsetOffset = italicSlantOffset
            for xoffset, layer in [(0, self.leftBowtieLayer), (self.currentGlyph.width, self.rightBowtieLayer)]:
                self.drawItalicBowtie(layer=layer,
                                    italicAngle=italicAngle,
                                    crossHeight=crossHeight,
                                    ascender=ascender,
                                    descender=descender,
                                    italicSlantOffset=italicSlantOffsetOffset,
                                    xoffset=xoffset)
            # crossheight
            self.crossHeightLayer.setStartPoint((0, crossHeight))
            self.crossHeightLayer.setEndPoint((self.currentGlyph.width, crossHeight))

    ################################
    ################################
    ################################

    def getItalicAngle(self):
        a = self.w.italicAngle.get()
        try:
            return float(a)
        except ValueError:
            return 0

    def getItalicSlantOffset(self):
        a = self.w.italicSlantOffset.get()
        try:
            return float(a)
        except ValueError:
            return 0

    def getCrossHeight(self):
        a = self.w.crossHeight.get()
        try:
            return float(a)
        except ValueError:
            print('error', a)
            return 0

    def setItalicAngle(self, italicAngle):
        self.w.italicAngle.set(f'{italicAngle}')

    def setItalicSlantOffset(self, italicSlantOffset):
        self.w.italicSlantOffset.set(f'{italicSlantOffset}')

    def setCrossHeight(self, crossHeight):
        self.w.crossHeight.set(f'{crossHeight}')


if __name__ == '__main__':
    if CurrentFont():
        registerRoboFontSubscriber(ItalicBowtie)