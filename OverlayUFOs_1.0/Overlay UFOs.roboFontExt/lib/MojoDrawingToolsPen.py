from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from mojo.drawingTools import newPath, moveTo, lineTo, curveTo, closePath, drawPath

class MojoDrawingToolsPen(BasePen):
    def __init__(self, g, f):
        BasePen.__init__(self, None)
        self.g = g
        self.glyphSet = f
        self.__currentPoint = None
        newPath()
    
    def _moveTo(self, pt):
        moveTo(pt)
    
    def _lineTo(self, pt):
        lineTo(pt)
    
    def _curveToOne(self, pt1, pt2, pt3):
        curveTo(pt1, pt2, pt3)
    
    def _closePath(self):
        closePath()
    
    def _endPath(self):
        closePath()
    
    def draw(self):
        drawPath()
    
    def addComponent(self, baseName, transformation):
        try:
            glyph = self.glyphSet[baseName]
            tPen = TransformPen(self, transformation)
            glyph.draw(tPen)
        except:
            pass
