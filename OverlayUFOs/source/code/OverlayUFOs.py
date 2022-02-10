#!/usr/bin/env python3
"""
RA NOTES:
- drop python2 support
- reorganize folder structure to boilerplate
- switch to merz first
- then subscriber

"""

from AppKit import NSColor, NSFont, NSSmallControlSize, NSTextFieldCell
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.drawingTools import scale, translate
from mojo.events import addObserver, removeObserver
from mojo.extensions import (
    getExtensionDefault,
    getExtensionDefaultColor,
    setExtensionDefault,
    setExtensionDefaultColor,
)
from mojo.roboFont import AllFonts, CurrentFont, OpenFont
from mojo.UI import UpdateCurrentGlyphView
from vanilla import (
    Button,
    CheckBox,
    ColorWell,
    EditText,
    FloatingWindow,
    List,
    RadioGroup,
    TextBox,
)

from lib.tools.drawing import strokePixelPath
from lib.UI.spaceCenter.glyphSequenceEditText import splitText

selectedSymbol = "•"


def SmallTextListCell(editable=False):
    cell = NSTextFieldCell.alloc().init()
    size = NSSmallControlSize  # NSMiniControlSize
    cell.setControlSize_(size)
    font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(size))
    cell.setFont_(font)
    cell.setEditable_(editable)
    return cell


class TX:
    """
    An agnostic way to get a naked font.
    """

    @classmethod
    def naked(cls, f):
        try:
            return f.naked()
        except Exception:
            return f


class Tool:
    """
    The tool object manages the font list. This is a simplification.
    """

    fonts = AllFonts()

    def addObserver(self, target, method, action):
        addObserver(target, method, action)

    def removeObserver(self, target, method, action):
        removeObserver(target, method, action)

    def getCurrentFont(self):
        return CurrentFont()

    def getFonts(self):
        """Answers the list of selected fonts, ordered by their path."""
        return self.fonts

    def appendToFonts(self, path):
        f = OpenFont(path, showInterface=False)
        self.fonts.append(f)

    def removeFromFonts(self, path):
        for index, font in enumerate(self.fonts):
            if font.path == path:
                del self.fonts[index]

    def getFontPaths(self):
        return [f.path or str(f.info.familyName) + " " + str(f.info.styleName) for f in self.getFonts()]

    def getFontLabel(self, path):
        if path is None:
            return None
        if not path:
            return "Untitled"
        name = path.split("/")[-1]
        status = selectedSymbol
        return status, path, name

    def getFontLabels(self):
        labels = {}
        for path in self.getFontPaths():
            if path:
                label = self.getFontLabel(path)
                name = label[-1]
            else:
                name = "Untitled"
            if name not in labels:
                labels[name] = []
            labels[name].append(label)
        sortedLabels = []
        for _, labelSet in sorted(labels.items()):
            if len(labelSet) == 1:  # There is only a single font with this name
                sortedLabels.append(labelSet[0])
            else:  # Otherwise we'll have to construct new names to show the difference
                for status, path, name in sorted(labelSet):
                    sortedLabels.append((status, path, '%s "%s"' % (name, "/".join(path.split("/")[:-1]))))
        return sortedLabels


class C:
    """
    Some constants.
    """

    C2 = 100
    BUTTON_WIDTH = 80
    STYLE_CHECKBOXSIZE = "small"
    STYLE_LABELSIZE = "small"
    STYLE_RADIOSIZE = "small"
    L = 22
    LL = 25


class OverlayUFOs(BaseWindowController):

    DEFAULTKEY = "com.fontbureau.overlayUFO"
    DEFAULTKEY_FILLCOLOR = f"{DEFAULTKEY}.fillColor"
    DEFAULTKEY_STROKECOLOR = f"{DEFAULTKEY}.strokeColor"
    DEFAULTKEY_STROKE = f"{DEFAULTKEY}.stroke"
    DEFAULTKEY_FILL = f"{DEFAULTKEY}.fill"
    FALLBACK_FILLCOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0, 0.5, 0.1)
    FALLBACK_STROKECOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0, 0.5, 0.5)

    VERSION = 1.0

    NAME = "Overlay UFOs"

    MANUAL = """In the current glyph window, this will present the view the same glyph from a separate
    UFO or set of UFOs.<br/>
    This does NOT import the UFO into a background layer. Instead, it renders a outline directly from the UFO into the glyph window view.
    <ul>
    <li>There is no need to import duplicate data into a background layer.</li>
    <li>The source outline is always live; when changes are made to the source, they will automatically
    appear in the current without re-importing.</li>
    <li>The source font does not need to be opened with a UI.</li>
    </ul>
    <h3>DIALOG</h3>
    <ul>
    <li>A floating dialog is present to let you open and select source fonts, fill, stroke, color.</li>
    <li>Source Fonts: The default source font list is self.getOpenFonts(). The refresh button will
    return this list to self.getOpenFonts().</li>
    <li>Adding Fonts: You can manually add fonts by selecting a UFO file.
    The UFO file will open without an interface.</li>
    <li>Removing Fonts: There are buttons for removing selected fonts and for clearing the source font list.</li>
    </ul>
    <h3>BUGS/IMPROVEMENTS</h3>
    <ul>
    <li>Known Issue: The source font is drawn on top of the current font, instead of behind it.
    So, it is good to select a color with a low opacity.</li>
    <li>Known Bug: If the glyph window for both source and current fonts are open, it is possible
    to select and inadvertently edit the source outline in the current window. I don't know how to solve this.</li>
    <li>Improvement?: Add options to scale the source font.</li>
    <li>Improvement?: Set different colors, fill settings for each font?</li>
    </ul>
    """

    # Fixed width of the window.
    VIEWMINSIZE = 400
    VIEWSIZE = VIEWMINSIZE
    VIEWMAXSIZE = VIEWMINSIZE

    WINDOW_POSSIZE = (130, 20, VIEWSIZE, 260)
    WINDOW_MINSIZE = (VIEWMINSIZE, 260)
    WINDOW_MAXSIZE = (VIEWMAXSIZE, 260)

    def getPathListDescriptor(self):
        return [
            dict(title="Status", key="status", cell=SmallTextListCell(editable=False), width=12, editable=False),
            dict(title="Name", key="name", width=300, cell=SmallTextListCell(editable=False), editable=False),
            dict(title="Path", key="path", width=0, editable=False),
        ]

    ################
    # OBSERVERS AND UPDATERS
    ################

    def fontSelectionChanged(self):
        self.setSourceFonts()

    def activateModule(self):
        self.tool.addObserver(self, "drawInactive", "drawInactive")
        self.tool.addObserver(self, "drawBackground", "drawBackground")
        self.tool.addObserver(self, "fontDidOpen", "fontDidOpen")
        self.tool.addObserver(self, "fontWillClose", "fontWillClose")

    def deactivateModule(self):
        removeObserver(self, "drawBackground")
        removeObserver(self, "drawInactive")
        removeObserver(self, "fontDidOpen")
        removeObserver(self, "fontWillClose")

    ################
    # CONTEXTS
    ################

    def fontDidOpen(self, info):
        font = info.get("font")
        if font:
            self.tool.fonts.append(font)
            self.refreshCallback()

    def fontWillClose(self, info):
        font = info.get("font")
        path = font.path
        if path:
            self.tool.removeFromFonts(path)
            self.refreshCallback()

    def __init__(self):
        self.tool = Tool()
        self.w = FloatingWindow((400, 200), "Overlay UFOs", minSize=(400, 200))
        self.populateView()
        self.getView().open()

    def getView(self):
        return self.w

    def refreshCallback(self, sender=None):
        """
        Update the font list.
        """
        self.getView().fontList.set(self.getFontItems())

    def resetCallback(self, sender=None):
        """
        Resets the view to the currently opened fonts.
        """
        self.tool.fonts = AllFonts()
        self.getView().fontList.set(self.getFontItems())

    def addCallback(self, sender=None):
        """
        Open a font without UI and add it to the font list.
        """
        f = OpenFont(None, showInterface=False)
        if f is None:
            return
        self.tool.appendToFonts(f.path)
        self.refreshCallback()

    def populateView(self):
        """
        The UI
        """
        self.fillColor = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)
        self.strokeColor = getExtensionDefaultColor(self.DEFAULTKEY_STROKECOLOR, self.FALLBACK_STROKECOLOR)
        self.contextBefore = self.contextAfter = ""

        # Populating the view can only happen after the view is attached to the window,
        # or else the relative widths go wrong.
        view = self.getView()
        view.add = Button((-40, 3, 30, 22), "+", callback=self.addCallback)
        view.reset = Button((-40, 30, 30, 22), chr(8634), callback=self.resetCallback)
        # Flag to see if the selection list click is in progress. We are resetting the selection
        # ourselves, using the list "buttons", but changing that selection will cause another
        # list update, that should be ignored.
        self._selectionChanging = False
        # Indicate that we are a drawing module
        self._canDraw = True

        self.sources = []

        x = y = 4

        view.fontList = List(
            (C.C2, y, 250, -65),
            self.getFontItems(),
            selectionCallback=self.fontListCallback,
            drawFocusRing=False,
            enableDelete=False,
            allowsMultipleSelection=False,
            allowsEmptySelection=True,
            drawHorizontalLines=True,
            showColumnTitles=False,
            columnDescriptions=self.getPathListDescriptor(),
            rowHeight=16,
        )
        view.viewEnabled = CheckBox(
            (x, y, C.BUTTON_WIDTH, 22), "Show", callback=self.viewCallback, sizeStyle=C.STYLE_CHECKBOXSIZE, value=True
        )
        y += C.L
        view.fill = CheckBox(
            (x, y, 60, 22),
            "Fill",
            sizeStyle=C.STYLE_CHECKBOXSIZE,
            # value=getExtensionDefault("%s.%s" %(self.DEFAULTKEY, "fill"), True),
            value=True,
            callback=self.fillCallback,
        )
        y += C.L
        color = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)
        view.color = ColorWell((x, y, 60, 22), color=color, callback=self.colorCallback)
        y += C.L + 5
        view.stroke = CheckBox(
            (x, y, 60, 22),
            "Stroke",
            sizeStyle=C.STYLE_CHECKBOXSIZE,
            # value=getExtensionDefault("%s.%s" %(self.DEFAULTKEY, "stroke"), False),
            value=False,
            callback=self.strokeCallback,
        )

        y += C.LL
        view.alignText = TextBox((x, y, 90, 50), "Alignment", sizeStyle=C.STYLE_LABELSIZE)
        y += C.L
        view.align = RadioGroup(
            (x, y, 90, 50),
            ["Left", "Center", "Right"],
            isVertical=True,
            sizeStyle=C.STYLE_RADIOSIZE,
            callback=self.alignCallback,
        )
        view.align.set(0)

        # view.contextLabel = TextBox((C.C2, -58, 90, 50), 'Contexts', sizeStyle=C.STYLE_LABELSIZE)

        view.viewCurrent = CheckBox(
            (C.C2, -60, 150, 22),
            "Always View Current",
            sizeStyle=C.STYLE_CHECKBOXSIZE,
            value=False,
            callback=self.contextEditCallback,
        )

        # view.contextUandlc = CheckBox((C.C2+170, -60, 85, 22), "Match Case", sizeStyle=C.STYLE_CHECKBOXSIZE,
        #    value = False,
        #    callback=self.contextEditCallback)

        view.contextBefore = EditText(
            (C.C2, -30, 85, 20),
            callback=self.contextEditCallback,
            continuous=True,
            sizeStyle="small",
            placeholder="Left Context",
        )
        view.contextCurrent = EditText(
            (C.C2 + 95, -30, 60, 20), callback=self.contextCurrentEditCallback, continuous=True, sizeStyle="small"
        )
        view.contextAfter = EditText(
            (C.C2 + 165, -30, 85, 20),
            callback=self.contextEditCallback,
            continuous=True,
            sizeStyle="small",
            placeholder="Right Context",
        )
        self.activateModule()
        self.setUpBaseWindowBehavior()

    def fontListCallback(self, sender):
        """If there is a selection, toggle the status of these fonts."""
        # Avoid recursive loop because of changing font selection
        if not self._selectionChanging:
            for selectedIndex in sender.getSelection():
                item = sender.get()[selectedIndex]
                if item["status"]:
                    item["status"] = ""
                else:
                    item["status"] = selectedSymbol
            self._selectionChanging = True
            # Avoid recursive loop because of changing font selection
            sender.setSelection([])
            self._selectionChanging = False
        self.updateView()

    def canDraw(self):
        return True

    def getHiddenFont(self, path):
        from builtins import str

        for f in self.tool.getFonts():
            if f.path == path:
                return f
            elif path == str(f.info.familyName) + " " + str(f.info.styleName):
                return f

    def drawBackground(self, info):
        """Draw the background of defined glyphs and fonbts.
        Scale is available as mouse.scale."""
        view = self.getView()
        if not view.viewEnabled.get():
            return
        fill = getExtensionDefault(self.DEFAULTKEY_FILL, True)
        stroke = getExtensionDefault(self.DEFAULTKEY_STROKE, True)
        fillcolor = getExtensionDefaultColor(self.DEFAULTKEY_FILLCOLOR, self.FALLBACK_FILLCOLOR)

        glyph = info.get("glyph")
        if glyph is not None:
            current = glyph.font
        else:
            current = self.tool.getCurrentFont()
        if glyph is None or current is None:
            return
        align = self.getAlignment()

        # Get the fonts from the list and see if they are selected.
        sourceItems = self.getSourceFonts()
        showFonts = []
        for item in sourceItems:
            if not item["status"]:
                continue
            path = item["path"]
            font = self.getHiddenFont(path)
            showFonts.append(font)

        if view.viewCurrent.get() and current not in showFonts:
            showFonts.append(current)

        for font in showFonts:
            self.fillColor.setFill()
            self.strokeColor.setStroke()

            contextBefore, contextCurrent, contextAfter = self.getContexts()

            if font is not None:
                contextBefore = splitText(contextBefore, TX.naked(font).unicodeData, TX.naked(font).groups)
                contextBefore = [font[gname] for gname in contextBefore if gname in font.keys()]
                contextAfter = splitText(contextAfter, TX.naked(font).unicodeData, TX.naked(font).groups)
                contextAfter = [font[gname] for gname in contextAfter if gname in font.keys()]
                contextCurrent = splitText(contextCurrent, TX.naked(font).unicodeData, TX.naked(font).groups)
                if len(contextCurrent) > 0:
                    contextCurrent = [font[gname] for gname in [contextCurrent[0]] if gname in font.keys()]
                    if len(contextCurrent) > 0:
                        sourceGlyph = contextCurrent[0]
                    else:
                        sourceGlyph = None
                elif glyph.name in font.keys():
                    sourceGlyph = font[glyph.name]
                else:
                    sourceGlyph = None

                scale(current.info.unitsPerEm / float(font.info.unitsPerEm))

                widthOffset = 0
                if sourceGlyph is not None:
                    if align == "center":
                        destCenter = float(glyph.width / 2) / current.info.unitsPerEm
                        sourceCenter = float(sourceGlyph.width / 2) / font.info.unitsPerEm
                        widthOffset = (destCenter - sourceCenter) * font.info.unitsPerEm
                    elif align == "right":
                        widthOffset = (
                            (glyph.width / glyph.font.info.unitsPerEm)
                            - (sourceGlyph.width / sourceGlyph.font.info.unitsPerEm)
                        ) * font.info.unitsPerEm
                translate(widthOffset, 0)

                previousGlyph = sourceGlyph
                contextBefore.reverse()
                totalWidth = 0
                for i, cbGlyph in enumerate(contextBefore):
                    kernValue = 0
                    if previousGlyph is not None and previousGlyph.font == cbGlyph.font:
                        # Uncomment to activate kerning. Requires FontTX.
                        # kernValue += FontTX.kerning.getValue((previousGlyph.name, cbGlyph.name), font.kerning, font.groups)
                        kernValue += 0

                    translate(-cbGlyph.width - kernValue, 0)
                    totalWidth += cbGlyph.width + kernValue
                    drawGlyphPath = TX.naked(cbGlyph).getRepresentation("defconAppKit.NSBezierPath")
                    if view.fill.get():
                        drawGlyphPath.fill()
                    if view.stroke.get():
                        strokePixelPath(drawGlyphPath)
                    previousGlyph = cbGlyph
                translate(totalWidth, 0)

                totalWidth = 0
                contextCurrentAndAfter = [sourceGlyph] + contextAfter

                for i, cbGlyph in enumerate(contextCurrentAndAfter):
                    if cbGlyph is None:
                        cbGlyph = sourceGlyph
                    nextGlyph = None
                    if i + 1 < len(contextCurrentAndAfter):
                        nextGlyph = contextCurrentAndAfter[i + 1]
                    if (i == 0 and cbGlyph == glyph) or sourceGlyph is None:
                        pass
                    else:
                        drawGlyphPath = TX.naked(cbGlyph).getRepresentation("defconAppKit.NSBezierPath")
                        if view.fill.get():
                            drawGlyphPath.fill()
                        if view.stroke.get():
                            strokePixelPath(drawGlyphPath)
                    kernValue = 0

                    if cbGlyph is not None and nextGlyph is not None and nextGlyph.font == cbGlyph.font:
                        # kernValue = FontTX.kerning.getValue((cbGlyph.name, nextGlyph.name), font.kerning, font.groups)
                        # Uncomment to activate kerning. Requires FontTX.
                        kernValue = 0

                    width = 0
                    if cbGlyph is not None:
                        width = cbGlyph.width
                    translate(width + kernValue, 0)
                    totalWidth += width + kernValue
                    previousGlyph = cbGlyph

                translate(-totalWidth, 0)

                translate(-widthOffset, 0)
                scale(font.info.unitsPerEm / float(current.info.unitsPerEm))
        # restore()

    drawInactive = drawBackground

    def viewCallback(self, sender):
        self.updateView()

    def getSourceFonts(self):
        """
        Get the fonts in the list.
        """
        view = self.getView()
        return view.fontList.get()

    def setSourceFonts(self):
        """
        Set the font list from the current set of open fonts.
        """
        view = self.getView()
        labels = []
        currentSelection = []
        for d in self.getSourceFonts():
            if d["status"]:
                currentSelection.append(d["path"])
        for status, path, name in self.tool.getFontLabels():
            if path in currentSelection:
                status = selectedSymbol
            else:
                status = ""
            labels.append(dict(status=status, path=path, name=name))
        view.fontList.set(labels)

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

    def alignCallback(self, sender):
        """
        Change the alignment status.
        """
        self.updateView()

    def getAlignment(self):
        """
        Get the alignment as a string.
        """
        view = self.getView()
        index = view.align.get()
        if index == 0:
            return "left"
        elif index == 1:
            return "center"
        elif index == 2:
            return "right"

    def updateView(self, sender=None):
        UpdateCurrentGlyphView()

    def windowCloseCallback(self, sender):
        self.deactivateModule()
        self.updateView()
        BaseWindowController.windowCloseCallback(self, sender)

    def getFontItems(self, update=False):
        """
        Get all fonts in a way that can be set into a vanilla list.
        """
        paths = set()  # Set of all unique paths in the merges lists
        itemsByName = {}
        if update:  # If update flag is set, then keep the existing selected fonts.
            for item in self.getSourceFonts():
                if item["status"]:
                    itemsByName[item["name"]] = item
        currentStatuses = {}
        if hasattr(self.getView(), "fontList"):
            for d in self.getSourceFonts():
                currentStatuses[d["path"]] = d["status"]

        for status, path, uniqueName in self.tool.getFontLabels():
            if path in currentStatuses:
                status = currentStatuses[path]
            else:
                status = selectedSymbol

            if uniqueName not in itemsByName.keys():  # If it is not already there, add this to the list
                itemsByName[uniqueName] = dict(status=status, path=path, name=uniqueName)
        fontList = []
        for key, item in sorted(itemsByName.items()):
            fontList.append(item)
        return fontList

    ################
    # CONTEXTS
    ################

    def getContexts(self):
        if not hasattr(self, "contextBefore"):
            self.contextBefore = ""
        if not hasattr(self, "contextAfter"):
            self.contextAfter = ""
        if not hasattr(self, "contextCurrent"):
            self.contextCurrent = None
        return self.contextBefore, self.contextCurrent, self.contextAfter

    def setContexts(self, contextBefore, contextCurrent, contextAfter):

        self.contextBefore = contextBefore
        self.contextCurrent = contextCurrent
        self.contextAfter = contextAfter

    def contextEditCallback(self, sender):
        before = self.getView().contextBefore.get()
        current = self.getView().contextCurrent.get() or None
        after = self.getView().contextAfter.get()
        self.setContexts(before, current, after)
        self.updateView()

    def contextCurrentEditCallback(self, sender):
        # if sender.get():
        # sender.set(sender.get()[0])
        self.contextEditCallback(sender)


if __name__ == "__main__":
    OverlayUFOs()
