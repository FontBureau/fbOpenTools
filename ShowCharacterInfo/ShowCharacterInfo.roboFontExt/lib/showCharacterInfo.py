"""
SHOW CHARACTER INFO

"""

import os
import json
import unicodedata
from defconAppKit.windows.baseWindow import BaseWindowController
from vanilla import TextBox
try:
    from lib.tools.agl import AGL2UV
except ImportError:
    from fontTools.agl import AGL2UV
from lib.tools.defaults import getDefaultColor
from mojo.events import addObserver, removeObserver
from mojo.roboFont import version
if version >= "4.4b":  # Support for dark mode color retrieval
    from mojo.UI import appearanceColorKey


nameMap = {
    'ALT': 'Alternate',
    'SALT': 'Stylistic Alternate',
    'CALT': 'Contextual Alternate',
    'SC': 'Small Cap',
    'SMCP': 'Small Cap',
    'SUPS': 'Superior',
    'SINF': 'Inferior',
    'NUMR': 'Numerator',
    'DNOM': 'Denominator',
}

BIGUNI = None

class TX:
    @classmethod
    def hex2dec(cls, s):
        try:
            return int(s, 16)
        except Exception:
            pass

    @classmethod
    def dec2hex(cls, n, uni = 1):
        hex = "%X" % n
        if uni == 1:
            while len(hex) <= 3:
                hex = '0' + str(hex)
        return hex

    @classmethod
    def splitFourDigitUnicodeSequence(cls, l):
        u"""
        <doc><code>splitFourDigitUnicodeSequence</code> helps process unicode values.</doc>
        """
        return [l[i:i + 4] for i in range(0, len(l), 4)]

    @classmethod
    def getUnicodeSequence(cls, name, VERBOSE=False):
        """
        <doc><code>getUnicodeSequence</code> gets a unicode sequence from a unicode name, following the rules.
        <blockquote>If the component is of the form "uni" (U+0075 U+006E U+0069) followed by a sequence of uppercase
        hexadecimal digits (0 .. 9, A .. F, i.e. U+0030 .. U+0039, U+0041 .. U+0046), the length of that sequence is a
        multiple of four, and each group of four digits represents a number in the set {0x0000 .. 0xD7FF, 0xE000 ..
        0xFFFF}, then interpret each such number as a Unicode scalar value and map the component to the string made of
        those scalar values. Note that the range and digit length restrictions mean that the "uni" prefix can be used
        only with Unicode values from the Basic Multilingual Plane (BMP).</blockquote>

        <blockquote>Otherwise, if the component is of the form "u" (U+0075) followed by a sequence of four to six
        uppercase hexadecimal digits {0 .. 9, A .. F} (U+0030 .. U+0039, U+0041 .. U+0046), and those digits represent a
        number in {0x0000 .. 0xD7FF, 0xE000 .. 0x10FFFF}, then interpret this number as a Unicode scalar value and map
        the component to the string made of this scalar value.</blockquote></doc>
        """
        unicodeList = None
        if VERBOSE:
            print('isUnicodeName, %s' % name)
        if len(name) > 3 and name[:3] == 'uni':
            unicodeSequence = name[3:]
            if len(unicodeSequence) / 4 == int(len(unicodeSequence) / 4):
                unicodeList = cls.splitFourDigitUnicodeSequence(unicodeSequence)
                for unicodeHex in unicodeList:
                    if not cls.isHexDigit(unicodeHex):
                        return None
        elif len(name) > 1 and name[0] == 'u':
            unicodeSequence = name[1:]
            if len(unicodeSequence) >= 4 and len(unicodeSequence) <= 6 and cls.isHexDigit(unicodeSequence):
                if unicodeSequence:
                    unicodeList = [unicodeSequence]
                else:
                    unicodeList = unicodeSequence
        decUnicodeList = []
        if unicodeList:
            for u in unicodeList:
                try:
                    decUnicodeList.append(TX.hex2dec(u))
                except Exception:
                    decUnicodeList.append(u)
            return decUnicodeList
        else:
            return unicodeList

    @classmethod
    def isHexDigit(cls, name):
        u"""
        <doc><code>isHexDigit</code> returns True if the given name matches a hexadecimal unicode value.</doc>
        """
        for n in name:
            if n not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']:
                return False
        return True


def getCharName(char, dec=None, BIGUNI=BIGUNI):
    if dec is None:
        dec = ord(char)
    try:
        return unicodedata.name(char)
    except Exception:
        if not BIGUNI:
            bigUniFile = open(os.path.join(os.path.split(__file__)[0], 'bigUni.json'))
            BIGUNI = json.loads(bigUniFile.read())
        return BIGUNI.get(str(dec))

def getChar(dec):
    try:
        return chr(dec)
    except Exception:
        try:
            hexVersion = TX.dec2hex(dec)
            return (r'\U' + hexVersion.zfill(8)).decode('unicode-escape')
        except Exception:
            return ''

def getGlyphInfo(g):
    # break down the name into baseName elements and suffix Elements
    if g is None:
        return ''
    gname = g.name
    nameElements = gname.split('.')
    baseName = nameElements[0]
    suffix = ''
    if len(nameElements) > 1:
        suffix = u'.'.join(nameElements[1:])
    baseNameElements = baseName.split('_')
    suffixElements = suffix.split('_')
    if suffixElements == ['']:
        suffixElements = []
    f = g.font
    unicodeNameElements = []
    unicodeValueElements = []
    charString = u''
    isLig = False
    # if the glyph has unicodes, use those
    if not unicodeValueElements:
        for i, uv in enumerate(g.unicodes):
            char = getChar(uv)
            if i == 0:
                charString = char
            unicodeValueElements.append('U+'+TX.dec2hex(uv))
            charName = getCharName(char, uv)
            if charName:
                unicodeNameElements.append(charName)
    # the glyph name is a uniXXXX or a uXXXXX name, use those!
    if not unicodeValueElements:
        for i, uv in enumerate(TX.getUnicodeSequence(baseName) or []):
            char = getChar(uv)
            charString += char
            unicodeValueElements.append(u'! · ~U+'+TX.dec2hex(uv))
            if i > 0:
                isLig = True
            charName = getCharName(char, uv)
            if charName:
                unicodeNameElements.append(charName)
    # the base name is in the adobe glyph list
    if not unicodeValueElements:
        for i, baseNameElement in enumerate(baseNameElements):
            uv = AGL2UV.get(baseNameElement)
            if i > 0:
                isLig = True
            if uv:
                char = getChar(uv)
                charString += char
                unicodeValueElements.append('~U+'+TX.dec2hex(uv))
                charName = getCharName(char, uv)
                if charName:
                    unicodeNameElements.append(charName)
    # interpret this stuff into something to display
    suffixNameWords = []
    for suffixElement in suffixElements:
        suffixLabel = nameMap.get(suffixElement.upper()) or "'"+suffixElement+"'"
        if suffixLabel:
            suffixNameWords.append(suffixLabel)
    featureInfo = u' '.join(suffixNameWords)
    unicodeNameDisplay = ''

    # do special treatments for ligatures
    if isLig and charString:
        unicodeNameDisplay += 'LIGATURE ' + charString
    else:
        if unicodeNameElements:
            unicodeNameDisplay += unicodeNameElements[0]
    if isLig:
        uniValueSeparator = u'+'
    else:
        uniValueSeparator = u' '

    displayElements = []
    if unicodeValueElements:
        displayElements.append(uniValueSeparator.join(unicodeValueElements))
    if unicodeNameDisplay:
        displayElements.append(unicodeNameDisplay)
    if featureInfo:
        displayElements.append(featureInfo)
    if charString:
        displayElements.append(charString)
    #if not displayElements:
    #    displayElements.append('UNRECOGNIZED')
    charDisplay = u' · '.join(displayElements)
    return charDisplay


class ShowCharacterInfoBox(TextBox):
    """
    The subclassed vanilla text box.
    """
    def __init__(self, *args, **kwargs):
        self.window = kwargs['window']
        self.glyph  = self.window.getGlyph()
        self.font   = RFont(self.glyph.font)
        if version >= "4.4b":  # Support for dark mode color retrieval
            self.color = getDefaultColor(appearanceColorKey("glyphViewMetricsTitlesColor"))
        else:
            self.color = getDefaultColor("glyphViewMetricsTitlesColor")
        del kwargs['window']
        super(ShowCharacterInfoBox, self).__init__(*args, **kwargs)
        nsText = self.getNSTextField()
        nsText.setTextColor_(self.color)
        self.showInfo(self.glyph)
        addObserver(self, "currentGlyphChanged", "currentGlyphChanged")
        
    def currentGlyphChanged(self, info):
        self.glyph = info['glyph']
        self.showInfo(self.glyph)

    def showInfo(self, glyph):
        if self.glyph == None:
             return
        # Only change the glyph info in the glyph editor if the info belongs to that glyph
        if self.glyph.font == self.font:
            try:
                self.set(getGlyphInfo(self.glyph))
            except Exception:
                pass

    def _breakCycles(self):
        super(ShowCharacterInfoBox, self)._breakCycles()
        removeObserver(self, "currentGlyphChanged")

class ShowCharacterInfo(BaseWindowController):
    """
    Attach a vanilla text box to a window.
    """
    def __init__(self):
        addObserver(self, "glyphWindowDidOpen", "glyphWindowDidOpen")
        self.window = None

    def glyphWindowDidOpen(self, info):
        self.window = info["window"]
        glyph  = info["glyph"]
        vanillaView = ShowCharacterInfoBox((20, -30, -20, 22), getGlyphInfo(glyph), window=self.window, alignment="right", sizeStyle="mini")
        superview = self.window.editGlyphView.enclosingScrollView().superview()
        view = vanillaView.getNSTextField()
        frame = superview.frame()
        vanillaView._setFrame(frame)
        superview.addSubview_(view)

    def windowCloseCallback(self, sender):
        super(ShowCharacterInfoBox, self).windowCloseCallback(sender)
        removeObserver(self, "glyphWindowDidOpen")


if __name__ == '__main__':
    ShowCharacterInfo()
