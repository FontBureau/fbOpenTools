from mojo.UI import CurrentGlyphWindow, UpdateCurrentGlyphView
from mojo.events import addObserver, removeObserver
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.drawingTools import *
from AppKit import * #@PydevCodeAnalysisIgnore
from vanilla import * #@PydevCodeAnalysisIgnore 

import unicodedata
from lib.tools.drawing import strokePixelPath
from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor


#anchorMap = {
#'top': ['gravecmb', 'acutecmb', 'circumflexcmb', 'tildecmb', 'macroncmb', 'brevecmb', 'dotaccentcmb', 'dieresiscmb', 'ringcmb', 'hungarumlautcmb', 'caroncmb', 'commaturnedabovecmb', 'commaaccentcmb', 'cedillacmb', 'cyrillicbrevecmb', 'dieresistonoscmb', 'tonoscmb', 'caroncmb.salt'],

#'bottom': ['cedillacmb', 'commaaccentcmb', 'ogonekcmb']
#}

COMBINING2FLOATING = {
        768 : 96,
        769 : 180,
        770 : 710,
        771 : 732,
        #772 : 175,
        #773 : 175,
        774 : 728,
        775 : 729,
        776 : 168,
        778 : 730,
        779 : 733,
        780 : 711,
        807 : 184,
        808 : 731
        }
 
class OriginAnchor:
    name = "__Origin__"
    x = 0
    y = 0
   
class MojoGlyphDisplay:

    source = None

    def setSource(self, source):
        self.source = source
        
    def getSource(self):
        return self.source

    def setOffset(self, offset):
        self.offset = offset
        
    def getOffset(self):
        return self.offset

    def setScale(self, scale):
        self.scale = scale
        
    def getScale(self):
        return self.scale

    def drawGlyph(self, info={}, stroke=True, fill=True):
        glyph = self.getSource()
        translate(self.offset[0], self.offset[1])
        scale(self.scale[0], self.scale[1])
        drawGlyphPath = TX.naked(glyph).getRepresentation("defconAppKit.NSBezierPath")
        if fill:
            drawGlyphPath.fill()
        if stroke:
            strokePixelPath(drawGlyphPath)
        translate(-self.offset[0], -self.offset[1])
        scale(1/float(self.scale[0]), 1/float(self.scale[1]))

    def __init__(self, dest, source, offset=(0, 0), scale=(1, 1)):
        self.setSource(source)
        self.setOffset(offset)
        self.setScale(scale)

    def updateView(self, sender=None):
        UpdateCurrentGlyphView()
        
        
class TX:
    @classmethod
    def hex2dec(cls, s):
        	try:
        		return int(s, 16)
        	except:
        		pass
        		
    @classmethod
    def naked(cls, p):
        if hasattr(p, 'naked'):
            p = p.naked()
        return p
        
    @classmethod
    def hasAnchor(cls, anchorName, g):
        for a in g.anchors:
            if a.name == anchorName:
                return True
        return False
                
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
    def getItalicCoordinates(cls, coords, italicAngle):
        """
        Given (x, y) coords and an italic angle, get new coordinates accounting for italic offset.
        """
        x, y = coords
        x += cls.getItalicOffset(y, italicAngle)
        return x, y
                
class CharacterTX:
    
    @classmethod
    def char2Glyph(cls, char, f):
        d = ord(char)
        for g in f:
            if d in g.unicodes:
                return g
    
    @classmethod
    def glyph2Char(cls, glyph):
        f = glyph.getParent()
        u = f.naked().unicodeData.pseudoUnicodeForGlyphName(glyph.name)
        if isinstance(u, int):
            return unichr(u)
        else:
            return None

    @classmethod
    def getDecomposition(cls, char):
        u"""
        <doc>
        Decomposition.
        </doc>
        """
        charDec = ord(char)
        decompString = unicodedata.decomposition(char)
        if decompString:
            decompHex = decompString.split(' ')
            decomp = [TX.hex2dec(i) for i in decompHex]
            overrides = {
                290: {807: 806}, # u'Ģ': {u'̦': u'̧'}
                291: {807: 806}, # u'ģ': {u'̦': u'̧'}
                325: {807: 806}, # u'Ņ': {u'̦': u'̧'}
                311: {807: 806}, # u'ķ': {u'̦': u'̧'}
                310: {807: 806}, # u'Ķ': {u'̦': u'̧'}
                342: {807: 806}, # u'Ŗ': {u'̦': u'̧'}
                343: {807: 806}, # u'ŗ': {u'̦': u'̧'}
                536: {807: 806}, # u'Ș': {u'̦': u'̧'}
                537: {807: 806}, # u'ș': {u'̦': u'̧'}
                538: {807: 806}, # u'Ț': {u'̦': u'̧'}
                539: {807: 806}, # u'ț': {u'̦': u'̧'}
                316: {807: 806}, # u'ļ': {u'̦': u'̧'}
                315: {807: 806}, # u'Ļ': {u'̦': u'̧'}
                291: {807: 786}, # gcommaccent
                319: {183: 775},
                320: {183: 775}
                }
            for x, u in enumerate(decomp):
                if overrides.has_key(charDec) and overrides[charDec].has_key(u):
                    decomp[x] = overrides[charDec][u]
            charList = []
            for d in decomp:
                if isinstance(d, int):
                    charList.append(unichr(d))
            return charList
        return None
        
class AnchorPlacer(BaseWindowController):

    DEFAULTKEY = "com.fontbureau.diacriticView"
    DEFAULTKEY_FILLCOLOR = "%s.fillColor" %DEFAULTKEY
    DEFAULTKEY_STROKECOLOR = "%s.strokeColor" %DEFAULTKEY
    DEFAULTKEY_STROKE = "%s.stroke" %DEFAULTKEY
    DEFAULTKEY_FILL = "%s.fill" %DEFAULTKEY
    FALLBACK_FILLCOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .5, .5, .3)
    FALLBACK_STROKECOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .5, .5, .5)
    VERSION = 1.0
    NAME = u'Accentista'
    MANUAL = u"""TK"""

    bottomAccentFind = ['below', 'cedilla', 'commaaccent', 'ogonek']
    BASEUNICODES = list(range(0, 383)) + list(range(880, 1279)) + [536, 537, 538, 539]
    BASECHARSET = [unichr(u) for u in BASEUNICODES if unicodedata.category(unichr(u)) in ["Lu", "Ll"]]
    
    def updateView(self, sender=None):
        UpdateCurrentGlyphView()
    
    def getCharsThatIncludeChar(self, char):
        accentChars = []
        for base in self.BASECHARSET:
            decomp = CharacterTX.getDecomposition(base)
            if decomp and char in decomp:
                accentChars.append(base)
        return accentChars
    
    def getDefaultAnchorName(self, char):
        anchorName = 'top'
        accentUnicodeName = unicodedata.name(char)
        for searchString in self.bottomAccentFind:
            if accentUnicodeName.find(searchString.upper()) != -1:
                anchorName = 'bottom'
        return anchorName
     
    def currentGlyphChanged(self, info={}):
        self.current = CurrentGlyph()
        self.setShowAccents(self.current)
    
    def getAccentGlyphFromChar(self, d, char, f):
        name = unicodedata.name(char)
        if 'ABOVE' in name and d == 'i':
            d = u'ı'
        g = CharacterTX.char2Glyph(d, f)
        if g is None and COMBINING2FLOATING.has_key(ord(d)):
            g = CharacterTX.char2Glyph(unichr(COMBINING2FLOATING[ord(d)]), f)
        if g is not None:
            if CurrentGlyph() and '.sc' in CurrentGlyph().name:
                if f.has_key(g.name+'.sc'):
                    g = f[g.name+'.sc']
            elif unicodedata.category(char) == 'Lu' and f.has_key(g.name+'.uc'):
                g = f[g.name+'.uc']
        if ord(char) in [317, 271, 318, 357] and ord(d) in [780, 711]:
            if f.has_key('caroncmb.salt'):
                g = f['caroncmb.salt']
            elif f.has_key('caron.salt'):
                g = f['caron.salt']
        return g
    
    def getAnchorName(self, accentGlyph, d, g):
        accentName = accentGlyph.name
        if TX.hasAnchor('top_'+accentName, g):
            anchorName = 'top_'+accentName
        elif TX.hasAnchor('bottom_'+accentName, g):
            anchorName = 'bottom_'+accentName
        else:
            anchorName = self.getDefaultAnchorName(d)
        return anchorName
        
    def setShowAccents(self, g):
        source = g
        accentView = []
        accents = {}
        if g is not None:
            f = g.getParent()
            char = CharacterTX.glyph2Char(g)
            chars = self.getCharsThatIncludeChar(char)
            for baseChar in chars:
                accentViewItem = {}
                decomp = CharacterTX.getDecomposition(baseChar)
                decomp.remove(char)
                for d in decomp:
                    accentGlyph = self.getAccentGlyphFromChar(d, baseChar, f)
                    if accentGlyph is not None:
                        if unicodedata.category(d) not in ["Lu", "Ll"]:
                            accentName = accentGlyph.name
                            anchorName = self.getAnchorName(accentGlyph, d, g)
                            accents[accentName] = (accentGlyph, anchorName)
                            accentViewItem['Accent'] = accentName
                            accentViewItem['Anchor'] = anchorName
                if accentViewItem:
                    accentView.append(accentViewItem)
            
            if not accents:
                decomp = CharacterTX.getDecomposition(char) or []
                for i, d in enumerate(decomp):
                    if unicodedata.category(d) in ["Lu", "Ll"]:
                        baseGlyph = self.getAccentGlyphFromChar(d, char, f)
                        if baseGlyph is not None:
                            anchorName = '__Origin__'
                            accentView.append({'Accent': baseGlyph.name, 'Anchor': anchorName})
                            source = baseGlyph
                            accents[baseGlyph.name] = (baseGlyph, anchorName)
                        decomp.pop(i)
                        break
                for d in decomp:
                    accentViewItem = {}
                    accentGlyph = self.getAccentGlyphFromChar(d, char, f)
                    if accentGlyph is not None:
                        accentName = accentGlyph.name
                        anchorName = anchorName = self.getAnchorName(accentGlyph, d, source)
                        accents[accentName] = (accentGlyph, anchorName)
                        accentViewItem['Accent'] = accentName
                        accentViewItem['Anchor'] = anchorName
                    if accentViewItem:
                        accentView.append(accentViewItem)
            
            self.getView().glyphName.set(g.name)
            self.getView().diacriticList.set(accentView)
        self.showAccents = accents
        self.showAccentSource = source
    
    
    def getShowAccentSource(self):
        return self.showAccentSource
        
    def getShowAccents(self):
        return self.showAccents or {}

    def activateModule(self):
        addObserver(self, "drawAccents", "drawBackground")
        addObserver(self, "currentGlyphChanged", "currentGlyphChanged")

    def deactivateModule(self):
        removeObserver(self, "drawBackground")
        removeObserver(self, "currentGlyphChanged")

    def __init__(self, doWindow=True):
        self.current = CurrentGlyph()
        self.showAccents = {}
        self.w = FloatingWindow((425, 200), self.NAME, minSize=(350, 200))
        self.populateView()
        self.activateModule()
        self.getView().open()
    
    def getView(self):
        return self.w

    
    def populateView(self):
        
        self.fillColor = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)
        self.strokeColor = getExtensionDefaultColor(self.DEFAULTKEY_STROKECOLOR, self.FALLBACK_STROKECOLOR)

        doWindow = True
        if doWindow:
            view = self.getView()
            x = 10
            y = 10
            y += 30
            view.diacriticList = List((x, y, -10, -10), [],
                    columnDescriptions=[
                                    {"title": "Accent", "editable": False, 'enableDelete': True, 'typingSensitive': True}, 
                                    {"title": "Anchor", "editable": True, 'enableDelete': True, 'typingSensitive': True}, 
                                    ], 
                        doubleClickCallback=self.doubleClickCallback, 
                        #editCallback=self.modifyCallback,
                        selectionCallback=self.selectionCallback                  
                        )

            y-=30            
            view.glyphName = TextBox((x, y, 200, 25), '')

            x = -240
            view.guides = CheckBox((x, y, 60, 22), "Guides", sizeStyle="small", 
                #value=getExtensionDefault("%s.%s" %(self.DEFAULTKEY, "stroke"), False),
                value = True, 
                callback=self.updateView)
            x += 60            
            view.fill = CheckBox((x, y, 40, 22), "Fill", sizeStyle="small", 
                #value=getExtensionDefault("%s.%s" %(self.DEFAULTKEY, "fill"), True),
                value = True,
                callback=self.fillCallback)
            x += 40
            view.stroke = CheckBox((x, y, 60, 22), "Stroke", sizeStyle="small", 
                #value=getExtensionDefault("%s.%s" %(self.DEFAULTKEY, "stroke"), False),
                value = True, 
                callback=self.strokeCallback)
            x += 60
            color = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)
            view.color = ColorWell((x, y, 30, 22), 
                color=color,
                callback=self.colorCallback)
            x += 40
            view.reset = Button((x, y, 30, 22), unichr(8634), callback=self.clearSelectionCallback)



          
            self.setUpBaseWindowBehavior()
        
        self.setShowAccents(self.current)

        UpdateCurrentGlyphView()

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

    def fillCallback(self, sender):
        """
        Change the fill status.
        """
        setExtensionDefault(self.DEFAULTKEY_FILL, sender.get())
        self.updateView()

    def strokeCallback(self, sender):
        """
        Change the stroke status.
        """
        setExtensionDefault(self.DEFAULTKEY_STROKE, sender.get())
        self.updateView()

    def selectionCallback(self, sender):
        self.updateView()
    
    def modifyCallback(self, sender):
        accents = self.getShowAccents()
        for accentName, accentBunch in accents.items():
            accentGlyph, anchorName = accentBunch
            for item in sender.get():
                if item.get('Accent') == accentName and item.get('Anchor') != anchorName:
                    newBunch = accentGlyph, item.get('Anchor')
                    self.getShowAccents()[accentName] = newBunch
    
    def doubleClickCallback(self, sender):
        for i in sender.getSelection():
            item = sender.get()[i]
            self.current.appendAnchor(item['Anchor']+'_'+item['Accent'], (0, 0))
            self.setShowAccents(self.current)
    
    def clearSelectionCallback(self, sender={}):
        self.getView().diacriticList.setSelection([])
    
    def drawAccents(self, info):
        #fill = getExtensionDefault(self.DEFAULTKEY_FILL, True)
        #stroke = getExtensionDefault(self.DEFAULTKEY_STROKE, True)
        #fillcolor = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)

        self.fillColor.setFill()
        self.strokeColor.setStroke()

        g = self.getShowAccentSource()
        accents = self.getShowAccents()

        diacriticList = self.getView().diacriticList.get()
        currentSelectionIndexes = self.w.diacriticList.getSelection()
        selectedAccentNames = [diacriticList[i]['Accent'] for i in currentSelectionIndexes]
        for accentName, accentBunch in accents.items():
            accentGlyph, anchorName = accentBunch
            compatibleAnchorName = '_' + anchorName.split('_')[0]
            anchorMatch = False
            accentOffset = 0, 0
            offset = 0, 0
            if not selectedAccentNames or accentName in selectedAccentNames:
                for anchor in g.anchors:
                    if anchor.name == anchorName:
                        baseOffset = anchor.x, anchor.y
                        for accentAnchor in accentGlyph.anchors:
                            
                            if accentAnchor.name == compatibleAnchorName:
                                accentOffset = accentAnchor.x, accentAnchor.y
                        offset = baseOffset[0] - accentOffset[0], baseOffset[1] - accentOffset[1]
                        d = MojoGlyphDisplay(self.current, accentGlyph, offset=offset)
                        d.drawGlyph(fill=self.getView().fill.get(),
                        stroke=self.getView().stroke.get()
                        )
                        anchorMatch = True
            #if not anchorMatch:
            if anchorName == '__Origin__':
                d = MojoGlyphDisplay(self.current, accentGlyph, offset=offset)
                d.drawGlyph(fill=self.getView().fill.get(),
                        stroke=self.getView().stroke.get()
                        )
        if g.box and self.getView().guides.get():
            boxWidth = g.box[2] - g.box[0]
            leftX = g.angledLeftMargin + g.getParent().lib.get('com.typemytype.robofont.italicSlantOffset') or 0
            rightX = g.width - g.angledRightMargin + g.getParent().lib.get('com.typemytype.robofont.italicSlantOffset') or 0
            midX = leftX + (g.width - g.angledLeftMargin - g.angledRightMargin) / 2.0
            dashLine(2)
            stroke(0, 0, 0, .3)
            
            topY = self.current.getParent().info.ascender * 2
            bottomY = self.current.getParent().info.descender * 2
            italicAngle = self.current.getParent().info.italicAngle or 0
            topX = TX.getItalicOffset(topY, italicAngle)
            bottomX = TX.getItalicOffset(bottomY, italicAngle)
            line(leftX+topX, topY, leftX+bottomX, bottomY)
            line(midX+topX, topY, midX+bottomX, bottomY)
            line(rightX+topX, topY, rightX+bottomX, bottomY)
            
    def windowCloseCallback(self, sender):
        self.deactivateModule()
        UpdateCurrentGlyphView()
        BaseWindowController.windowCloseCallback(self, sender)

a = AnchorPlacer()
