#!/usr/bin/env python3

# ------------- #
# Italic Bowtie #
# ------------- #

# -- Modules -- #
from vanilla import FloatingWindow, TextBox, EditText
from vanilla import Button, RadioGroup, CheckBox

from mojo.roboFont import CurrentFont, AllFonts, CurrentGlyph, OpenWindow
from mojo.UI import CurrentGlyphWindow
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.subscriber import WindowController, Subscriber, registerGlyphEditorSubscriber
from mojo.subscriber import registerSubscriberEvent, roboFontSubscriberEventRegistry
from mojo.events import postEvent

from tools import calcCrossHeight, italicize, calcItalicOffset, calcItalicSlantOffset

# -- Modules -- #
DEFAULT_KEY = 'com.fontbureau.italicBowtie'
DEFAULT_KEY_REFERENCE = DEFAULT_KEY + '.drawReferenceGlyph'
ITALIC_SLANT_OFFSET_KEY = 'com.typemytype.robofont.italicSlantOffset'


# -- Objects -- #
class ItalicBowtieController(WindowController):

    debug = True

    def build(self):
        self.w = FloatingWindow((325, 250), "Italic Bowtie")
        self.populateWindow()

    def populateWindow(self):
        y = 10
        x = 10
        self.w.italicAngleLabel = TextBox((x, y+4, 100, 22),
                                          'Italic Angle', sizeStyle="small")
        x += 100
        self.w.italicAngle = EditText((x, y, 40, 22), "",
                                      sizeStyle="small", callback=self.calcItalicCallback)

        y += 30
        x = 10
        self.w.crossHeightLabel = TextBox((x, y+4, 95, 22), 'Cross Height', sizeStyle="small")
        x += 100
        self.w.crossHeight = EditText((x, y, 40, 22), "",
                                      sizeStyle="small", callback=self.calcItalicCallback)
        x += 50
        self.w.crossHeightSetUC = Button((x, y, 65, 22), 'Mid UC',
                                         sizeStyle="small", callback=self.calcItalicCallback)
        x += 75
        self.w.crossHeightSetLC = Button((x, y, 65, 22), 'Mid LC',
                                         sizeStyle="small", callback=self.calcItalicCallback)

        y += 30
        x = 10
        self.w.italicSlantOffsetLabel = TextBox((x, y+4, 100, 22), 'Italic Slant Offset', sizeStyle="small")
        x += 100
        self.w.italicSlantOffset = EditText((x, y, 40, 22), "",
                                            sizeStyle="small", callback=self.calcItalicCallback)
        x += 60

        y += 30
        x = 10
        self.w.refresh = Button((x, y, 140, 22), u'Values from Current', callback=self.refresh, sizeStyle="small")

        y += 30

        self.w.fontSelection = RadioGroup((x, y, 120, 35), ['Current Font', 'All Fonts'], sizeStyle="small")
        self.w.fontSelection.set(0)

        x += 160
        self.w.glyphSelection = RadioGroup((x, y, 120, 55),
                                           ['Current Glyph', 'Selected Glyphs', 'All Glyphs'],
                                           sizeStyle="small")
        self.w.glyphSelection.set(0)
        y += 60
        x = 10
        self.w.setInFont = Button((x, y, 140, 22), 'Set Font Italic Values',
                                  sizeStyle="small", callback=self.setInFontCallback)
        x += 160
        self.w.italicize = Button((x, y, 140, 22), 'Italicize Glyphs',
                                  sizeStyle="small", callback=self.italicizeCallback)
        y += 25
        self.w.makeReferenceLayer = CheckBox((x, y, 145, 22), 'Make Reference Layer',
                                             value=getExtensionDefault(DEFAULT_KEY_REFERENCE, False),
                                             sizeStyle="small", callback=self.makeReferenceLayerCallback)
        x = 10

        self.refresh()
        if self.getItalicAngle() == 0 and CurrentFont() is not None:
            self.setCrossHeight((CurrentFont().info.capHeight or 0) / 2)

    def refresh(self, sender=None):
        f = CurrentFont()
        if f:
            italicSlantOffset = f.lib.get(ITALIC_SLANT_OFFSET_KEY) or 0
            italicAngle = f.info.italicAngle or 0
            crossHeight = calcCrossHeight(italicAngle=italicAngle,
                                                    italicSlantOffset=italicSlantOffset)
            self.setItalicSlantOffset(italicSlantOffset)
            self.setItalicAngle(italicAngle)
            self.setCrossHeight(crossHeight)
        else:
            self.setItalicSlantOffset(0)
            self.setItalicAngle(0)
            self.setCrossHeight(0)

        postEvent(f"{DEFAULT_KEY}.updateGlyphEditor",
                  italicAngle=self.getItalicAngle(),
                  italicSlantOffset=self.getItalicSlantOffset(),
                  crossHeight=self.getCrossHeight())

    def setInFontCallback(self, sender):
        if self.w.fontSelection.get() == 0:
            if CurrentFont() is not None:
                fonts = [CurrentFont()]
            else:
                fonts = []
        else:
            fonts = AllFonts()
        for f in fonts:
            with f.undo('italicBowtie'):
                f.info.italicAngle = self.getItalicAngle()
                f.lib[ITALIC_SLANT_OFFSET_KEY] = self.getItalicSlantOffset()
        try:
            window = CurrentGlyphWindow()
            window.setGlyph(CurrentGlyph().naked())
        except Exception:
            print(DEFAULT_KEY, 'error resetting window, please refresh it')

        postEvent(f"{DEFAULT_KEY}.updateGlyphEditor",
                  italicAngle=self.getItalicAngle(),
                  italicSlantOffset=self.getItalicSlantOffset(),
                  crossHeight=self.getCrossHeight())

    def calcItalicCallback(self, sender):
        italicAngle = self.getItalicAngle()
        italicSlantOffset = self.getItalicSlantOffset()

        font = CurrentFont()
        if sender == self.w.crossHeightSetUC and font is not None:
            crossHeight = (font.info.capHeight or 0) / 2.0
            sender = self.w.crossHeight
        elif sender == self.w.crossHeightSetLC and font is not None:
            crossHeight = (font.info.xHeight or 0) / 2.0
            sender = self.w.crossHeight
        else:
            crossHeight = self.getCrossHeight()
        if sender == self.w.italicAngle or sender == self.w.italicSlantOffset:
            self.setCrossHeight(calcCrossHeight(italicAngle=italicAngle, italicSlantOffset=italicSlantOffset))
        elif sender == self.w.crossHeight:
            self.setItalicSlantOffset(calcItalicSlantOffset(italicAngle=italicAngle, crossHeight=crossHeight))
            self.setCrossHeight(crossHeight)

        postEvent(f"{DEFAULT_KEY}.updateGlyphEditor",
                  italicAngle=italicAngle,
                  italicSlantOffset=italicSlantOffset,
                  crossHeight=crossHeight)

    def italicizeCallback(self, sender=None):
        italicAngle = self.getItalicAngle()
        italicSlantOffset = self.getItalicSlantOffset()
        if self.w.fontSelection.get() == 0:
            if CurrentFont() is not None:
                fonts = [CurrentFont()]
            else:
                fonts = []
        else:
            fonts = AllFonts()

        if self.w.glyphSelection.get() == 0 and CurrentGlyph() is not None:
            glyphs = [CurrentGlyph()]
        elif self.w.glyphSelection.get() == 1:
            glyphs = []
            for f in fonts:
                for gname in CurrentFont().selection:
                    if gname in f:
                        glyphs.append(f[gname])
        else:
            glyphs = []
            for f in fonts:
                for g in f:
                    glyphs.append(g.name)

        for glyph in glyphs:
            italicize(glyph, italicAngle,
                      offset=italicSlantOffset,
                      shouldMakeReferenceLayer=self.w.makeReferenceLayer.get())

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

    def makeReferenceLayerCallback(self, sender):
        setExtensionDefault(DEFAULT_KEY_REFERENCE, sender.get())

    def windowWillClose(self, window):
        postEvent(f"{DEFAULT_KEY}.removeBowtie")


class ItalicBowtie(Subscriber):

    debug = True

    italicAngle = 0
    italicSlantOffset = 0
    crossHeight = 0

    def build(self):
        glyphEditor = self.getGlyphEditor()
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

    def destroy(self):
        self.container.clearSublayers()

    def italicBowtieUpdateGlyphEditor(self, info):
        self.italicAngle = info['lowLevelEvents'][0]['italicAngle']
        self.italicSlantOffset = info['lowLevelEvents'][0]['italicSlantOffset']
        self.crossHeight = info['lowLevelEvents'][0]['crossHeight']
        self.updateBowtie()

    def italicBowtieRemoveBowtie(self, info):
        self.terminate()

    def glyphEditorGlyphDidChange(self, info):
        self.updateBowtie()

    def glyphEditorDidSetGlyph(self, info):
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

    def updateBowtie(self):
        glyph = CurrentGlyph()
        ascender = glyph.font.info.ascender
        descender = glyph.font.info.descender
        italicSlantOffsetOffset = self.italicSlantOffset
        for xoffset, layer in [(0, self.leftBowtieLayer), (glyph.width, self.rightBowtieLayer)]:
            self.drawItalicBowtie(layer=layer,
                                  italicAngle=self.italicAngle,
                                  crossHeight=self.crossHeight,
                                  ascender=ascender,
                                  descender=descender,
                                  italicSlantOffset=italicSlantOffsetOffset,
                                  xoffset=xoffset)
        # crossheight
        self.crossHeightLayer.setStartPoint((0, self.crossHeight))
        self.crossHeightLayer.setEndPoint((glyph.width, self.crossHeight))


if __name__ == '__main__':

    if f"{DEFAULT_KEY}.updateGlyphEditor" not in roboFontSubscriberEventRegistry:
        registerSubscriberEvent(
            subscriberEventName=f"{DEFAULT_KEY}.updateGlyphEditor",
            methodName="italicBowtieUpdateGlyphEditor",
            lowLevelEventNames=[f"{DEFAULT_KEY}.updateGlyphEditor"],
            dispatcher="roboFont",
            delay=0.02,
        )

        registerSubscriberEvent(
            subscriberEventName=f"{DEFAULT_KEY}.removeBowtie",
            methodName="italicBowtieRemoveBowtie",
            lowLevelEventNames=[f"{DEFAULT_KEY}.removeBowtie"],
            dispatcher="roboFont",
            delay=0,
        )

    OpenWindow(ItalicBowtieController)
    registerGlyphEditorSubscriber(ItalicBowtie)
