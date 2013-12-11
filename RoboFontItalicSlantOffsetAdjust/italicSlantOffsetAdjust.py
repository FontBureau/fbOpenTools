#coding=utf-8
### Italic Slant Offset Adjust
"""
Takes all open fonts that have been skewed from the baseline, and offsets them by the Italic Slant Offset value accessible in Font Info > RoboFont. Offsets contours, anchors, guides, and the image for foreground layer and all other layers.
"""

# override the italic slant offset that exists in the fonts?
italicSlantOffsetOverride = None
# Print every object that is offset?
DEBUG = False

def offsetGlyph(g, xoffset, doContours=True, doAnchors=True, doGuides=True, doImage=True, DEBUG=DEBUG):
    """
    Offsets one glyph.
    """
    # contours
    g.prepareUndo()
    if doContours:
        for c in g.contours:
            c.move((xoffset, 0))
            if DEBUG: print '\t\t\t', c
    # anchors
    if doAnchors:
        for anchor in g.anchors:
            anchor.move((xoffset, 0))
            if DEBUG: print '\t\t\t', anchor
    # guides
    if doGuides:
        for guide in g.guides:
            guide.x += xoffset
            if DEBUG: print '\t\t\t', guide, guide.x
    # image
    if doImage:
        if g.image:
            g.image.move((xoffset, 0))
            if DEBUG: print '\t\t\t', image 
    g.performUndo() 

#process all font
fonts = AllFonts()
for f in fonts:
    xoffset = f.lib.get("com.typemytype.robofont.italicSlantOffset", 0)
    if italicSlantOffsetOverride:
        xoffset = italicSlantOffsetOverride
    if xoffset:
        print f, 'offset', xoffset, 'units'
        for g in f:
            if DEBUG: print '\t', g
            # offset glyph
            offsetGlyph(g, xoffset)
            # offset other layers of glyph
            for layerName in f.layerOrder:
                layer = g.getLayer(layerName)
                if DEBUG: print '\t\t', layer
                # apparently the guides are layer independent. don’t shift them twice!
                offsetGlyph(layer, xoffset, doGuides=False)
print 'done'
        