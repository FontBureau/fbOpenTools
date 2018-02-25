# a quick random word generator for typeface design class
"""
If you have a space center open, this will replace the text with a bunch of random words. Otherwise it will simply print to the output window!

I am not responsible for naughty or otherwise inappropriate words!

"""
import random
from vanilla import *
from mojo.UI import *

class RandomWordsWindow:
    def __init__(self):
        self.words = []
        self.charsInFont = []
        
        with open('/usr/share/dict/words', 'r') as wordsFile:
            wordsText = wordsFile.read()
            self.allWords = wordsText.split('\n')

        y = 10        
        self.w = Window((350, 100), 'Random Words')

        self.w.countText = TextBox((10, y, 100, 22), 'Word Count') 
        
        self.w.wordCount = Slider((100, y, -10, 22), value=10,
                                        maxValue=100,
                                        minValue=0,
                                        tickMarkCount = 10,
                                        #stopOnTickMarks = True,
                                        callback= self.set)
        
        #self.w.wordLength = TextBox((10, 40, 100, 22), 'Word Length') 
        #self.w.minWordLength = EditText((110, 40, 30, 22), "5", callback=self.makeWordsCallback) 
        #self.w.maxWordLength = EditText((150, 40, 30, 22), "12", callback=self.makeWordsCallback)
        y += 30
        self.w.capitalize = CheckBox((10, y, 100, 22), 'Capitalize', value=True, callback=self.set)
        self.w.allCaps = CheckBox((110, y, 100, 22), 'All Caps', value=False, callback=self.set)
        self.w.newWords = Button((200, y, -10, 22), 'New Words', callback=self.makeWordsCallback)

        y += 30
        self.w.charLimit = CheckBox((10, y, -10, 22), 'Limit to characters in font', value=False, callback=self.set)


        self.w.open()
        self.makeWordsCallback()
    
    def getCharsInFont(self, f):
        chars = []
        for g in f:
            if not g.template:
                for u in g.unicodes:
                    chars.append(unichr(u))
        return chars
    
    def addWord(self, min=0, max=100, charLimit=None):
        complete = False
        tick = 0
        while complete is not True:
            tick += 1
            word = random.choice(self.allWords)
            go = True
            if len(word) > min and len(word) < max:
                go = False
            #if self.w.charLimit.get() and charLimit:
            #    print 'analyzing charLimit', word, u''.join(charLimit)
            #    for c in word:
            #        if c not in charLimit:
            #            go = False
            #            print word, c
            #            break
            if go:    
                self.words.append(word)
                complete = True
            if tick > 500:
                complete = True

    def trimWords(self, count):
        self.words = self.words[:count-1]

    def makeWordsCallback(self, sender=None):
        self.words = []
        wordCount = 200
        
        # these are set explicitly! too much of a pain otherwise!
        wordLengthMin = 3  
        wordLengthMax = 12
        
        for x in range(0, wordCount):
            self.addWord(wordLengthMin, wordLengthMax)
        self.set()
    
    def set(self, sender=None):
        c = CurrentSpaceCenter()
        if c:
            charLimit = self.getCharsInFont(c.font)
        else:
            charLimit = None
        
        words = self.words[:int(self.w.wordCount.get())]
        if self.w.capitalize.get():
            words = [w.capitalize() for w in words]
        if self.w.allCaps.get():
            words = [w.upper() for w in words]
        if self.w.charLimit.get() and charLimit:
            for i, origWord in enumerate(words):
                newWord = []
                for char in origWord:
                    if char in charLimit:
                        newWord.append(char)
                words[i] = ''.join(newWord)
        try:
            c.setRaw(' '.join(words))
        except:
            print(' '.join(words))

RandomWordsWindow()