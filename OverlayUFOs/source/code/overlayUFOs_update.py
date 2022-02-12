from pathlib import Path

from AppKit import NSColor, NSFont, NSSmallControlSize, NSTextFieldCell
from mojo.events import addObserver, removeObserver
from mojo.extensions import (
    getExtensionDefault,
    getExtensionDefaultColor,
    setExtensionDefault,
    setExtensionDefaultColor,
)
from mojo.roboFont import AllFonts, OpenFont, OpenWindow
from mojo.subscriber import (
    Subscriber,
    WindowController,
    registerGlyphEditorSubscriber,
    registerRoboFontSubscriber,
    unregisterGlyphEditorSubscriber,
    unregisterRoboFontSubscriber,
)
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

DEBUG_MODE = True

# tool keys
DEFAULTKEY = "com.fontbureau.overlayUFO"
DEFAULTKEY_CONTAINER = f"{DEFAULTKEY}.backgroundContainer"
DEFAULTKEY_FILLCOLOR = f"{DEFAULTKEY}.fillColor"
DEFAULTKEY_STROKECOLOR = f"{DEFAULTKEY}.strokeColor"
DEFAULTKEY_STROKE = f"{DEFAULTKEY}.stroke"
DEFAULTKEY_FILL = f"{DEFAULTKEY}.fill"
FALLBACK_FILLCOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0, 0.5, 0.1)
FALLBACK_STROKECOLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0, 0.5, 0.5)

# Fixed width of the window
VIEW_MIN_SIZE = 400
VIEWSIZE = VIEW_MIN_SIZE
VIEW_MAX_SIZE = VIEW_MIN_SIZE
WINDOW_POSSIZE = (130, 20, VIEWSIZE, 260)
WINDOW_MINSIZE = (VIEW_MIN_SIZE, 260)
WINDOW_MAXSIZE = (VIEW_MAX_SIZE, 260)

# UI constants
C2 = 100
BUTTON_WIDTH = 80
CONTROLS_SIZE_STYLE = "small"

L = 22
LL = 25

SELECTED_SYMBOL = "•"


def SmallTextListCell(editable=False):
    cell = NSTextFieldCell.alloc().init()
    size = NSSmallControlSize
    cell.setControlSize_(size)
    font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(size))
    cell.setFont_(font)
    cell.setEditable_(editable)
    return cell


class GlyphEditorSubscriber(Subscriber):

    debug = DEBUG_MODE

    def build(self):
        glyphEditor = self.getGlyphEditor()
        self.container = glyphEditor.getExtensionContainer(
            identifier=DEFAULTKEY_CONTAINER, position="background", clear=True
        )

    def destroy(self):
        self.container.clearSublayers()


class FontListManager(Subscriber):
    """
    The tool object manages the font list. This is a simplification.
    """

    debug = DEBUG_MODE
    fonts = AllFonts()

    def fontDocumentDidOpen(self, info):
        font = info.get("font")
        if font:
            self.tool.fonts.append(font)
            self.controller.refreshCallback()

    def fontDocumentWillClose(self, info):
        path = info["font"].path
        if path:
            self.removeFromFonts(path)
            self.controller.refreshCallback()

    def appendToFonts(self, path):
        f = OpenFont(path, showInterface=False)
        self.fonts.append(f)

    def removeFromFonts(self, path):
        for index, font in enumerate(self.fonts):
            if font.path == path:
                del self.fonts[index]

    def getFontLabel(self, path):
        if path is None:
            return None
        if not path:
            return "Untitled"
        name = path.split("/")[-1]
        status = SELECTED_SYMBOL
        return status, path, name

    def getFontLabels(self):
        labels = {}
        fontPaths = [f.path or f"{f.info.familyName} {f.info.styleName}" for f in self.fonts]
        for path in fontPaths:
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
            # There is only a single font with this name
            if len(labelSet) == 1:
                sortedLabels.append(labelSet[0])
            # Otherwise we'll have to construct new names to show the difference
            else:
                for status, path, name in sorted(labelSet):
                    sortedLabels.append((status, path, f'{name} "{Path(path).parent}"'))
        return sortedLabels


class OverlayUFOs(WindowController):

    debug = DEBUG_MODE

    def build(self):
        self.fontListManager = FontListManager()
        self.w = FloatingWindow((400, 200), "Overlay UFOs", minSize=(400, 200))
        self.populateWindow()
        self.w.open()

    def started(self):
        GlyphEditorSubscriber.controller = self
        registerGlyphEditorSubscriber(GlyphEditorSubscriber)

        FontListManager.controller = self
        registerRoboFontSubscriber(FontListManager)

    def destroy(self, sender):
        GlyphEditorSubscriber.controller = None
        unregisterGlyphEditorSubscriber(GlyphEditorSubscriber)

        FontListManager.controller = None
        unregisterRoboFontSubscriber(FontListManager)
        self.updateView()

        if DEBUG_MODE:
            for eachFont in AllFonts():
                eachFont.close()

    def refreshCallback(self, sender=None):
        """
        Update the font list.
        """
        self.w.fontList.set(self.getFontItems())

    def resetCallback(self, sender=None):
        """
        Resets the view to the currently opened fonts.
        """
        self.fontListManager.fonts = AllFonts()
        self.w.fontList.set(self.getFontItems())

    def addCallback(self, sender=None):
        """
        Open a font without UI and add it to the font list.
        """
        f = OpenFont(None, showInterface=False)
        if f is None:
            return
        self.fontListManager.appendToFonts(f.path)
        self.refreshCallback()

    def populateWindow(self):
        """
        The UI
        """
        self.fillColor = getExtensionDefaultColor(DEFAULTKEY_FILLCOLOR, FALLBACK_FILLCOLOR)
        self.strokeColor = getExtensionDefaultColor(DEFAULTKEY_STROKECOLOR, FALLBACK_STROKECOLOR)
        self.contextBefore = self.contextAfter = ""

        # Populating the view can only happen after the view is attached to the window,
        # or else the relative widths go wrong.
        self.w.add = Button((-40, 3, 30, 22), "+", callback=self.addCallback)
        self.w.reset = Button((-40, 30, 30, 22), chr(8634), callback=self.resetCallback)

        # Flag to see if the selection list click is in progress. We are resetting the selection
        # ourselves, using the list "buttons", but changing that selection will cause another
        # list update, that should be ignored.
        self._selectionChanging = False

        x = y = 4

        self.w.fontList = List(
            (C2, y, 250, -65),
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
        self.w.viewEnabled = CheckBox(
            (x, y, BUTTON_WIDTH, 22), "Show", callback=self.viewCallback, sizeStyle=CONTROLS_SIZE_STYLE, value=True
        )
        y += L
        self.w.fill = CheckBox(
            (x, y, 60, 22),
            "Fill",
            sizeStyle=CONTROLS_SIZE_STYLE,
            value=True,
            callback=self.fillCallback,
        )
        y += L
        color = getExtensionDefaultColor(DEFAULTKEY_FILLCOLOR, FALLBACK_FILLCOLOR)
        self.w.color = ColorWell((x, y, 60, 22), color=color, callback=self.colorCallback)
        y += L + 5
        self.w.stroke = CheckBox(
            (x, y, 60, 22),
            "Stroke",
            sizeStyle=CONTROLS_SIZE_STYLE,
            value=False,
            callback=self.strokeCallback,
        )

        y += LL
        self.w.alignText = TextBox((x, y, 90, 50), "Alignment", sizeStyle=CONTROLS_SIZE_STYLE)
        y += L
        self.w.align = RadioGroup(
            (x, y, 90, 50),
            ["Left", "Center", "Right"],
            isVertical=True,
            sizeStyle=CONTROLS_SIZE_STYLE,
            callback=self.alignCallback,
        )
        self.w.align.set(0)

        self.w.viewCurrent = CheckBox(
            (C2, -60, 150, 22),
            "Always View Current",
            sizeStyle=CONTROLS_SIZE_STYLE,
            value=False,
            callback=self.contextEditCallback,
        )

        self.w.contextBefore = EditText(
            (C2, -30, 85, 20),
            callback=self.contextEditCallback,
            continuous=True,
            sizeStyle="small",
            placeholder="Left Context",
        )
        self.w.contextCurrent = EditText(
            (C2 + 95, -30, 60, 20), callback=self.contextCurrentEditCallback, continuous=True, sizeStyle="small"
        )
        self.w.contextAfter = EditText(
            (C2 + 165, -30, 85, 20),
            callback=self.contextEditCallback,
            continuous=True,
            sizeStyle="small",
            placeholder="Right Context",
        )

    def viewCallback(self, sender):
        pass
        # self.updateView()

    def fontListCallback(self, sender):
        """If there is a selection, toggle the status of these fonts."""
        # Avoid recursive loop because of changing font selection
        if not self._selectionChanging:
            for selectedIndex in sender.getSelection():
                item = sender.get()[selectedIndex]
                if item["status"]:
                    item["status"] = ""
                else:
                    item["status"] = SELECTED_SYMBOL
            self._selectionChanging = True
            # Avoid recursive loop because of changing font selection
            sender.setSelection([])
            self._selectionChanging = False
        self.updateView()

    def getHiddenFont(self, path):
        for f in self.fontListManager.fonts:
            if f.path == path:
                return f
            elif path == f"{f.info.familyName} {f.info.styleName}":
                return f

    def getFontItems(self, update=False):
        """
        Get all fonts in a way that can be set into a vanilla list.
        """
        itemsByName = {}
        if update:  # if update flag is set, then keep the existing selected fonts
            for item in self.getSourceFonts():
                if item["status"]:
                    itemsByName[item["name"]] = item
        currentStatuses = {}
        if hasattr(self.w, "fontList"):
            for d in self.getSourceFonts():
                currentStatuses[d["path"]] = d["status"]

        for status, path, uniqueName in self.fontListManager.getFontLabels():
            if path in currentStatuses:
                status = currentStatuses[path]
            else:
                status = SELECTED_SYMBOL

            if uniqueName not in itemsByName.keys():  # If it is not already there, add this to the list
                itemsByName[uniqueName] = dict(status=status, path=path, name=uniqueName)
        fontList = []
        for _, item in sorted(itemsByName.items()):
            fontList.append(item)
        return fontList

    def getPathListDescriptor(self):
        return [
            dict(title="Status", key="status", cell=SmallTextListCell(editable=False), width=12, editable=False),
            dict(title="Name", key="name", width=300, cell=SmallTextListCell(editable=False), editable=False),
            dict(title="Path", key="path", width=0, editable=False),
        ]

    def getSourceFonts(self):
        """
        Get the fonts in the list.
        """
        return self.w.fontList.get()

    def setSourceFonts(self):
        """
        Set the font list from the current set of open fonts.
        """
        labels = []
        currentSelection = []
        for d in self.getSourceFonts():
            if d["status"]:
                currentSelection.append(d["path"])
        for status, path, name in self.tool.getFontLabels():
            if path in currentSelection:
                status = SELECTED_SYMBOL
            else:
                status = ""
            labels.append(dict(status=status, path=path, name=name))
        self.w.fontList.set(labels)

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
        setExtensionDefaultColor(DEFAULTKEY_FILLCOLOR, selectedColor)
        setExtensionDefaultColor(DEFAULTKEY_STROKECOLOR, strokeColor)
        self.fillColor = selectedColor
        self.strokeColor = strokeColor
        self.updateView()

    def fillCallback(self, sender):
        """
        Change the fill status.
        """
        setExtensionDefault(DEFAULTKEY_FILL, sender.get())
        self.updateView()

    def strokeCallback(self, sender):
        """
        Change the stroke status.
        """
        setExtensionDefault(DEFAULTKEY_STROKE, sender.get())
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
        index = self.w.align.get()
        int_2_alignment = {0: "left", 1: "center", 2: "right"}
        return int_2_alignment[index]

    def updateView(self, sender=None):
        pass

    def fontSelectionChanged(self):
        self.setSourceFonts()

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
        before = self.w.contextBefore.get()
        current = self.w.contextCurrent.get() or None
        after = self.w.contextAfter.get()
        self.setContexts(before, current, after)
        self.updateView()

    def contextCurrentEditCallback(self, sender):
        self.contextEditCallback(sender)


if __name__ == "__main__":

    if DEBUG_MODE:
        testFontsFolder = Path.home() / "Desktop/mutatorSans"
        for eachFontPath in [ff for ff in testFontsFolder.iterdir() if ff.suffix == ".ufo"]:
            OpenFont(eachFontPath, showInterface=True)

        try:
            OpenWindow(OverlayUFOs)
        except Exception as error:
            for eachFont in AllFonts():
                eachFont.close()
            raise error

    else:
        OpenWindow(OverlayUFOs)
