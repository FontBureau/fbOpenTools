from pathlib import Path

from AppKit import NSColor, NSFont, NSSmallControlSize, NSTextFieldCell
from mojo.events import postEvent
from mojo.extensions import NSColorToRgba, getExtensionDefault, setExtensionDefault
from mojo.roboFont import AllFonts, OpenFont, OpenWindow
from mojo.subscriber import (
    Subscriber,
    WindowController,
    registerCurrentGlyphSubscriber,
    registerGlyphEditorSubscriber,
    registerRoboFontSubscriber,
    unregisterCurrentGlyphSubscriber,
    unregisterGlyphEditorSubscriber,
    unregisterRoboFontSubscriber,
)
from mojo.UI import AllGlyphWindows, splitText
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

# tool keys
from customEvents import DEBUG_MODE, DEFAULTKEY

DEFAULTKEY_CONTAINER = f"{DEFAULTKEY}.backgroundContainer"
DEFAULTKEY_FILLCOLOR = f"{DEFAULTKEY}.fillColor"
DEFAULTKEY_STROKECOLOR = f"{DEFAULTKEY}.strokeColor"
DEFAULTKEY_STROKE = f"{DEFAULTKEY}.stroke"
DEFAULTKEY_FILL = f"{DEFAULTKEY}.fill"
FALLBACK_FILLCOLOR = (0.5, 0, 0.5, 0.1)
FALLBACK_STROKECOLOR = (0.5, 0, 0.5, 0.5)

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


class GlyphNamesEditText(EditText):

    """
    Custom Edit Text
    adds .getFirstName() method to basic functionality

    """

    _title = None

    def __init__(self, *args, **kwargs):
        super(GlyphNamesEditText, self).__init__(*args, **kwargs)

    def getFirstName(self, font):
        """
        Provide the first glyph name from the splitText() call, otherwise return an empty string
        """
        names = splitText(self.get(), font.getCharacterMapping(), groups=font.groups)
        return names[0] if len(names) > 0 else ""

    @property
    def title(self):
        """
        We need a title value to post the contextDidChange event

        """
        return self._title

    @title.setter
    def title(self, value):
        self._title = value


class CurrentGlyphSubscriber(Subscriber):

    debug = DEBUG_MODE

    def currentGlyphDidChange(self, info):
        """
        Post events only for interesting glyph cutting non-useful notifications

        """
        glyph = info["glyph"]
        editorGlyphNames = [editor.getGlyph().name for editor in AllGlyphWindows()]
        if glyph.name in editorGlyphNames:
            postEvent(f"{DEFAULTKEY}.displayedGlyphDidChange", glyph=glyph)

        contextNames = [
            self.controller.w.contextBefore.getFirstName(font=glyph.font),
            self.controller.w.contextCurrent.getFirstName(font=glyph.font),
            self.controller.w.contextAfter.getFirstName(font=glyph.font),
        ]
        if glyph.name in contextNames:
            postEvent(f"{DEFAULTKEY}.displayedGlyphDidChange", glyph=glyph)


class GlyphEditorSubscriber(Subscriber):

    debug = DEBUG_MODE

    def build(self):
        """
        Add merz layers to the container

        """
        glyphEditor = self.getGlyphEditor()
        self.container = glyphEditor.extensionContainer(
            identifier=DEFAULTKEY_CONTAINER, location="background", clear=True
        )

        self.contextBeforeLayer = self.container.appendBaseSublayer(name="contextBefore")
        self.contextCurrentLayer = self.container.appendBaseSublayer(name="contextCurrent")
        self.contextAfterLayer = self.container.appendBaseSublayer(name="contextAfter")

        self._traverseGlyphLayers(position="contextBefore", onlyAlignment=False)
        self._traverseGlyphLayers(position="contextCurrent", onlyAlignment=False)
        self._traverseGlyphLayers(position="contextAfter", onlyAlignment=False)

    def destroy(self):
        """
        Cleanup!

        """
        self.container.clearSublayers()

    def glyphEditorDidSetGlyph(self, info):
        """
        Catch:
            - glyph switches in the editor
            - when becomes first responder
        So, we rebuild the current glyph

        """
        glyphObj = info["glyph"]
        if self._getCurrentGlyphName(font=glyphObj.font) == glyphObj.name:
            self._traverseGlyphLayers(position="contextCurrent", onlyAlignment=False)
        self.alignmentDidChange(info=None)

    def _traverseGlyphLayers(self, position, onlyAlignment=True):
        """
        Lengthy method that abstracts the heavy lifting of dealing with merz layers in the subscriber.
        It is able to:
            - traverse all the merz layers
            - add glyph paths or adjust x position (when alignment is changed)

        """
        assert position in {"contextBefore", "contextCurrent", "contextAfter"}

        glyphEditorGlyph = self.getGlyphEditor().getGlyph()
        baseLayer = self.container.getSublayer(name=f"{position}")
        if not onlyAlignment:
            baseLayer.clearSublayers()

        for fontData in self.controller.w.fontList.get():

            # QUESTION: do we need to support unsaved fonts?
            for eachFont in self.controller.fonts:
                if eachFont.path == fontData["path"]:
                    break

            if position == "contextCurrent":
                displayedName = self._getCurrentGlyphName(font=eachFont)
            else:
                displayedName = getattr(self.controller.w, position).getFirstName(font=eachFont)

            # we bail out if the glyph name is an empty string
            # we bail out if there is no available glyph
            if not displayedName or displayedName not in eachFont:
                continue

            glyphObj = eachFont[displayedName]
            if self.controller.w.align.get() == 0:  # left
                x = 0
            elif self.controller.w.align.get() == 1:  # center
                x = glyphEditorGlyph.width / 2 - glyphObj.width / 2
            else:  # right
                x = glyphEditorGlyph.width - glyphObj.width

            # adjusting x according to current glyph in the editor
            if position == "contextAfter":
                x += glyphEditorGlyph.width
            elif position == "contextBefore":
                x -= glyphEditorGlyph.width

            # adding a new layer
            if not onlyAlignment:
                glyphLayer = baseLayer.appendPathSublayer(
                    name=f"{displayedName}.{fontData['path']}",
                    fillColor=self.controller.fillColor,
                    strokeColor=self.controller.strokeColor,
                    position=(x, 0),
                )
                glyphPath = glyphObj.getRepresentation("merz.CGPath")
                glyphLayer.setPath(glyphPath)
            # adjusting the x value
            else:
                glyphLayer = baseLayer.getSublayer(
                    name=f"{displayedName}.{fontData['path']}",
                )
                glyphLayer.setPosition((x, 0))

            # fix visibility according to viewCurrent checkbox and current glyph in editor
            # we don't show invisible fonts or the current glyph in the editor
            # the viewCurrent might override the status from the fontList
            onlyCurrentView = self.controller.w.viewCurrent.get()
            if glyphObj.asDefcon() is glyphEditorGlyph:
                visibility = False
            elif onlyCurrentView:
                visibility = glyphEditorGlyph.font is glyphObj.font.asDefcon()
            else:
                visibility = bool(fontData["status"])
            glyphLayer.setVisible(visibility)

    def displayedGlyphDidChange(self, info):
        """
        Take care of resetting a glyph path if it changed somewhere

        """
        glyph = info["glyph"]

        displayedNames = [
            self._getCurrentGlyphName(font=glyph.font),
            getattr(self.controller.w, "contextBefore").getFirstName(font=glyph.font),
            getattr(self.controller.w, "contextAfter").getFirstName(font=glyph.font),
        ]

        for eachBaseLayer in self.container.getSublayers():
            for eachGlyphLayer in eachBaseLayer.getSublayers():
                layerName = eachGlyphLayer.getName()
                someName, somePath = layerName.split(".", maxsplit=1)
                if someName in displayedNames and somePath.endswith(glyph.font.path):
                    eachGlyphLayer.setPath(glyph.getRepresentation("merz.CGPath"))

    def _getCurrentGlyphName(self, font):
        """
        Based on currentContext edit text controller and font cmap

        """
        glyphEditorGlyph = self.getGlyphEditor().getGlyph()
        return (
            self.controller.w.contextCurrent.getFirstName(font)
            if self.controller.w.contextCurrent.getFirstName(font)
            else glyphEditorGlyph.name
        )

    def alignmentDidChange(self, info):
        """
        Used to adjust alignment when user input new value in the radio group or
        when the user switches to another glyph in the editor

        """
        self._traverseGlyphLayers(position="contextBefore", onlyAlignment=True)
        self._traverseGlyphLayers(position="contextCurrent", onlyAlignment=True)
        self._traverseGlyphLayers(position="contextAfter", onlyAlignment=True)

    def alwaysCurrentViewDidChange(self, info):
        """
        When currentView changes we only need to traverse all the merz layers
        at the end of the method are checked the criteria for visibility for each layer
        the convenience layer for this is alignmentDidChange 🤷‍♂️

        """
        self.alignmentDidChange(info=None)

    def displayedFontsDidChange(self, info):
        """
        Adjust the merz layers visibility according to parameters from the self.w.fontList

        """
        for fontData in self.controller.w.fontList.get():
            for eachLayer in self.container.getSublayers():
                if eachLayer.getName().endswith(fontData["path"]):
                    eachLayer.setVisible(bool(fontData["status"]))

    def contextDidChange(self, info):
        """
        Adjust the merz layers based on changes from the context custom edit texts

        """
        self._traverseGlyphLayers(position=info["position"], onlyAlignment=False)

    def colorDidChange(self, info):
        """
        Adjust the merz layers according to the color well

        """
        with self.container.propertyGroup():
            for eachBaseLayer in self.container.getSublayers():
                for eachGlyphLayer in eachBaseLayer.getSublayers():
                    eachGlyphLayer.setFillColor(self.controller.fillColor)
                    eachGlyphLayer.setStrokeColor(self.controller.strokeColor)

    def fillCheckBoxDidChange(self, info):
        """
        Adjust the merz layers according to the fill check box

        """
        r, g, b, a = self.controller.fillColor
        a = a if self.controller.w.fill.get() else 0
        with self.container.propertyGroup():
            for eachBaseLayer in self.container.getSublayers():
                for eachGlyphLayer in eachBaseLayer.getSublayers():
                    eachGlyphLayer.setFillColor((r, g, b, a))

    def strokeCheckBoxDidChange(self, info):
        """
        Adjust the merz layers according to the stroke check box

        """
        thickness = 1 if self.controller.w.stroke.get() else 0
        with self.container.propertyGroup():
            for eachBaseLayer in self.container.getSublayers():
                for eachGlyphLayer in eachBaseLayer.getSublayers():
                    eachGlyphLayer.setStrokeWidth(thickness)

    def fontListDidChange(self, info):
        """
        If the font list changes, we rebuild all the layers
        No need for real speed in this situation, we can go for a safer approach
        reducing complexity instead of diffing the existing layers

        """
        self._traverseGlyphLayers(position="contextBefore", onlyAlignment=False)
        self._traverseGlyphLayers(position="contextCurrent", onlyAlignment=False)
        self._traverseGlyphLayers(position="contextAfter", onlyAlignment=False)


class FontListManager(Subscriber):
    """
    A subscriber following opened/closed fonts notifications

    """

    debug = DEBUG_MODE

    def fontDocumentDidOpen(self, info):
        font = info.get("font")
        if font:
            self.controller.fonts.append(font)
            postEvent(f"{DEFAULTKEY}.openedFontsDidChange")

    def fontDocumentWillClose(self, info):
        path = info["font"].path
        if path:
            self.removeFromFonts(path)
            postEvent(f"{DEFAULTKEY}.openedFontsDidChange")

    def removeFromFonts(self, path):
        for index, font in enumerate(self.controller.fonts):
            if font.path == path:
                del self.controller.fonts[index]


class OverlayUFOs(Subscriber, WindowController):

    debug = DEBUG_MODE

    def build(self):
        self.fonts = AllFonts()
        self.w = FloatingWindow((400, 200), "Overlay UFOs", minSize=(400, 200))
        self.populateWindow()
        self.w.open()

    def started(self):
        CurrentGlyphSubscriber.controller = self
        registerCurrentGlyphSubscriber(CurrentGlyphSubscriber)

        GlyphEditorSubscriber.controller = self
        registerGlyphEditorSubscriber(GlyphEditorSubscriber)

        FontListManager.controller = self
        registerRoboFontSubscriber(FontListManager)

    def destroy(self):
        CurrentGlyphSubscriber.controller = None
        unregisterCurrentGlyphSubscriber(CurrentGlyphSubscriber)

        GlyphEditorSubscriber.controller = None
        unregisterGlyphEditorSubscriber(GlyphEditorSubscriber)

        FontListManager.controller = None
        unregisterRoboFontSubscriber(FontListManager)

        if DEBUG_MODE:
            for eachFont in AllFonts():
                eachFont.close()

    def _getFontLabel(self, path):
        if path is None:
            return None
        if not path:
            return "Untitled"
        name = path.split("/")[-1]
        status = SELECTED_SYMBOL
        return status, path, name

    def _getFontLabels(self):
        labels = {}
        fontPaths = [f.path or f"{f.info.familyName} {f.info.styleName}" for f in self.fonts]
        for path in fontPaths:
            if path:
                label = self._getFontLabel(path)
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

    def openedFontsDidChange(self, info):
        self.w.fontList.set(self._getFontItems())

    def resetCallback(self, sender=None):
        """
        Resets the view to the currently opened fonts.

        """
        self.fonts = AllFonts()
        self.w.fontList.set(self._getFontItems())

    def addCallback(self, sender=None):
        """
        Open a font without UI and add it to the font list.

        """
        f = OpenFont(None, showInterface=False)
        if f is None:
            return
        self.fonts.append(f)
        self.w.fontList.set(self._getFontItems())

    def populateWindow(self):
        """
        The UI

        """
        self.fillColor = getExtensionDefault(DEFAULTKEY_FILLCOLOR, FALLBACK_FILLCOLOR)
        self.strokeColor = getExtensionDefault(DEFAULTKEY_STROKECOLOR, FALLBACK_STROKECOLOR)
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
            self._getFontItems(),
            selectionCallback=self.fontListCallback,
            drawFocusRing=False,
            enableDelete=False,
            allowsMultipleSelection=False,
            allowsEmptySelection=True,
            drawHorizontalLines=True,
            showColumnTitles=False,
            columnDescriptions=self._getPathListDescriptor(),
            rowHeight=16,
        )

        self.w.fill = CheckBox(
            (x, y, 60, 22),
            "Fill",
            sizeStyle=CONTROLS_SIZE_STYLE,
            value=True,
            callback=self.fillCallback,
        )
        y += L - 3
        self.w.stroke = CheckBox(
            (x, y, 60, 22),
            "Stroke",
            sizeStyle=CONTROLS_SIZE_STYLE,
            value=False,
            callback=self.strokeCallback,
        )
        y += L
        defaultColor = getExtensionDefault(DEFAULTKEY_FILLCOLOR, FALLBACK_FILLCOLOR)
        self.w.color = ColorWell(
            (x, y, 60, 22),
            color=NSColor.colorWithCalibratedRed_green_blue_alpha_(*defaultColor),
            callback=self.colorCallback,
        )
        y += LL + 5
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
            callback=self.viewCurrentCallback,
        )

        self.w.contextBefore = GlyphNamesEditText(
            (C2, -30, 85, 20),
            callback=self.contextEditCallback,
            continuous=True,
            sizeStyle="small",
            placeholder="Left Context",
        )
        self.w.contextBefore.title = "contextBefore"

        self.w.contextCurrent = GlyphNamesEditText(
            (C2 + 95, -30, 60, 20),
            callback=self.contextEditCallback,
            continuous=True,
            sizeStyle="small",
        )
        self.w.contextCurrent.title = "contextCurrent"

        self.w.contextAfter = GlyphNamesEditText(
            (C2 + 165, -30, 85, 20),
            callback=self.contextEditCallback,
            continuous=True,
            sizeStyle="small",
            placeholder="Right Context",
        )
        self.w.contextAfter.title = "contextAfter"

    def viewCurrentCallback(self, sender):
        postEvent(f"{DEFAULTKEY}.alwaysCurrentViewDidChange")

    def fontListCallback(self, sender):
        """
        If there is a selection, toggle the status of these fonts

        """
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
        postEvent(f"{DEFAULTKEY}.displayedFontsDidChange")

    def _getFontItems(self, update=False):
        """
        Get all fonts in a way that can be set into a vanilla list

        """
        itemsByName = {}
        if update:  # if update flag is set, then keep the existing selected fonts
            for item in self.w.fontList.get():
                if item["status"]:
                    itemsByName[item["name"]] = item
        currentStatuses = {}
        if hasattr(self.w, "fontList"):
            for d in self.w.fontList.get():
                currentStatuses[d["path"]] = d["status"]

        for status, path, uniqueName in self._getFontLabels():
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

    def _getPathListDescriptor(self):
        return [
            dict(title="Status", key="status", cell=SmallTextListCell(editable=False), width=12, editable=False),
            dict(title="Name", key="name", width=300, cell=SmallTextListCell(editable=False), editable=False),
            dict(title="Path", key="path", width=0, editable=False),
        ]

    def _setSourceFonts(self):
        """
        Set the font list from the current set of open fonts

        """
        labels = []
        currentSelection = []
        for d in self.w.fontList.get():
            if d["status"]:
                currentSelection.append(d["path"])
        for status, path, name in self.fontListManager.getFontLabels():
            if path in currentSelection:
                status = SELECTED_SYMBOL
            else:
                status = ""
            labels.append(dict(status=status, path=path, name=name))
        self.w.fontList.set(labels)

    def colorCallback(self, sender):
        """
        Change the color

        """
        r, g, b, a = NSColorToRgba(sender.get())
        self.fillColor = r, g, b, a
        self.strokeColor = r, g, b, 1
        setExtensionDefault(DEFAULTKEY_FILLCOLOR, (r, g, b, a))
        setExtensionDefault(DEFAULTKEY_STROKECOLOR, self.strokeColor)
        postEvent(f"{DEFAULTKEY}.colorDidChange")

    def fillCallback(self, sender):
        """
        Change the fill status

        """
        setExtensionDefault(DEFAULTKEY_FILL, sender.get())
        postEvent(f"{DEFAULTKEY}.fillCheckBoxDidChange")

    def strokeCallback(self, sender):
        """
        Change the stroke status

        """
        setExtensionDefault(DEFAULTKEY_STROKE, sender.get())
        postEvent(f"{DEFAULTKEY}.strokeCheckBoxDidChange")

    def alignCallback(self, sender):
        """
        Change the alignment status

        """
        postEvent(f"{DEFAULTKEY}.alignmentDidChange")

    def contextEditCallback(self, sender):
        postEvent(f"{DEFAULTKEY}.contextDidChange", position=sender.title)


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
