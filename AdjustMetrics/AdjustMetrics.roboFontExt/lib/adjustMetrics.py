# -*- coding: UTF-8 -*-  
#
# ----------------------------------------------------------------------------------
from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController
from AppKit import *
import os.path
from builtins import chr
from mojo.roboFont import version

def sortFonts(fonts):
    """
    Some day I will implement this.
    """
    return fonts

    # ---------------------------------------------------------------------------------------------------------
    #    A D J U S T  M E T R I C S
    #
    # Adjust metrics.
    #
    """
    
    Adjust both margins, left margin, or right margin
    To current glyph selection or all glyphs
    In current font or a selection of opened fonts
    
    Options:
        
        Adjust components (on by default): If 'A' is selected but not 'Aacute', 'Aacute' will be shifted back so it does not affect the original position.
    
        Adjust Comps with Selected (off by default): If 'A' is selected, also transform 'Aacute' et. al.
    
    """

def addMargins(f, gnames=[], leftUnits=0, rightUnits=0, adjustComponents=True):
    for gname in gnames:
        if gname in f:
            g = f[gname]
            g.prepareUndo('addMargins')
            # do left side
            if leftUnits != 0:
                # RF3
                if version >= "3.0.0":
                    if g.bounds:
                        g.leftMargin += leftUnits
                    else:
                        g.width += leftUnits
                # RF1
                else:
                    if g.box:
                        g.leftMargin += leftUnits
                    else:
                        g.width += leftUnits

                if adjustComponents:
                    for comp in g.components:
                        if comp.baseGlyph in gnames:
                            comp.offset = (comp.offset[0]-leftUnits, comp.offset[1])
                    #print('adjusting', g, 'leftMargin by', leftUnits, 'units')
            if rightUnits != 0:
                # RF3
                if version >= "3.0.0":
                    if g.bounds:
                        g.rightMargin += rightUnits
                    else:
                        g.width += rightUnits
                # RF1
                else:
                    if g.box:
                        g.rightMargin += rightUnits
                    else:
                        g.width += rightUnits
            g.performUndo()
    
def multiplyMargins(f, gnames, leftMultiplier=1, rightMultiplier=1, roundValues=1, adjustComponents=True):
    marginRecords = {}
    # Step 1: Compile records
    for gname in gnames:
        leftUnits, rightUnits = 0, 0
        if gname in f:
            g = f[gname]
            if leftMultiplier != 1:
                leftUnits = (leftMultiplier * g.leftMargin) - g.leftMargin
            if rightMultiplier != 1:
                rightUnits = (rightMultiplier * g.rightMargin ) - g.rightMargin
            if roundValues != 0:
                leftUnits = round(leftUnits, roundValues)
                rightUnits = round(rightUnits, roundValues)
            marginRecords[g.name] = leftUnits, rightUnits
    # Make changes
    for gname in gnames:
        if gname in f:
            g = f[gname]
            g.prepareUndo('multiplyMargins')
            leftUnits, rightUnits = marginRecords[gname]
            g.leftMargin += leftUnits
            g.rightMargin += rightUnits
            if adjustComponents:
                for comp in g.components:
                    if comp.baseGlyph in gnames:
                        compLeftUnits, compRightUnits = marginRecords[comp.baseGlyph]
                        comp.offset = (comp.offset[0]-compLeftUnits, comp.offset[1])
            g.performUndo()

class AdjustMetrics(BaseWindowController):

    WINDOWTITLE                  = u'Adjust Metrics'

    def __init__(self):
        
        #layout variables
        width = 250
        height = 500
        x = 20
        y = 20
        rightMargin = -20
        itemHeight = 22
        lineHeight = 25

        fonts = AllFonts()
        self.fonts = sortFonts(fonts)
        current = CurrentFont()

        # Window
                
        self.w = Window((width, height), self.WINDOWTITLE, autosaveName=self.WINDOWTITLE, minSize=(width, height))
                
        # Adjust Both
        self.w.adjustBothText = TextBox((x, y, rightMargin, itemHeight), 'Adjust Both Margins')
        y+=lineHeight
        self.w.adjustBothValue = EditText((x, y, 50, itemHeight), callback=self.adjustBothValueCallback)
        x+=60
        self.w.adjustBothUnit = RadioGroup((x, y, 120, itemHeight*2), ['Units', 'Percent'], callback=self.adjustBothUnitCallback)
        self.w.adjustBothUnit.set(0)
        x = 20
        y += lineHeight * 2.5

        # Adjust Left
        self.w.adjustLeftText = TextBox((x, y, rightMargin, itemHeight), 'Adjust Left Margin')
        y+=lineHeight
        self.w.adjustLeftValue = EditText((x, y, 50, itemHeight), callback=self.clearBothCallback)
        x+=60
        self.w.adjustLeftUnit = RadioGroup((x, y, 120, itemHeight*2), ['Units', 'Percent'], callback=self.clearBothCallback)
        self.w.adjustLeftUnit.set(0)
        x = 20
        y += lineHeight * 2.5       

        # Adjust Right
        self.w.adjustRightText = TextBox((x, y, rightMargin, itemHeight), 'Adjust Right Margin')
        y+=lineHeight
        self.w.adjustRightValue = EditText((x, y, 50, itemHeight), callback=self.clearBothCallback)
        x+=60
        self.w.adjustRightUnit = RadioGroup((x, y-3, 120, itemHeight*2), ['Units', 'Percent'], callback=self.clearBothCallback)
        self.w.adjustRightUnit.set(0)
        x = 20
        y += lineHeight * 2.5
 
        # Glyph Selection
        self.w.glyphSelection = RadioGroup((x, y, rightMargin, itemHeight*2), ['Current Glyph Selection', 'All Glyphs'])
        self.w.glyphSelection.set(0)

        y += lineHeight * 2.5

        # Components
        self.w.adjustComponents = CheckBox((x, y, rightMargin, itemHeight), 'Adjust Components')
        self.w.adjustComponents.set(1)

        y += lineHeight
        
        # Transform
        self.w.adjustBaseComponents = CheckBox((x, y, rightMargin, itemHeight), 'Adjust Comps with Selected')
        self.w.adjustBaseComponents.set(0)
        
        y += lineHeight
        
        # Transform
        self.w.ignoreZeroWidth = CheckBox((x, y, rightMargin, itemHeight), 'Ignore Zero-Width Glyphs')
        self.w.ignoreZeroWidth.set(1)
        
        self.w.apply = Button((x, -40, 100, itemHeight), 'Apply', callback=self.apply)
        self.w.cancel = Button((x+110, -40, 100, itemHeight), 'Close', callback=self.cancel)
        
        # Font Selection Drawer

        self.fs = Drawer((200, 150), self.w)
        fsx = 5
        fsy = 5
        
        self.fs.selectAllFonts = Button((fsx, fsy, -55, itemHeight), 'Select All Fonts', callback=self.selectAllFonts, sizeStyle='small')
        self.fs.refreshFontList = Button((-35, fsy, 30, 22), chr(8634), callback=self.refreshFontList)

        fsy += 25
        self.fs.deselectAllFonts = Button((fsx, fsy, -55, itemHeight), 'Deselect All Fonts', callback=self.deselectAllFonts, sizeStyle='small')
        fsy += 25
        self.fs.selectCurrentFont = Button((fsx, fsy, -55, itemHeight), 'Select Current Font', callback=self.selectCurrentFont, sizeStyle='small')
        fsy += 25

        fontNameList = []
        currentIndex = None
        for x, f in enumerate(self.fonts):
            fontName = str(f.info.familyName)+' '+str(f.info.styleName)
            if fontName in fontNameList:
                fontName = f.path
            fontNameList.append(fontName)
            if f == CurrentFont():
                currentIndex = x
        fsy += 5
        self.fs.fontSelect = List((fsx, fsy, -5, -5), fontNameList)
        if currentIndex is not None:
            self.fs.fontSelect.setSelection([currentIndex])
        
        self.w.open()
        self.fs.open()

    def refreshFontList(self, sender):
        self.fonts = sortFonts(AllFonts())
        fontNameList = []
        currentIndex = None
        for x, f in enumerate(self.fonts):
            fontName = str(f.info.familyName)+' '+str(f.info.styleName)
            if fontName in fontNameList:
                fontName = f.path
            fontNameList.append(fontName)
            if f == CurrentFont():
                currentIndex = x
        self.fs.fontSelect.set(fontNameList)
        self.fs.fontSelect.setSelection([currentIndex])
    
    def adjustBothUnitCallback(self, sender):
        self.w.adjustLeftUnit.set(sender.get())
        self.w.adjustRightUnit.set(sender.get())
        
    def adjustBothValueCallback(self, sender):
        self.w.adjustLeftValue.set(sender.get())
        self.w.adjustRightValue.set(sender.get())
    
    def clearBothCallback(self, sender):
        self.w.adjustBothValue.set('')
     
    def selectAllFonts(self, sender):
        indexRange = range(0, len(self.fonts))
        self.fs.fontSelect.setSelection(indexRange)

    def deselectAllFonts(self, sender):
        self.fs.fontSelect.setSelection([])

    def selectCurrentFont(self, sender):
        for x, f in enumerate(self.fonts):
            if f == CurrentFont():
                currentIndex = x
        self.fs.fontSelect.setSelection([currentIndex])

    def getSelectedFonts(self):
        selectedFonts = []
        for index in self.fs.fontSelect.getSelection():
            selectedFonts.append(self.fonts[index])
        return selectedFonts

    def makeMetricsAdjustment(self, f, gnames):
        """
        """
        if self.w.ignoreZeroWidth.get():
            newGnames = []
            for gname in gnames:
                if f[gname].width != 0:
                    newGnames.append(gname)
            gnames = newGnames
        
        if self.w.adjustComponents.get():
            adjustComponents = True
        else:
            adjustComponents = False
        # get values
        adjustLeftUnit = self.w.adjustLeftUnit.get()
        adjustRightUnit = self.w.adjustRightUnit.get()

        try:
            leftValue = int(self.w.adjustLeftValue.get())
        except:
            if adjustLeftUnit == 0:
                leftValue = 0
            else:
                leftValue = 1
        try:
            rightValue = int(self.w.adjustRightValue.get())
        except:
            if adjustRightUnit == 0:
                rightValue = 0
            else:
                rightValue = 1
        
        if adjustLeftUnit == 0:
            if adjustRightUnit == 0:
                addMargins(f, gnames, leftValue, rightValue, adjustComponents=adjustComponents)
            else:
                addMargins(f, gnames, leftValue, 0, adjustComponents=adjustComponents)    
                multiplyMargins(f, gnames, 1, rightValue*.01, adjustComponents=adjustComponents)    
        if adjustLeftUnit == 1:
            if adjustRightUnit == 1:
                multiplyMargins(f, gnames, leftValue*.01, rightValue*.01, adjustComponents=adjustComponents)
            else:
                multiplyMargins(f, gnames, leftValue*.01, 1, adjustComponents=adjustComponents)    
                addMargins(f, gnames, 0, rightValue, adjustComponents=adjustComponents)    
        f.update()
  

  
    def apply(self, sender):

        fonts = self.getSelectedFonts()
                
        for f in fonts:

            if self.w.glyphSelection.get() == 0:
                gnames = CurrentFont().selection
            else:
                gnames = f._object.keys()
                
        
            if self.w.adjustBaseComponents.get():
                additionalGnames = []
                for g in f:
                    if len(g.components) >= 1 and ( g.components[0].baseGlyph in gnames ) and ( g.name not in gnames ):
                        additionalGnames.append(g.name)
                gnames += additionalGnames
                        
            print(f, gnames)
            self.makeMetricsAdjustment(f, gnames)
                       
    def cancel(self, sender):
        self.w.close()

OpenWindow(AdjustMetrics)

