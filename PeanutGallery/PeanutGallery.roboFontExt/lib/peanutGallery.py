#coding=utf-8
from mojo.events import BaseEventTool, installTool
from collections import OrderedDict
from AppKit import *
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.drawingTools import *
from mojo.extensions import ExtensionBundle
from vanilla import *
from mojo.UI import UpdateCurrentGlyphView, setGlyphViewDisplaySettings, getGlyphViewDisplaySettings, CurrentGlyphWindow
from roboflightlib.toolbox.storage.state import State
from roboflightlib.toolbox import TX


COMMENT_LIB_KEY = 'com.fontbureau.comments'
COMMENT_TYPE_ICONS = {
                      
                'comment': u'💬',
                #'moveLeft': u'◀',
                #'moveRight': u'▶',
                #'moveUp': u'▲',
                #'moveDown': u'▼',
                'moveLeft': u'←',
                'moveRight': u'→',
                'moveUp': u'↑',
                'moveDown': u'↓',
                'moveUpLeft': u'↖',
                'moveUpRight': u'↗',
                'moveDownLeft': u'↙',
                'moveDownRight': u'↘',
                'round': u'◯',
                'add': u'╋',
                'subtract': u'━',
                'happy': u'😀',
                'surprise': u'😮',
                'cyclone': u'🌀',
                'saltire': u'☓',
                }

COMMENT_TYPE_ORDER_1 = ['moveUpLeft', 'moveUp',  'moveUpRight', 'add', 'happy',
                        'moveLeft', 'comment', 'moveRight', 'subtract', 'surprise',
                        'moveDownLeft', 'moveDown', 'moveDownRight', 'saltire', 'cyclone']

from roboflightlib.toolbox import CharacterTX
import unicodedata

try:
    bundle = ExtensionBundle("PeanutGallery")
    toolbarIcon = bundle.getResourceImage("peanutGallery")
    toolbarIcon.setSize_((16, 16))
except:
    pass


class Comment(OrderedDict):
    pass        
    
class Commentary(OrderedDict):
    pass


class CommentDialog(BaseWindowController):
    
    COMMENT_LIB_KEY = COMMENT_LIB_KEY
    COMMENT_TYPE_ORDER = COMMENT_TYPE_ORDER_1
    COMMENT_TYPE_ORDER_1 = COMMENT_TYPE_ORDER_1
    COMMENT_TYPE_ICONS = COMMENT_TYPE_ICONS

        
    def __init__(self, parent, commentInfo={}, edit=False):
        self.parent = parent
        self.original = commentInfo
        self.commentInfo = commentInfo
        
        # title
        if edit:
            title = 'Edit Comment'
            buttonTitle = u'Edit →'
        else:
            title = 'Add Comment'
            buttonTitle = u'Add →'
        self.w = Window((400, 110), title, closable=True)
        yoffset = 10
        lineHeight = 22
        itemHeight = 22
        
        # text
        self.w.commentText = EditText((10, yoffset, -10, itemHeight), commentInfo.get('commentText') or '')
        yoffset += lineHeight
    
        # type
        commentType = 'comment'
        if commentInfo.has_key('commentType'):
            commentType = commentInfo.get('commentType')
        if commentType in self.COMMENT_TYPE_ICONS:
            currentIcon = self.COMMENT_TYPE_ICONS[commentType]
        else:
            currentIcon = self.parent.getIcon()
        self.w.commentTypePreview = TextBox((10, yoffset+5, 35, itemHeight), currentIcon)
        xoffset = 35
        for i, buildType in enumerate(self.COMMENT_TYPE_ORDER_1):
            icon = self.COMMENT_TYPE_ICONS[buildType]
            setattr(self.w, buildType+'Button', Button((xoffset, yoffset, 35, itemHeight), icon, callback=self.commentTypeCallback, sizeStyle="mini"))
            xoffset += 35
            if (i+1)/5 == int((i+1)/5):
                xoffset = 35
                yoffset += lineHeight
        yoffset -= lineHeight * 3
        
        # buttons
        self.w.ok = Button((-100, yoffset, -10, 20), buttonTitle, callback=self.okCallback, sizeStyle='mini')
        yoffset += lineHeight * 2
        self.w.ok.bind("rightarrow", [])
        if edit:
            self.w.delete = Button((-100, yoffset, -10, 20), 'Delete', callback=self.deleteCallback, sizeStyle='mini')
        else:
            self.w.clear = Button((-100, yoffset, -10, 20), 'Clear', callback=self.clearCallback, sizeStyle='mini')
        self.w.open()
        self.setUpBaseWindowBehavior()
    
    def commentTypeCallback(self, sender):
        for i, buildType in enumerate(self.COMMENT_TYPE_ORDER_1):
            icon = self.COMMENT_TYPE_ICONS[buildType]
            if getattr(self.w, buildType+'Button') == sender:
                self.commentInfo['commentType'] = buildType
                self.w.commentTypePreview.set(icon)
    
    def okCallback(self, sender):
        commentInfo = Comment()
        commentInfo['coords'] = self.commentInfo['coords']
        commentText = self.w.commentText.get()
        if commentText:
            commentInfo['commentText'] = commentText
        commentType = self.commentInfo.get('commentType') or 'comment'
        if commentType:
            commentInfo['commentType'] = commentType
        self.parent.addComment(commentInfo)
        self.w.close()
       
    def deleteCallback(self, sender):
        commentInfo = self.commentInfo
        id = self.parent.getID(commentInfo.get('coords'))
        self.parent.removeComment(id)
        if sender:
            self.w.close()
        
    def clearCallback(self, sender):
        self.parent.clearComments()
        if sender:
            self.w.close()

class PeanutGallery(BaseEventTool):
    u"""
    Shows the bounding box and useful divisions.
    """
    
    COMMENT_LIB_KEY = COMMENT_LIB_KEY
    COMMENT_TYPE_ICONS = COMMENT_TYPE_ICONS
    

    xBufferLeft = 20
    xBufferRight = 20
    yBufferTop = 20
    yBufferBottom = 20
    
    def getCurrentFont(self):
        if hasattr(self, 'f'):
            return self.f
        else:
            return CurrentFont()
    
    def setCurrentFont(self, f):
        self.f = f
        
    def prepareUndo(self, g=None):
        if g is None:
            g = self.getGlyph()
        try:
            g.prepareUndo()
        except:
            pass
            
    def performUndo(self, g=None):
        if g is None:
            g = self.getGlyph()
        try:
            g.performUndo()
        except:
            pass  

    def readComments(self, g=None):
        if g is None:
            g = self.getGlyph()
        if g is not None and g.lib.has_key(self.COMMENT_LIB_KEY):
            return Commentary(g.lib[self.COMMENT_LIB_KEY])
        else:
            return Commentary()
    
    def writeComments(self, g=None):
        if g is None:
            g = self.getGlyph()
        if g is not None:
            comments = self.getComments()
            g.lib[self.COMMENT_LIB_KEY] = comments
        
    def setComments(self, comments):
        self.comments = comments
        self.writeComments()
        #self.setFontComments()
        self.updateView()
    
    def setComment(self, commentKey, commentValue):
        self.getComments()[commentKey] = commentValue
        self.writeComments()
        #self.setFontComments()
        self.updateView()
        
    def addComment(self, commentInfo):
        self.prepareUndo()
        comment = Comment(commentInfo)
        self.getComments()[self.getID(commentInfo['coords'])] = comment
        self.writeComments()
        #self.setFontComments()
        self.updateView()
        self.performUndo()
        
    def clearComments(self):
        self.prepareUndo()
        self.setComments(Commentary())
        self.writeComments()
        #self.setFontComments()
        self.updateView()
        self.performUndo()
        
    def removeComment(self, commentKey):
        self.prepareUndo()
        if self.getComments().has_key(commentKey):
            del self.getComments()[commentKey]
        self.writeComments()
        #self.setFontComments()
        self.updateView()
        self.performUndo()
    
    def getComments(self):
        if not hasattr(self, 'comments'):
            self.comments = Commentary()
        return self.comments

    def getIcon(self, commentType=None):
        if self.COMMENT_TYPE_ICONS.has_key(commentType):
            return self.COMMENT_TYPE_ICONS[commentType]
        else:
            return u'💬'
            
    def getNameForIcon(self, icon=""):
        map = TX.reverseDict(COMMENT_TYPE_ICONS)
        if map.has_key(icon):
            return map[icon]

    def getID(self, coords):
        x, y = coords
        return '%s,%s' %(int(x), int(y))

    def getSelectedComments(self):
        if hasattr(self, 'selectedComments'):
            return self.selectedComments
        else:
            return []

    def readFontComments(self, f=None):
        if f is None:
            g = self.getGlyph()
            if g is None:
                f = CurrentFont()
            else:
                f = g.getParent()
        self.setCurrentFont(f)
        allComments = []
        for gname in f.glyphOrder:
            if f.has_key(gname):
                g = f[gname]
                comments = self.readComments(g)
                if comments:
                    for commentID, comment in comments.items():
                        coords = comment.get('coords')
                        x, y = coords
                        x = int(round(x))
                        y = int(round(y))
                        c = {
                             'Coords': coords,
                             'ID': commentID,
                             'Glyph': g.name, 
                             'Type': self.getIcon(comment.get('commentType')), 
                             'Text': comment.get('commentText') or '', 
                             'Done': comment.get('done') or False,
                             }
                        allComments.append(c)
        return allComments
        
    def setFontComments(self):
        if hasattr(self, 'w'):
            allComments = self.readFontComments()
            self.w.fontCommentsList.set(allComments)
        else:
            print 'no window to set'

    def refreshFontComments(self, sender):
        self.setFontComments()

    # ACTIVITY

    def becomeActive(self):
        #print 'becoming active'
        # read the comments into the tool    
        self.setComments(self.readComments())
        # do custom display settings
        self.originalDisplaySettings = getGlyphViewDisplaySettings()
        self.setCustomViewSettings()
        self.windowSelection = []
        fontComments = self.readFontComments()
        self.w = Window( (300, 500), 'Commentary', minSize=(200, 400), closable=True )
        self.w.fontCommentsList = List((10, 10, -10, -40),
                             fontComments,
                             columnDescriptions=[
                                                 {"title": "Glyph", "width": 60, 'editable': False}, 
                                                 {"title": "Type", "width": 40, 'editable': False}, 
                                                 {"title": "Text", 'editable': True, "width": 130},
                                                 {"title": "Done", 'cell': CheckBoxListCell(), "width": 40},

                                                 {"title": "Coords", "width": 0, 'editable': False}, 
                                                 {"title": "ID", "width": 0, 'editable': False}
                                                 ],
                             selectionCallback=self.selectionCallback,
                             allowsMultipleSelection=False,
                             editCallback=self.editCallback,
                             #dragSettings=dict(type="smartListPboardType", callback=self.dragCallback),
                             enableDelete=True
                             )
        self.w.goButton = Button((10, -30, 30, -10), unichr(8634), self.refreshFontComments)
        
        #'moveLeft': u'←',
        #'moveRight': u'→',
        
        self.w.previous = Button((-80, -30, 35, -10), u'←', self.goToPrevious)
        self.w.next = Button((-40, -30, 35, -10), u'→', self.goToNext)
        
        self.w.toggle = Button((-160, -30, 35, -10), u'👀', self.toggleView)
        
        self.w.open()

    def becomeInactive(self):
        """
        
        """
        self.setOriginalViewSettings()
        # close any open dialogs
        if hasattr(self, 'openDialog'):
            try:
                self.openDialog.w.close()
            except:
                pass
        try:
            self.w.close()
        except:
            pass

    def setOriginalViewSettings(self, sender=None):
        # return display settings to how they were
        setGlyphViewDisplaySettings(self.originalDisplaySettings)
        self.viewMode = 'original'

    def setCustomViewSettings(self, sender=None):
        settings = {u'Component Indexes': False, 
                    u'Component info': False, 
                    u'Anchors': False, 
                    u'Point Indexes': False, 
                    u'Labels': False, 
                    u'Blues': False, 
                    u'Bitmap': False, 
                    u'Metrics': True, 
                    u'Rulers': True, 
                    u'Stroke': False, 
                    u'Family Blues': False, 
                    u'Grid': False, 
                    u'Point Coordinates': False, 
                    u'Anchor Indexes': False, 
                    u'Outline Errors': 0L, 
                    u'Off Curve Points': False, 
                    u'On Curve Points': False, 
                    u'Contour Indexes': False, 
                    u'Curve Length': False, 
                    u'Fill': True,
                    }
        setGlyphViewDisplaySettings(settings)
        self.viewMode = 'custom'
        
    def toggleView(self, sender=None):
        if self.viewMode == 'custom':
            self.setOriginalViewSettings()
        else:
            self.setCustomViewSettings()

    def selectionCallback(self, sender):
        self.changeCommentCallback(sender)
    
    def editCallback(self, sender):
        commentDicts = sender.get()
        selection = sender.getSelection()
        if selection:
            commentDict = commentDicts[selection[0]]
            comment = {}
            id = commentDict['ID']
            comment['coords'] = commentDict['Coords']
            comment['commentText'] = commentDict['Text']            
            comment['commentType'] = self.getNameForIcon(commentDict['Type'])
            comment['done'] = commentDict['Done']
            self.addComment(comment)
        
    def goToNext(self, sender):
        selection = self.w.fontCommentsList.getSelection()
        if selection:
            selection = selection[0]
            if selection < len(self.w.fontCommentsList):
                self.w.fontCommentsList.setSelection([selection+1])
            #else:
            #    self.w.fontCommentsList.setSelection([0])
        self.changeCommentCallback(sender)
        
    def goToPrevious(self, sender):
        selection = self.w.fontCommentsList.getSelection()
        if selection:
            selection = selection[0]
            if selection > 0:
                self.w.fontCommentsList.setSelection([selection-1])
            #else:
            #    self.w.fontCommentsList.setSelection([len(self.w.fontCommentsList)-1])
        self.changeCommentCallback(sender)
             
    def changeCommentCallback(self, sender):
        selection = self.w.fontCommentsList.getSelection()
        commentDicts = self.w.fontCommentsList.get()
        if selection:
            commentDict = commentDicts[selection[0]]
            if hasattr(self, 'f') and self.f.has_key(commentDict['Glyph']):
                CurrentGlyphWindow().setGlyph(self.f[commentDict['Glyph']].naked()) 
                self.selectedComments = [commentDict['ID']]

    def getToolbarTip(self):
        return "Peanut Gallery"
        
    def getToolbarIcon(self):
        return toolbarIcon
    
    def mouseMoved(self, point):
        self.coords = point.x, point.y

    def getMouseCoords(self):
        if hasattr(self, 'coords'):
            return self.coords
        else:
            return (0, 0)

    def closeOpenDialogs(self):
        if hasattr(self, 'openDialogs'):
            for dialog in openDialogs:
                dialog.close()

    def getSelected(self, coords):

        coords = self.getMouseCoords()
        for commentIDs, commentInfo in self.getComments().items():
            commentCoords = commentInfo.get('coords') or (0, 0)
            xmin = commentCoords[0] - self.xBufferLeft
            ymin = commentCoords[1] - self.yBufferBottom
            xmax = commentCoords[0] + self.xBufferRight
            ymax = commentCoords[1] + self.yBufferTop
            if xmin <= coords[0] <= xmax and ymin <= coords[1] <= ymax:
                return commentInfo
    
    def mouseDown(self, point, clickCount):
        if hasattr(self, 'openDialog'):
            try:
                self.openDialog.w.close()
            except:
                pass
        coords = self.getMouseCoords()
        self.dragSelected = self.getSelected(coords)
        if clickCount == 2:
            selected = self.getSelected(coords)
            if selected:
                self.openDialog = CommentDialog(self, selected, edit=True)
            else:
                commentInfo = Comment(coords=coords)
                self.openDialog = CommentDialog(self, commentInfo)
    
    def mouseDragged(self, point, delta):
        if self.dragSelected:
            commentInfo = self.dragSelected

            commentCoords = commentInfo.get('coords')
            commentID = self.getID(commentCoords)
            newCoordX = point.x + delta.x/2.0
            newCoordY = point.y + delta.y/2.0
            newCoords = newCoordX, newCoordY
            # remove the entry, and replace it
            if self.getComments().has_key(commentID):
                self.removeComment(commentID)
                commentInfo['coords'] = newCoords
                self.addComment(commentInfo)
                self.dragSelected = commentInfo
            
    def keyUp(self, event):
        char = event.charactersIgnoringModifiers()        
        commentType = None
        #char == unichr(63232) or 
        if char == 'W':
            commentType = 'moveUp'
        # char == unichr(63233)
        elif char == 'X':
            commentType = 'moveDown'
        # char == unichr(63234) or
        elif char == 'A':
            commentType = 'moveLeft'
        #char == unichr(63235) or
        elif char == 'D':
            commentType = 'moveRight'
        elif char == 'Q':
            commentType = 'moveUpLeft'
        elif char == 'E':
            commentType = 'moveUpRight'
        elif char == 'Z':
            commentType = 'moveDownLeft'
        elif char == 'C':
            commentType = 'moveDownRight'
        elif char == 'S':
            commentType = 'comment'
        elif char == '!':
            commentType = 'subtract'
        elif char == '@':
            commentType = 'add'

        if commentType:
            self.addComment({'commentType': commentType, 'coords': self.getMouseCoords()})
    
    
    def viewDidChangeGlyph(self):
        self.setComments(self.readComments())
        
    def updateView(self):
        #print 'updating view'
        #self.setFontComments()
        UpdateCurrentGlyphView()
    
    def draw(self, scaleValue):
        
        iconSize = 30
        
        commentBoxes = []
        for commentID, commentInfo in self.getComments().items():
            commentCoords = commentInfo.get('coords') or (0, 0)

            commentType = commentInfo.get('commentType')
            if self.COMMENT_TYPE_ICONS.has_key(commentType):
                icon = self.COMMENT_TYPE_ICONS[commentType]
            else:
                icon = self.COMMENT_TYPE_ICONS['comment']
            commentText = commentInfo.get('commentText') or ''
            drawCoordsX, drawCoordsY = commentCoords

            if commentInfo.get("done"):
                fillr, fillg, fillb = (.5, .5, 1)
            else:
                fillr, fillg, fillb = (1, .5, .5)
            
            if commentID in self.getSelectedComments():
                fill(fillr, fillg, fillb, .5)
                rect(drawCoordsX-iconSize/2, drawCoordsY-10, iconSize, iconSize)


            fill(fillr, fillg, fillb, 1)
                
            strokeWidth(0)
            stroke()
            font('LucidaGrande')
            fontSize(iconSize)        
            
            text(icon, (drawCoordsX-iconSize/2, drawCoordsY-iconSize/2 ) )
            #fill(1, 0, 0, 1)
            #oval(drawCoordsX-4, drawCoordsY-4, 8, 8)

            fontSize(10*scaleValue)
            
            text(commentText, (drawCoordsX+17, drawCoordsY+0))
            
    
    def drawInactive(self, scaleValue, glyph, view):
        self.draw(scaleValue)
    
installTool(PeanutGallery())