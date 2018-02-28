#coding=utf-8
###########
# BOUNDING TOOL
###########
# BY DJR, with help from Nina Stössinger. Thanks Nina!

# I should probably redo this at some point using angled point instead of doing the math myself. Next time...

from mojo.UI import CurrentGlyphWindow, UpdateCurrentGlyphView
from mojo.events import BaseEventTool, installTool, EditingTool
from AppKit import *
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.drawingTools import *
from mojo.extensions import ExtensionBundle
from vanilla import *
from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor
from lib.tools.defaults import getDefault
from lib.tools import bezierTools
from mojo.roboFont import version

bundle = ExtensionBundle("BoundingTool")
toolbarIcon = bundle.getResourceImage("boundingTool")
try:
    toolbarIcon.setSize_((16, 16))
except:
    pass

class TX:
    
    @classmethod
    def formatStringValue(cls, f): return format(f, '.1f').rstrip('0').rstrip('.')    
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
    def getItalicshowCoordinates(cls, coords, italicAngle):
        """
        Given (x, y) coords and an italic angle, get new showCoordinates accounting for italic offset.
        """
        x, y = coords
        x += cls.getItalicOffset(y, italicAngle)
        return x, y

class BoundingTool(EditingTool, BaseWindowController):
    slantPointCoordinates = int(getDefault("glyphViewShouldSlantPointCoordinates"))
    offsetPointCoordinates = getDefault("glyphViewShouldOffsetPointCoordinates")

    DEFAULTKEY = "com.fontbureau.boundingTool"
    DEFAULTKEY_FILLCOLOR = "%s.fillColor" %DEFAULTKEY
    DEFAULTKEY_STROKECOLOR = "%s.strokeColor" %DEFAULTKEY
    DEFAULTKEY_SHOWCOORDINATES = "%s.showCoordinates" %DEFAULTKEY
    DEFAULTKEY_SHOWDIMENSIONS = "%s.showCoordinates" %DEFAULTKEY
    DEFAULTKEY_SELECTION = "%s.selection" %DEFAULTKEY
    DEFAULTKEY_DIVISIONSX = "%s.divisionsX" %DEFAULTKEY
    DEFAULTKEY_DIVISIONSY = "%s.divisionsY" %DEFAULTKEY
    DEFAULTKEY_USEITALIC = "%s.useItalic" %DEFAULTKEY
    FALLBACK_FILLCOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, .5, .3)
    FALLBACK_STROKECOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, .5, .5)
    VERSION = 1.0
    NAME = u'Bounding Tool'
    MANUAL = u"""TK"""



    color = (1, 0, .2)
    alpha = 1
    divisionsStringList = ['1', '2', '3', '4']
    divisionsList = [1, 2, 3, 4]
    
    def getToolbarTip(self):
        return self.NAME
        
    def getToolbarIcon(self):
        return toolbarIcon

    def getBox(self, selected=True):
        g = self.getGlyph()
        # RF3
        if version >= "3.0.0":
            gbox = g.bounds
        # RF1
        else:
            gbox = g.box
        if g is not None and gbox is not None:
            n = g
            if selected:
                hasSelection = False
                copyGlyph = g.naked().selection.getCopyGlyph()
                if copyGlyph and copyGlyph[1].get('contours'):
                    n = RGlyph(copyGlyph[0])
                else:
                    n = g
            if self.w.useItalic.get():
                italicAngle = g.getParent().info.italicAngle or 0
                # RF3
                if version >= "3.0.0":
                    nbox = n.bounds
                # RF1
                else:
                    nbox = n.box
                if nbox:
                    boxTop = nbox[3]
                    boxBottom = nbox[1]
                    boxWidth = nbox[2] - nbox[0]
                else:
                    boxTop = g.getParent().info.ascender
                    boxBottom = g.getParent().info.descender
                    boxWidth = g.width
                #print n.angledLeftMargin, g.getParent().lib.get('com.typemytype.robofont.italicSlantOffset')
                try:
                    leftX = n.angledLeftMargin or 0 + g.getParent().lib.get('com.typemytype.robofont.italicSlantOffset') or 0
                    rightX = n.width - n.angledRightMargin or 0 + g.getParent().lib.get('com.typemytype.robofont.italicSlantOffset') or 0
                except:
                    leftX = rightX = 0

                topY = nbox[3]
                bottomY = nbox[1]

                topX = TX.getItalicOffset(topY, italicAngle)
                bottomX = TX.getItalicOffset(bottomY, italicAngle)
                
                box = (
                (leftX+bottomX, bottomY), # bottom left
                (leftX+topX, topY), # top left
                (rightX+topX, topY), # top right
                (rightX+bottomX, bottomY), # bottom right
                (n.naked().angledBounds[2]-n.naked().angledBounds[0], n.naked().angledBounds[3]-n.naked().angledBounds[1])
                )
            else:
                # RF3
                if version >= "3.0.0":
                    nbox = n.bounds
                # RF1
                else:
                    nbox = n.box
                box = (
                    (nbox[0], nbox[1]),
                    (nbox[0], nbox[3]),
                    (nbox[2], nbox[3]),
                    (nbox[2], nbox[1]),
                    (nbox[2]-nbox[0], nbox[3]-nbox[1])
                    ) 
        else:
            box = None #((0, 0), (0, 0), (0, 0), (0, 0), (0, 0))
        return box


    def drawBackground(self, scale):
        g = self.getGlyph()
        self.fillColor.setFill()
        
        slantCoordinates = self.slantPointCoordinates
        italicSlantOffset = 0
        if self.offsetPointCoordinates:
            italicSlantOffset = g.getParent().lib.get('com.typemytype.robofont.italicSlantOffset') or 0
        color = self.fillColor.colorUsingColorSpaceName_(NSCalibratedRGBColorSpace)
        red = color.redComponent()
        green = color.greenComponent()
        blue = color.blueComponent()
        alpha = color.alphaComponent()
        fill(red, green, blue, alpha)
        stroke(red, green, blue, alpha)
        strokeWidth(1*scale)
        # RF3
        if version >= "3.0.0":
            lineDash(1)
        # RF1?
        else:
            dashLine(1)
        fontSizeValue = 8
        fontSize(fontSizeValue*scale)
        
        showCoordinates = self.w.showCoordinates.get()
        showDimensions = self.w.showDimensions.get()
        
        selectedBox = self.getBox(selected=True)
        
        if selectedBox:
            # switch them around so that we draw a line perpindicular to the axis we want to subdivide
            divisionsY = int(self.w.divisionsRadioX.get())
            divisionsX = int(self.w.divisionsRadioY.get())
            
            pt1, pt2, pt3, pt4, dimensions = selectedBox
            pt1X, pt1Y = pt1 # bottom left
            pt2X, pt2Y = pt2 # top left
            pt3X, pt3Y = pt3 # top right
            pt4X, pt4Y = pt4 # bottom right
            
            pt1X += italicSlantOffset
            pt2X += italicSlantOffset
            pt3X += italicSlantOffset
            pt4X += italicSlantOffset

            width, height = dimensions
            startRectX = pt1X
            startRectY = pt1Y
            rectWidth = width / float(divisionsY)
            rectHeight = height / float(divisionsX)
            if self.w.useItalic.get():
                italicAngle = g.getParent().info.italicAngle or 0
            else:
                italicAngle = 0
            margin = 0
            f = g.getParent()
            asc = f.info.ascender + f.info.unitsPerEm
            desc = f.info.descender - f.info.unitsPerEm
        
            ascOffset = TX.getItalicOffset(asc-pt3Y, italicAngle)
            descOffset = TX.getItalicOffset(desc-pt1Y, italicAngle)

            line((pt1X+descOffset, desc), (pt2X+ascOffset, asc))
            line((pt4X+descOffset, desc), (pt3X+ascOffset, asc))

            line((pt1X-f.info.unitsPerEm, pt1Y), (pt4X+f.info.unitsPerEm, pt1Y))
            line((pt2X-f.info.unitsPerEm, pt2Y), (pt3X+f.info.unitsPerEm, pt2Y))
            
            margin = 10*scale #((width + height) / 2) / 20
            
            
            if showDimensions:
                widthYBump = 0
                if italicAngle:
                    widthYBump = 20*scale

                widthString = 'w: %s' %(TX.formatStringValue(width))
                widthXPos = pt2X+(width/2.0)+TX.getItalicOffset(margin, italicAngle)-10*scale 
                widthYPos = pt2Y+margin+widthYBump               
                if divisionsY > 1:
                    subWidthString = '    %s' %(TX.formatStringValue(width/divisionsY))
                    text(subWidthString, (widthXPos, widthYPos))
                    widthYPos += fontSizeValue*scale
                font("LucidaGrande-Bold")
                text(widthString,
                (widthXPos,
                widthYPos))
                
            if divisionsY >= 1:
                xoffset = pt1X
                for divY in range(divisionsY+1):
                    if divY != 0 and divY != divisionsY:
                        line( 
                            (xoffset-TX.getItalicOffset(margin, italicAngle),
                            pt1Y-margin),
                            (xoffset + TX.getItalicOffset(pt2Y-pt1Y, italicAngle) + TX.getItalicOffset(margin, italicAngle),
                            pt3Y+margin)
                            )
                    if showCoordinates:
                        font("LucidaGrande")
                        x, y = bezierTools.angledPoint((xoffset, pt1Y), italicAngle, roundValue=italicAngle, reverse=-1)
                        text('%s' %(TX.formatStringValue(x-italicSlantOffset)), (xoffset-TX.getItalicOffset(margin, italicAngle)+2*scale, pt1Y-margin-fontSizeValue))
                        if italicAngle != 0:
                            x, y = bezierTools.angledPoint((xoffset, pt1Y), italicAngle, roundValue=italicAngle, reverse=-1)
                            text('%s' %(TX.formatStringValue(x-italicSlantOffset)), (xoffset+TX.getItalicOffset(pt3Y-pt1Y, italicAngle)+TX.getItalicOffset(margin, italicAngle)+2*scale, pt3Y+margin))
                    xoffset += rectWidth

            ###################
            ###################
            ###################
            ###################
            margin = 10*scale

            if showDimensions:
                heightString = 'h: %s' %(TX.formatStringValue(height))
                heightXPos = pt4X + TX.getItalicOffset(height/2.0, italicAngle) + margin
                heightYPos = pt4Y+(height/2.0)-fontSizeValue/2

                if divisionsX > 1:
                    heightYPos -= fontSizeValue*scale/2
                    subHeightString = '    %s' %(TX.formatStringValue(height/divisionsX))
                    text(
                        subHeightString,
                        (heightXPos,
                        heightYPos),
                        )
                    heightYPos += fontSizeValue*scale
                
                font("LucidaGrande-Bold")
                text(heightString, 
                (heightXPos,
                heightYPos)
                )
            if divisionsX >= 1:
                yoffset = pt1Y
                for divX in range(divisionsX+1):
                    if divX != 0 and divX != divisionsX:
                        line( 
                            (pt1X + TX.getItalicOffset(yoffset-pt1Y, italicAngle) - margin,
                            yoffset),
                            (pt1X + TX.getItalicOffset(yoffset-pt1Y, italicAngle) + width + margin,
                            yoffset)
                            )
                    if showCoordinates:
                        font("LucidaGrande")
                        text('%s' %(TX.formatStringValue(yoffset)), 
                        (pt1X + TX.getItalicOffset(yoffset-pt1Y, italicAngle) - margin - 14*scale, 
                        yoffset))
                    yoffset += rectHeight
            
                        
            
    def becomeActive(self):
        """
        Boot up the dialog.
        """
        
        self.fillColor = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)
        self.strokeColor = getExtensionDefaultColor(self.DEFAULTKEY_STROKECOLOR, self.FALLBACK_STROKECOLOR)
        
        self.w = FloatingWindow((260, 130), "Bounding Options", minSize=(100, 100), closable=False)

        self.w.viewOptions = RadioGroup((10, 10, 150, 20),
                                        ['Selection', 'Glyph'],
                                        callback=self.selectionCallback, isVertical=False, sizeStyle="small")
        self.w.viewOptions.set(getExtensionDefault(self.DEFAULTKEY_SELECTION, 0))
        
        self.w.useItalic = CheckBox((165, 10, 100, 20), "Use Italic", value=getExtensionDefault(self.DEFAULTKEY_USEITALIC, True), sizeStyle="small", callback=self.useItalicCallback)

        self.w.xLabel = TextBox((10, 40, 70, 20), "Divisions: X", sizeStyle="small")

        self.w.divisionsRadioX = Slider((80, 40, 70, 30),
        value=getExtensionDefault(self.DEFAULTKEY_DIVISIONSX, 1),
        minValue=1,
        maxValue=4,
        tickMarkCount=4,
        stopOnTickMarks=True,
        continuous=True,
        sizeStyle="small",
        callback=self.divisionsXCallback)

        self.w.yLabel = TextBox((160, 40, 70, 20), "Y", sizeStyle="small")
        self.w.divisionsRadioY = Slider((175, 40, 70, 30),
        value=getExtensionDefault(self.DEFAULTKEY_DIVISIONSY, 1),
        minValue=1,
        maxValue=4,
        tickMarkCount=4,
        stopOnTickMarks=True,
        continuous=True,
        sizeStyle="small",
        callback=self.divisionsYCallback)

        self.w.drawGuidesButton = Button((10, 100, 90, 20), 'Div Guides', callback=self.drawDivGuides, sizeStyle="small")
        self.w.drawBoxGuidesButton = Button((120, 100, 90, 20), 'Box Guides', callback=self.drawBoxGuides, sizeStyle="small",)
            

        x = 10
        y = 70
        self.w.showCoordinates = CheckBox((x, y, 90, 20), "Coordinates", value=getExtensionDefault(self.DEFAULTKEY_SHOWCOORDINATES, True), sizeStyle="small", callback=self.showCoordinatesCallback)
        x += 90
        self.w.showDimensions = CheckBox((x, y, 90, 20), "Dimensions", value=getExtensionDefault(self.DEFAULTKEY_SHOWDIMENSIONS, True), sizeStyle="small", callback=self.showDimensionsCallback)
            
        
        x += 90
        color = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)
        self.w.color = ColorWell((x, y, 30, 22), 
                color=color,
                callback=self.colorCallback)

        self.setUpBaseWindowBehavior()
        self.w.open()
        
    def becomeInactive(self):
        """
        Remove the dialog when the tool is inactive.
        """
        self.windowCloseCallback(None)
        self.w.close()
        
    def colorCallback(self, sender):
        """
        Change the color.
        """
        selectedColor = sender.get()
        r = selectedColor.redComponent()
        g = selectedColor.greenComponent()
        b = selectedColor.blueComponent()
        a = 1
        strokeColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)
        setExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, selectedColor)
        setExtensionDefaultColor(self.DEFAULTKEY_STROKECOLOR, strokeColor)
        self.fillColor = selectedColor
        self.strokeColor = strokeColor
        self.updateView()

    def showCoordinatesCallback(self, sender):
        setExtensionDefault(self.DEFAULTKEY_SHOWCOORDINATES, sender.get())
        self.updateView()

    def showDimensionsCallback(self, sender):
        setExtensionDefault(self.DEFAULTKEY_SHOWDIMENSIONS, sender.get())
        self.updateView()

    def divisionsXCallback(self, sender):
        setExtensionDefault(self.DEFAULTKEY_DIVISIONSX, sender.get())
        self.updateView()

    def divisionsYCallback(self, sender):
        setExtensionDefault(self.DEFAULTKEY_DIVISIONSY, sender.get())
        self.updateView()

    def selectionCallback(self, sender):
        setExtensionDefault(self.DEFAULTKEY_SELECTION, sender.get())
        self.updateView()

    def useItalicCallback(self, sender):
        setExtensionDefault(self.DEFAULTKEY_USEITALIC, sender.get())
        self.updateView()

    def drawDivGuides(self, sender):
        """
        Draw guidelines for the current divisions.
        """
        g = self.getGlyph()
        if self.w.viewOptions.get() == 0:
            selectedBox = self.getBox(selected=True)
        else:
            selectedBox = self.getBox(selected=False)
        if selectedBox:
            divisionsX = int(self.w.divisionsRadioY.get())
            divisionsY = int(self.w.divisionsRadioX.get())
            pt1, pt2, pt3, pt4, dimensions = selectedBox
            pt1X, pt1Y = pt1 # bottom left
            pt2X, pt2Y = pt2 # top left
            pt3X, pt3Y = pt3 # top right
            pt4X, pt4Y = pt4 # bottom right
            width, height = dimensions
            italicAngle = 0
            if self.w.useItalic.get():
                italicAngle = g.getParent().info.italicAngle or 0
            g.prepareUndo()
            offset = pt1X
            advance = float(width) / divisionsX
            for i in range(divisionsX-1):
                xmid = offset + advance
                # RF3
                if version >= "3.0.0":
                    g.appendGuideline((xmid, pt1Y), 90+italicAngle)
                # RF1
                else:
                    g.addGuide((xmid, pt1Y), 90+italicAngle)
                offset += advance
            offset = pt1Y
            advance = float(height) / divisionsY
            for i in range(divisionsY-1):
                ymid = offset + advance
                # RF3
                if version >= "3.0.0":
                    g.appendGuideline((pt1X, ymid), 0)
                # RF1
                else:
                    g.addGuide((pt1X, ymid), 0)
                offset += advance
            g.performUndo()
                    
    def drawBoxGuides(self, sender):
        """
        Draw guidelines for the current box.
        """
        g = self.getGlyph()
        selectedBox = self.getBox(selected=True)
        if selectedBox:
            divisionsX = int(self.w.divisionsRadioY.get())
            divisionsY = int(self.w.divisionsRadioX.get())
            pt1, pt2, pt3, pt4, dimensions = selectedBox
            pt1X, pt1Y = pt1 # bottom left
            pt2X, pt2Y = pt2 # top left
            pt3X, pt3Y = pt3 # top right
            pt4X, pt4Y = pt4 # bottom right
            width, height = dimensions
            italicAngle = 0
            if self.w.useItalic.get():
                italicAngle = g.getParent().info.italicAngle or 0
            g.prepareUndo()
            #if self.w.viewX.get():
            # RF3
            if version >= "3.0.0":
                g.appendGuideline((pt1X, pt1Y), 90+italicAngle)
                g.appendGuideline((pt3X, pt3Y), 90+italicAngle)
            # RF1
            else:
                g.addGuide((pt1X, pt1Y), 90+italicAngle)
                g.addGuide((pt3X, pt3Y), 90+italicAngle)
            #if self.w.viewY.get():
            # RF3
            if version >= "3.0.0":
                g.appendGuideline((pt1X, pt1Y), 0)
                g.appendGuideline((pt3X, pt3Y), 0)
            # RF1
            else:
                g.addGuide((pt1X, pt1Y), 0)
                g.addGuide((pt3X, pt3Y), 0)
            g.performUndo()

    def updateView(self, sender=None):
        UpdateCurrentGlyphView()
        

    
installTool(BoundingTool())