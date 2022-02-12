#!/usr/bin/env python3
"""
RA NOTES:
- switch to merz first
- then subscriber

"""

from defconAppKit.windows.baseWindow import BaseWindowController
from lib.tools.drawing import strokePixelPath
from mojo.drawingTools import scale, translate
from mojo.UI import splitText


class OverlayUFOs(BaseWindowController):
    def drawBackground(self, info):
        """Draw the background of defined glyphs and fonts.
        Scale is available as mouse.scale."""
        view = self.w
        if not view.viewEnabled.get():
            return

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
                contextBefore = splitText(contextBefore, font.getCharacterMapping(), font.groups)
                contextBefore = [font[gname] for gname in contextBefore if gname in font.keys()]
                contextAfter = splitText(contextAfter, font.getCharacterMapping(), font.groups)
                contextAfter = [font[gname] for gname in contextAfter if gname in font.keys()]
                contextCurrent = splitText(contextCurrent, font.getCharacterMapping(), font.groups)
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
                        kernValue += 0

                    translate(-cbGlyph.width - kernValue, 0)
                    totalWidth += cbGlyph.width + kernValue
                    drawGlyphPath = cbGlyph.getRepresentation("defconAppKit.NSBezierPath")
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
                        drawGlyphPath = cbGlyph.getRepresentation("defconAppKit.NSBezierPath")
                        if view.fill.get():
                            drawGlyphPath.fill()
                        if view.stroke.get():
                            strokePixelPath(drawGlyphPath)
                    kernValue = 0

                    if cbGlyph is not None and nextGlyph is not None and nextGlyph.font == cbGlyph.font:
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


if __name__ == "__main__":
    OverlayUFOs()
