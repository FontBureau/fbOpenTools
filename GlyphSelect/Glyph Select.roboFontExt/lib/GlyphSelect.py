# -*- coding: UTF-8 -*-  
#
# ----------------------------------------------------------------------------------
from vanilla import *
from AppKit import *
from defconAppKit.windows.baseWindow import BaseWindowController
from fnmatch import fnmatch
import string

#############
# RESOURCES #
#############

def splitName(name):
    """Splits a glyph name into a (baseName string, suffix string) tuple."""
    baseName, suffix = '', ''
    nameElements = name.split('.')
    if len(nameElements) > 0:
        baseName = nameElements[0]
        if len(nameElements) > 1:
            suffix = '.'.join(nameElements[1:])
        else:
            suffix = ''
    return baseName, suffix

UNICODE_CATEGORY_ORDER = ['Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Mn', 'Mc', 'Me', 'Nd', 'Nl', 'No', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'Zs', 'Zl', 'Zp', 'Cc', 'Cf', 'Cs', 'Co', 'Cn']
UNICODE_CATEGORIES = {
    'Lu': 'Letter, Uppercase',                #an uppercase letter
    'Ll': 'Letter, Lowercase',                #a lowercase letter
    'Lt': 'Letter, Titlecase',                #a digraphic character, with first part uppercase
    'Lm': 'Letter, Modifier',                #a modifier letter
    'Lo': 'Letter, Other',                    #other letters, including syllables and ideographs
    'Mn': 'Mark, Nonspacing',                #a nonspacing combining mark (zero advance width)
    'Mc': 'Mark, Spacing',                    #a spacing combining mark (positive advance width)
    'Me': 'Mark, Enclosing',                #an enclosing combining mark
    'Nd': 'Number, Decimal Digit',            #a decimal digit
    'Nl': 'Number, Letter',                    #a letterlike numeric character
    'No': 'Other Number',                    #a numeric character of other type
    'Pc': 'Punctuation, Connector',            #a connecting punctuation mark, like a tie
    'Pd': 'Punctuation, Dash',                #a dash or hyphen punctuation mark
    'Ps': 'Punctuation, Open',                #an opening punctuation mark (of a pair)
    'Pe': 'Punctuation, Close',                #a closing punctuation mark (of a pair)
    'Pi': 'Punctuation, Initial',            #an initial quotation mark
    'Pf': 'Punctuation, Final',                #a final quotation mark
    'Po': 'Punctuation, Other',                #a punctuation mark of other type
    'Sm': 'Symbol, Math',                    #a symbol of primarily mathematical use
    'Sc': 'Symbol, Currency',                #a currency sign
    'Sk': 'Symbol, Modifier',                #a non-letterlike modifier symbol
    'So': 'Symbol, Other',                    #a symbol of other type
    'Zs': 'Separator, Space',                #a space character (of various non-zero widths)
    'Zl': 'Separator, Line',                #U+2028 LINE SEPARATOR only
    'Zp': 'Separator, Paragraph',            #U+2029 PARAGRAPH SEPARATOR only
    'Cc': 'Other, Control',                    #a C0 or C1 control code
    'Cf': 'Other, Format',                    #a format control character
    'Cs': 'Other, Surrogate',                #a surrogate code point
    'Co': 'Other, Private Use',                #a private-use character
    'Cn': 'Other, Unassigned',                #a reserved unassigned code point or a noncharacter
}
UNICODE_CATEGORY_ORDER_COMBINED = ['Letter', 'Mark', 'Number', 'Punctuation', 'Symbol', 'Separator', 'Other']
UNICODE_CATEGORIES_COMBINED = {
    'Letter': ['Lu', 'Ll', 'Lt', 'Lm', 'Lo'],
    'Mark': ['Mn', 'Mc', 'Me'],
    'Number': ['Nd', 'Nl', 'No'],
    'Punctuation': ['Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po'],
    'Symbol': ['Sm', 'Sc', 'Sk', 'So'],
    'Separator': ['Zs', 'Zl', 'Zp'],
    'Other': ['Cc', 'Cf', 'Cs', 'Co', 'Cn'],
}
def dec2hex(n, uni = 1):
    hex = "%X" % n
    if uni == 1:
    	while len(hex) <= 3:
    		hex = '0' + str(hex)
    return hex
def readUnicode(unicodeInteger):
    if isinstance(unicodeInteger, int):
        return dec2hex(unicodeInteger)
    else:
        return str(unicodeInteger)
def hex2dec(s):
    try:
        return int(s, 16)
    except:
        pass
def writeUnicode(unicodeString):
    if type(unicodeString) is str:
        return hex2dec(unicodeString)
    else:
        return int(unicodeString)
def reverseDict(d):
	"""
	Reverse a dictionary. This only works right when the dictionary has unique keys and unique values.
	"""
	newDict = {}
	keys = d.keys()
	keys.sort()
	for k in keys:
		v = d[k]
		if v not in newDict.keys():
			newDict[v] = k
	return newDict


# ----------------------------------------------------------------------------------
# Glyph Search

class SelectGlyphSearch(BaseWindowController):
    """
    Search for glyphs using a variety of parameters:
    
    - Glyph Name:
        Exact match for glyph name.
    
    - Base Name:
        Exact match for the basename of the glyph (anything before the first period in a glyph name)
    
    - Suffix
        Exact match for the suffix of the glyph name (anything after the first period).

    - Unicode value
        Find exact match for hexadecimal unicode value.
    
    - Unicode category
        The unicode category groups and individual categories are listed in a dropdown. 
        You might have to hit enter/return in the dropdown to select an item.
        These categories are inclusive, so they will match base glyphs and alternates ("number" will match 'zero' and also 'zero.sups'). 

    You can use the following wildcards:
        *	matches everything
        ?	matches any single character
        [seq]	matches any character in seq
        [!seq]	matches any character not in seq

    Then you can manually select glyphs (by default, all search results are selected)

    You can perform the following selection manipulations in the current font or in all open fonts:

    - Replace selection with results
    - Add results to selection
    - Subtract results from selection
    - Intersect results and seletion (select glyphs common to both) 
    - Print the glyph list to the output window.

    """
    
    def __init__(self):
        """
        Initialize the dialog.
        """        
        title = "Glyph Select from Current Font"    
        self.w = Window((400, 500), title, minSize=(400, 500))
        # get the current font and selection
        f = self.getFont()
        if not f:
            print "Open a font."
            return
        self.setExistingSelection(f.selection[:])
        # make tabs
        tabList = ['Name', 'Basename', 'Suffix', 'Unicode', 'Category']
        self.w.tabs = Tabs((10, 10, -10, -10), tabList, sizeStyle="small")
        for i, tabName in enumerate(tabList):
            # search box
            if i == 0 or i == 1 or i == 2 or i == 3:
                self.w.tabs[i].searchBox = SearchBox((10, 10, -50, 22), callback=self.searchBoxCallback, placeholder=tabName)
            else:
                self.w.tabs[i].searchBox = ComboBox((10, 10, -50, 22), self.getUnicodeCategoriesList(), callback=self.searchBoxCallback)
            # refresh button
            self.w.tabs[i].refresh = Button((-40, 10, 30, 22), unichr(8634), callback=self.refreshCallback)
            # glyph list
            self.w.tabs[i].glyphList = List((10, 40, -10, -115), [])
            #self.w.tabs[i].spinner = ProgressSpinner((-33, 5, 32, 32), displayWhenStopped=False, sizeStyle="small")
        # buttons
        y = -120
        self.w.sourceName = TextBox((20, y, -10, 22), 'Source:', sizeStyle="small")
        y += 22
        self.w.replaceSelection = Button((20, y, 170, 22), 'Replace Selection', sizeStyle="small", callback=self.replaceSelection)       
        self.w.addToSelection = Button((210, y, 170, 22), 'Add To Selection', sizeStyle="small", callback=self.addToSelection)
        y += 27
        self.w.intersectWithSelection = Button((20, y, 170, 22), 'Intersect with Selection', sizeStyle="small", callback=self.intersectWithSelection)
        self.w.subtractFromSelection = Button((210, y, 170, 22), 'Subtract from Selection', sizeStyle="small", callback=self.subtractFromSelection)
        y += 30
        self.w.applySelectionText = TextBox((20, y, 120, 22), 'Apply selection:', sizeStyle="small")
        self.w.applySelectionRadio = RadioGroup((120, y-3, 210, 22),
                                        ["Current Font", "All Open Fonts"],
                                        isVertical=False, sizeStyle="small")
        self.w.applySelectionRadio.set(0)
        #10169
        self.w.printButton = Button((-50, y-3, 30, 22), unichr(9998), callback=self.printCallback, sizeStyle="small")
        self.setUpBaseWindowBehavior()
        self.w.open()

    def windowCloseCallback(self, sender):
        BaseWindowController.windowCloseCallback(self, sender)
    
    ###################
    ## GETS AND SETS ##
    ###################
        
    def getFont(self):
        """
        Returns the current font.
        The other option was to do this with an observer, but that just seemed...complicated.
        """
        f = CurrentFont()
        return f

    def setFontSource(self, f):
        if f is not None:
            self.w.sourceName.set('Source: ' + self.getFontName(f))
        else:
            self.w.sourceName.set('Source:')
    
    def getFontName(self, f=None):
        if f is None:
            f = self.getFont()
        return ' '.join([f.info.familyName, f.info.styleName])
    
    def getAllFonts(self):
        return AllFonts()
    
    def getGlyphOrder(self):
        return self.getFont().glyphOrder
    
    def getUnicodeData(self):
        return self.getFont().naked().unicodeData
    
    def getFontAndGlyphOrderAndUnicodeData(self):
        """
        Convenience function.
        """
        f = self.getFont()
        glyphOrder = f.glyphOrder
        unicodeData = f.naked().unicodeData
        return f, glyphOrder, unicodeData

    def getExistingSelection(self):
        return self.selection
        
    def setExistingSelection(self, selection):
        self.selection = selection
        
    def getNewSelection(self):
        """
        Return the current selection within glyphList.
        """
        i = self.w.tabs.get()
        tabAll = self.w.tabs[i].glyphList.get()
        tabSelectedIndexes = self.w.tabs[i].glyphList.getSelection()
        newSelection = []
        for selectedIndex in tabSelectedIndexes:
            newSelection.append(tabAll[selectedIndex])
        return newSelection

    ###############
    ## CALLBACKS ##
    ###############
    
    def searchBoxCallback(self, sender):
        """
        """
        searchTerm = sender.get()
        self.doSearch(searchTerm)

    def refreshCallback(self, sender):
        """
        Refresh the search with the current font.
        """
        i = self.w.tabs.get()
        self.doSearch(self.w.tabs[i].searchBox.get())
    
    def printCallback(self, sender):
        print self.getNewSelection()
    
    ###############
    ## DO SEARCH ##
    ###############
    
    def doSearchInGlyphName(self, searchTerm, searchIn):
        searchResults = []
        for gname in searchIn:
            if fnmatch(gname, searchTerm):
                searchResults.append(gname)
        return searchResults
        
    def doSearchInBaseName(self, searchTerm, searchIn):
        searchResults = []
        for gname in searchIn:
            baseName, suffix = splitName(gname)
            if fnmatch(baseName, searchTerm):
                searchResults.append(gname)
        return searchResults

    def doSearchInSuffix(self, searchTerm, searchIn):
        searchResults = []
        for gname in searchIn:
            baseName, suffix = splitName(gname)
            if fnmatch(suffix, searchTerm):
                searchResults.append(gname)
        return searchResults

    def getUnicodeCategoriesList(self):
        categoryList = []
        for metaCategoryName in UNICODE_CATEGORY_ORDER_COMBINED:
            categoryList.append(metaCategoryName)
        categoryList.append('')
        for catshort in UNICODE_CATEGORY_ORDER:
            categoryList.append(UNICODE_CATEGORIES[catshort])
        return categoryList

    def doSearchInUnicode(self, searchTerm, searchIn, unicodeData=None):
        searchResults = []

        if unicodeData is None:
            unicodeData = self.getUnicodeData()

        for gname in searchIn:
            dec = unicodeData.unicodeForGlyphName(gname)
            hex = readUnicode(dec)
            if fnmatch(hex, searchTerm) and not gname in searchResults:
                searchResults.append(gname)
        searchResults.sort()
        return searchResults

        """
        # at some point in the future, implement unicode ranges...
        searchRanges = searchTerm.split(',')
        for x, searchRange in enumerate(searchRanges):
            searchRange = string.strip(searchRange)
            searchRanges[x] = searchRange.split('-')
        
        # [[min, max], [min, max]]
        
        for gname in searchIn:
            dec = unicodeData.unicodeForGlyphName(gname)
            if dec:
                hex = dec2hex(dec)
                for searchRange in searchRanges:
                    if len(searchRange) == 1:
                        if fnmatch(hex, searchTerm) and not gname in searchResults:
                            searchResults.append(gname)
                    elif len(searchRange) == 2 and len(searchRange[0]) == 4 and len(searchRange[1]) == 4:
                        min, max = searchRange
                        mindec, maxdec = hex2dec(min), hex2dec(max)
                        if mindec and maxdec:
                            print min, max, mindec, maxdec, dec, min < dec, max
                            if mindec < dec < maxdec:
                                searchResults.append(gname)
        """
        
        searchResults.sort()
        return searchResults

        
        
    def doSearchInUnicodeCategory(self, searchTerm, searchIn, unicodeData=None):
        searchResults = []
        if unicodeData is None:
            unicodeData = self.getUnicodeData()
        reverseUnicodeCategories = reverseDict(UNICODE_CATEGORIES)
        try:
            searchTerms = [reverseUnicodeCategories[searchTerm]]
        except:
            searchTerms = UNICODE_CATEGORIES_COMBINED[searchTerm]
        for gname in searchIn:
            if unicodeData.categoryForGlyphName(gname) in searchTerms:
                searchResults.append(gname)
        return searchResults

    def doSearch(self, searchTerm):
        f, glyphOrder, unicodeData = self.getFontAndGlyphOrderAndUnicodeData()
        self.setFontSource(f)        
        i = self.w.tabs.get()
        if not searchTerm:
            self.setFontSource(None)
        searchResults = []
        #start the spinner
        #self.w.tabs[i].spinner.start()
        if i == 0:   # glyph name
            searchResults = self.doSearchInGlyphName(searchTerm, glyphOrder)
        elif i == 1:  # base name
            searchResults = self.doSearchInBaseName(searchTerm, glyphOrder)
        elif i == 2:    # suffix
            searchResults = self.doSearchInSuffix(searchTerm, glyphOrder)
        elif i == 3:    # unicode value
            searchResults = self.doSearchInUnicode(searchTerm, glyphOrder, unicodeData)
        elif i == 4:    # unicode category
            searchResults = self.doSearchInUnicodeCategory(searchTerm, glyphOrder, unicodeData)
        else:
            print 'tab error', i
        # set the search results
        self.w.tabs[i].glyphList.set(searchResults)
        # select all by default
        self.w.tabs[i].glyphList.setSelection(range(0, len(searchResults)))
        # stop the spinner
        #self.w.tabs[i].spinner.stop()

    ############################
    ##  MANIPULATE SELECTION  ##
    ############################
    

    
    def selectInFont(self):
        # figure out whether we are selecting in current font, or all fonts
        applySelectionIndex = self.w.applySelectionRadio.get()
        if applySelectionIndex == 1:
            fonts = self.getAllFonts()
        elif applySelectionIndex == 0:
            fonts = [self.getFont()]
        # apply selection
        for f in fonts:
            fontSet = set(f.keys())
            selectionSet = set(self.getExistingSelection())
            resultSet = fontSet.intersection(selectionSet)
            f.selection = list(resultSet)
            f.update()
    
    def addToSelection(self, sender):
        existingSet = set(self.getExistingSelection())
        newSet = set(self.getNewSelection())
        bothSet = existingSet | newSet
        self.setExistingSelection(list(bothSet))
        self.selectInFont()
 
    def intersectWithSelection(self, sender):
        existingSet = set(self.getExistingSelection())
        newSet = set(self.getNewSelection())
        bothSet = existingSet & newSet
        self.setExistingSelection(list(bothSet))
        self.selectInFont()
 
    def subtractFromSelection(self, sender):
        existingSet = set(self.getExistingSelection())
        newSet = set(self.getNewSelection())
        diffSet = existingSet - newSet
        self.setExistingSelection(list(diffSet))
        self.selectInFont()

    def replaceSelection(self, sender):
        self.setExistingSelection(self.getNewSelection())
        self.selectInFont()

    def clearSelection(self, sender):
        self.setExistingSelection([])
        self.selectInFont()

if __name__ is "__main__":
    OpenWindow(SelectGlyphSearch)