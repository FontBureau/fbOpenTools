from mojo.UI import CurrentGlyphWindow
from merz import MerzView
import unicodedata

from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber
from vanilla import FloatingWindow, TextBox

class ShowCharacterInfo(Subscriber):

    debug = False

    def build(self):
        glyphEditor = self.getGlyphEditor()
        self.container = glyphEditor.extensionContainer(
            identifier="com.fontbureau.showCharacterInfo",
            location="foreground",
            clear=True
        )

    def glyphEditorDidSetGlyph(self, info):
        # redraw the label every time we change the glyph
        container = self.container
        
        # make the text box
        textBoxLayer = container.appendTextBoxSublayer(
           size=(2000, 100),
           backgroundColor=None,
           fillColor=(0, 0, 0, 1)
        )
        textBoxLayer.setFont("system")
        textBoxLayer.setPointSize(13)
        textBoxLayer.setPosition((0, 0))
        textBoxLayer.setPadding((10, 10))


        # get the label string from the glyph in question
        s = '' # the string to fill
        g = info['glyph']

        # split glyph name into basename and suffixes
        nameParts = g.name.split('.')
        baseName = nameParts[0]
        suffixes = nameParts[1:]

        # decimal
        dec = None

        # try to get a unicode value from this glyph or the basename glyph
        try:
            dec = g.unicodes[0]
        except:
            srcg = None
            if baseName in g.getParent():
                srcg = g.getParent()[baseName]
            if srcg:
                try:
                    dec = srcg.unicodes[0]
                except:
                    pass
        
        # if there’s a unicode, parse and display it
        if dec:
            unistr = f"{dec:04}"
            s = chr(dec) + ' | ' + 'U+' + str(unistr)
    
            try:
                s += ' | ' + unicodedata.name(chr(dec))
            except:
                pass
        else:
            s = 'UNENCODED'

        # if there are suffixes, include those too
        if suffixes:
            s += ' | ' + ', '.join(suffixes)

        # set the text 
        textBoxLayer.setText(s)


if __name__ == '__main__':
    registerGlyphEditorSubscriber(ShowCharacterInfo)
