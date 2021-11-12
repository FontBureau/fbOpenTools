#!/usr/bin/env python3

# ------------------- #
# Italic Math + Tools #
# ------------------- #

# -- Modules -- #
import math
from fontTools.misc.transform import Identity

# -- Functions -- #
# math
def calcItalicOffset(yoffset, italicAngle):
    '''
    Given a y offset and an italic angle, calculate the x offset.
    '''
    from math import radians, tan
    ritalicAngle = radians(italicAngle)
    xoffset = int(round(tan(ritalicAngle) * yoffset))
    return xoffset*-1

def calcItalicRise(xoffset, italicAngle):
    '''
    Given a x offset and an italic angle, calculate the y offset.
    '''
    from math import radians, tan
    if italicAngle == 0:
        return 0
    ritalicAngle = radians(italicAngle)
    yoffset = int(round(float(xoffset) / tan(ritalicAngle)))
    return yoffset

def calcItalicCoordinates(coords, italicAngle):
    """
    Given (x, y) coords and an italic angle, get new coordinates accounting for italic offset.
    """
    x, y = coords
    x += calcItalicOffset(y, italicAngle)
    return x, y

# tools
def calcItalicSlantOffset(italicAngle=0, crossHeight=0):
    """
    Get italic slant offset.
    """
    return calcItalicOffset(-crossHeight, italicAngle)

def calcCrossHeight(italicAngle=0, italicSlantOffset=0):
    return calcItalicRise(italicSlantOffset, italicAngle)

def makeReferenceLayer(source, italicAngle, backgroundName='com.fontbureau.italicReference'):
    """
    Store a vertically skewed copy in the mask.
    """
    italicSlant = abs(italicAngle)
    g = source.getLayer(backgroundName)
    g.decompose()
    source.copyToLayer(backgroundName)
    # use for vertical offset later
    top1 = g.bounds[3]
    bottom1 = g.bounds[1]
    height1 = top1 + abs(bottom1)
    # vertical skew
    m = Identity
    dx = 0
    dy = italicSlant/2.0   # half the italic angle
    x = math.radians(dx)
    y = math.radians(dy)
    m = m.skew(x, -y)
    g.transform(m)
    top2 = g.bounds[3]
    bottom2 = g.bounds[1]
    height2 = top2 + abs(bottom2)
    dif = (height1-height2) / 2
    yoffset = (abs(bottom2)-abs(bottom1)) + dif
    g.moveBy((0, yoffset))

def italicize(glyph,
              italicAngle=None,
              offset=0,
              doContours = True,
              doAnchors = True,
              doGuides = True,
              doComponents = True,
              doImage = True,
              shouldMakeReferenceLayer=True,
              DEBUG=False):
    """
    Oblique a glyph using cap height and italic angle.
    """
    with glyph.undo("italicBowtie"):
        xoffset = offset
        # skew the glyph horizontally
        glyph.skew(-italicAngle, (0, 0))
        if doContours:
            for c in glyph.contours:
                c.moveBy((xoffset, 0))
                if DEBUG:
                    print(f'\t\t\t {c}')
        # anchors
        if doAnchors:
            for anchor in glyph.anchors:
                anchor.moveBy((xoffset, 0))
                if DEBUG:
                    print(f'\t\t\t {anchor}')
        # guides
        if doGuides:
            for guide in glyph.guides:
                guide.x += xoffset
                if DEBUG:
                    print(f'\t\t\t {guide} {guide.x}')
                # image
                if doImage:
                    if glyph.image:
                        glyph.image.moveBy((xoffset, 0))
                        if DEBUG:
                            print(f'\t\t\t {glyph.image}')
        if doComponents:
            for c in glyph.components:
                cxoffset = calcItalicOffset(c.offset[1], italicAngle)
                c.offset = (c.offset[0]-cxoffset, c.offset[1])

        if not glyph.components and shouldMakeReferenceLayer:
            makeReferenceLayer(glyph, italicAngle)
        glyph.markColor = (0, .1, 1, .2)
