#!/usr/bin/env python
# 
#  * boilerpipe
#  *
#  * Copyright (c) 2009 Christian Kohlschtter
#  *
#  * The author licenses this file to You under the Apache License, Version 2.0
#  * (the "License"); you may not use this file except in compliance with
#  * the License.  You may obtain a copy of the License at
#  *
#  *	 http://www.apache.org/licenses/LICENSE-2.0
#  *
#  * Unless required by applicable law or agreed to in writing, software
#  * distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.
#  

from HTMLParser import HTMLParser
from xml.sax import ContentHandler
from . import document
from document import DefaultLabels
import re



#----------------------------------------------------------------------------
#                                TAG ACTIONS
#----------------------------------------------------------------------------


class TagAction(object):
	def start(self, contentHandler, tagName, attrs): return False
	def end(self, contentHandler, tagName): return False
	def changesTagLevel(self): return False

# 
#  * Marks this tag as "ignorable", i.e. all its inner content is silently skipped.
#  
class IgnorableElementTagAction(TagAction):
	""" generated source for class TA_IGNORABLE_ELEMENT """
	def start(self, contentHandler, tagName, attrs):
		contentHandler.inIgnorableElement += 1
		return True

	def end(self, contentHandler, tagName):
		contentHandler.inIgnorableElement -= 1
		return True

	def changesTagLevel(self):
		return True

# 
#  * Marks this tag as "anchor" (this should usually only be set for the <code>&lt;A&gt;</code> tag).
#  * Anchor tags may not be nested.
#  *
#  * There is a bug in certain versions of NekoHTML which still allows nested tags.
#  * If boilerpipe encounters such nestings, a SAXException is thrown.
#  
class AnchorTextTagAction(TagAction):
	""" generated source for class TA_ANCHOR_TEXT """
	def start(self, contentHandler, tagName, attrs):
		contentHandler.inAnchor += 1
		if contentHandler.inAnchor > 1:
			#  as nested A elements are not allowed per specification, we
			#  are probably reaching this branch due to a bug in the XML
			#  parser
			print("Warning: SAX input contains nested A elements -- You have probably hit a bug in your HTML parser (e.g., NekoHTML bug #2909310). Please clean the HTML externally and feed it to boilerpipe again. Trying to recover somehow...")
			self.end(contentHandler, tagName)
		if contentHandler.inIgnorableElement == 0:
			contentHandler.addToken(SpecialTokens.ANCHOR_TEXT_START)
		return False

	def end(self, contentHandler, tagName):
		contentHandler.inAnchor -= 1
		if contentHandler.inAnchor == 0 and contentHandler.inIgnorableElement == 0:
			contentHandler.addToken(SpecialTokens.ANCHOR_TEXT_END)
		return False

	def changesTagLevel(self):
		return True

# 
#  * Marks this tag the body element (this should usually only be set for the <code>&lt;BODY&gt;</code> tag).
#  
class BodyTagAction(TagAction):
	""" generated source for class TA_BODY """
	def start(self, contentHandler, tagName, attrs):
		contentHandler.flushBlock()
		contentHandler.inBody += 1
		return False

	def end(self, contentHandler, tagName):
		contentHandler.flushBlock()
		contentHandler.inBody -= 1
		return False

	def changesTagLevel(self):
		return True

# 
#  * Marks this tag a simple "inline" element, which generates whitespace, but no new block.
#  
class InlineWhitespaceTagAction(TagAction):
	""" generated source for class TA_INLINE_WHITESPACE """
	def start(self, contentHandler, tagName, attrs):
		contentHandler.addWhitespaceIfNecessary()
		return False

	def end(self, contentHandler, tagName):
		contentHandler.addWhitespaceIfNecessary()
		return False

	def changesTagLevel(self): return False

# 
#  * Marks this tag a simple "inline" element, which neither generates whitespace, nor a new block.
#  
class InlineTagAction(TagAction):
	""" generated source for class TA_INLINE_NO_WHITESPACE """
	def start(self, contentHandler, tagName, attrs): return False
	def end(self, contentHandler, tagName): return False
	def changesTagLevel(self): return False

# 
#  * Explicitly marks this tag a simple "block-level" element, which always generates whitespace
#  
class BlockTagAction(TagAction):
	""" generated source for class TA_BLOCK_LEVEL """
	def start(self, contentHandler, tagName, attrs): return True
	def end(self, contentHandler, tagName): return True
	def changesTagLevel(self): return True

# 
#  * Special TagAction for the <code>&lt;FONT&gt;</code> tag, which keeps track of the
#  * absolute and relative font size.
#  
class FontTagAction(TagAction):
	""" generated source for class TA_FONT """
	#WARNING: POSSIBLE BUG -- used to be [0-9] without +
	PAT_FONT_SIZE = re.compile("([\+\-]?)([0-9]+)")

	def start(self, contentHandler, tagName, attrs):
		""" generated source for method start """
		sizeAttr = attrs.getValue("size")
		size=None
		if sizeAttr != None:
			match=PAT_FONT_SIZE.match(sizeAttr)
			if match!=None:
				rel=match.group(0)
				val=match.group(1)
				if len(rel)==0:
					#  absolute
					size = val
				else:
					#  relative
					#last non-none element from stack, default 3
					lastNonNone=(s for s in contentHandler.fontSizeStack[::-1] if s!=None)
					prevSize=next(lastNonNone,3)
					if rel[0] == '+': size = prevSize + val
					else: size = prevSize - val
		contentHandler.fontSizeStack.append(size)
		return False

	def end(self, contentHandler, tagName):
		contentHandler.fontSizeStack.pop()
		return False

	def changesTagLevel(self): return False

# 
#  * {@link CommonTagActions} for inline elements, which triggers some {@link LabelAction} on the generated
#  * {@link TextBlock}.
#  
class InlineTagLabelAction(TagAction):
	""" generated source for class InlineTagLabelAction """

	def __init__(self, action):
		""" generated source for method __init__ """
		super(InlineTagLabelAction, self).__init__()
		self.action = action

	def start(self, contentHandler, tagName, attrs):
		""" generated source for method start """
		contentHandler.addWhitespaceIfNecessary()
		contentHandler.addLabelAction(self.action)
		return False

	def end(self, contentHandler, tagName):
		""" generated source for method end """
		contentHandler.addWhitespaceIfNecessary()
		return False

	def changesTagLevel(self):
		""" generated source for method changesTagLevel """
		return False

# 
#  * {@link CommonTagActions} for block-level elements, which triggers some {@link LabelAction} on the generated
#  * {@link TextBlock}.
#  
class BlockTagLabelAction(TagAction):
	""" generated source for class BlockTagLabelAction """

	def __init__(self, action):
		""" generated source for method __init__ """
		super(BlockTagLabelAction, self).__init__()
		self.action = action

	def start(self, contentHandler, tagName, attrs):
		""" generated source for method start """
		contentHandler.addLabelAction(self.action)
		return True

	def end(self, contentHandler, tagName):
		""" generated source for method end """
		return True

	def changesTagLevel(self):
		""" generated source for method changesTagLevel """
		return True


class Chained(TagAction):

	def __init__(self, tagAction1, tagAction2):
		""" generated source for method __init__ """
		super(Chained, self).__init__()
		self.tagAction1 = tagAction1
		self.tagAction2 = tagAction2

	def start(self, contentHandler, tagName, attrs):
		""" generated source for method start """
		return self.tagAction1.start(contentHandler, tagName, attrs) | self.tagAction2.start(contentHandler, tagName, attrs)

	def end(self, contentHandler, tagName):
		""" generated source for method end """
		return self.tagAction1.end(contentHandler, tagName) | self.tagAction2.end(contentHandler, tagName)

	def changesTagLevel(self):
		""" generated source for method changesTagLevel """
		return self.tagAction1.changesTagLevel() or self.tagAction2.changesTagLevel()


class MarkupTagAction(TagAction):
	""" generated source for class MarkupTagAction """

	def __init__(self, isBlockLevel):
		""" generated source for method __init__ """
		super(MarkupTagAction, self).__init__()
		self.isBlockLevel = isBlockLevel
		self.labelStack = []

	PAT_NUM = re.compile("[0-9]+")

	def start(self, contentHandler, tagName, attrs):
		""" generated source for method start """
		labels = []
		labels.append(DefaultLabels.MARKUP_PREFIX + tagName)
		classVal = attrs.getValue("class")
		if classVal != None and len(classVal)>0:
			classVal = self.PAT_NUM.sub("#",classVal).strip()
			vals = classVal.split(r"[ ]+")
			labels.append(DefaultLabels.MARKUP_PREFIX + "." + classVal.replace(' ', '.'))
			if len(vals)>1:
				for s in vals:
					labels.append(DefaultLabels.MARKUP_PREFIX + "." + s)
		id = attrs.get("id")
		if id != None and len(id)<0:
			id = self.PAT_NUM.sub("#",id)
			labels.append(DefaultLabels.MARKUP_PREFIX + "#" + id)
		ancestors = self.getAncestorLabels()
		labelsWithAncestors = []
		for l in labels:
			for an in ancestors:
				labelsWithAncestors.append(an)
				labelsWithAncestors.append(an + " " + l)
			labelsWithAncestors.append(l)
		contentHandler.addLabelAction(LabelAction(labelsWithAncestors))
		self.labelStack.append(labels)
		return self.isBlockLevel

	def end(self, contentHandler, tagName):
		""" generated source for method end """
		self.labelStack.pop()
		return self.isBlockLevel

	def changesTagLevel(self):
		""" generated source for method changesTagLevel """
		return self.isBlockLevel

	def getAncestorLabels(self):
		""" generated source for method getAncestorLabels """
		labelSet = set()
		for labels in labelStack:
			if labels == None:continue 
			labelSet.update(labels)
		return labelSet


class CommonTagActions:
	TA_IGNORABLE_ELEMENT=IgnorableElementTagAction()
	TA_ANCHOR_TEXT=AnchorTextTagAction()
	TA_BODY=BodyTagAction()
	TA_INLINE_WHITESPACE=InlineWhitespaceTagAction()
	TA_INLINE_NO_WHITESPACE=InlineTagAction()
	TA_BLOCK_LEVEL=BlockTagAction()
	TA_FONT=FontTagAction()

defaultTagActionMap={
	"STYLE" : CommonTagActions.TA_IGNORABLE_ELEMENT,
	"SCRIPT" : CommonTagActions.TA_IGNORABLE_ELEMENT,
	"OPTION" : CommonTagActions.TA_IGNORABLE_ELEMENT,
	"OBJECT" : CommonTagActions.TA_IGNORABLE_ELEMENT,
	"EMBED" : CommonTagActions.TA_IGNORABLE_ELEMENT,
	"APPLET" : CommonTagActions.TA_IGNORABLE_ELEMENT,
	#Note: link removed because it can be self-closing in HTML5
	#"LINK" : CommonTagActions.TA_IGNORABLE_ELEMENT,
	"A" : CommonTagActions.TA_ANCHOR_TEXT,
	"BODY" : CommonTagActions.TA_BODY,
	"STRIKE" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"U" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"B" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"I" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"EM" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"STRONG" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"SPAN" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
		#  New in 1.1 (especially to improve extraction quality from Wikipedia etc.,
	"SUP" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
		#  New in 1.2
	"CODE" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"TT" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"SUB" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"VAR" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
	"ABBR" : CommonTagActions.TA_INLINE_WHITESPACE,
	"ACRONYM" : CommonTagActions.TA_INLINE_WHITESPACE,
	"FONT" : CommonTagActions.TA_INLINE_NO_WHITESPACE,
		#  could also use TA_FONT 
		#  added in 1.1.1
	"NOSCRIPT" : CommonTagActions.TA_IGNORABLE_ELEMENT
}



#----------------------------------------------------------------------------
#                                LABEL ACTIONS
#----------------------------------------------------------------------------

# 
#  * Helps adding labels to {@link TextBlock}s.
#  * 
#  * @author Christian Kohlschtter
#  
class LabelAction(object):
	def __init__(self, *labels):
		self.labels = labels

	def addTo(self, textBlock):
		self.addLabelsTo(textBlock)

	def addLabelsTo(self, textBlock):
		textBlock.addLabels(self.labels)

	def __str__(self):
		return str(self.labels)

class ConditionalLabelAction(LabelAction):
	def __init__(self, condition, *labels):
		super(ConditionalLabelAction, self).__init__(*labels)
		self.condition = condition

	def addTo(self, textBlock):
		if self.condition(textBlock): self.addLabelsTo(textBlock)


class SpecialTokens:
	ANCHOR_TEXT_START = u'\ue00astart'
	ANCHOR_TEXT_END = u'\ue00aend'


#----------------------------------------------------------------------------
#                           SAX CONTENT HANDLER
#----------------------------------------------------------------------------

# 
#  * A simple SAX {@link ContentHandler}, used by {@link BoilerpipeSAXInput}. Can
#  * be used by different parser implementations, e.g. NekoHTML and TagSoup.
#  * 
#  * @author Christian Kohlschtter
#  


class BoilerpipeBaseParser(object):
	EVENT_START_TAG=0
	EVENT_END_TAG=1
	EVENT_CHARACTERS=2
	EVENT_WHITESPACE=3
	#all word characters except underscore -- i.e. not (not word or underscore)
	PAT_VALID_WORD_CHARACTER = re.compile(r"[^\W_]",re.UNICODE)
#	PAT_WORD = re.compile(r"\ue00a?[\w]+",re.UNICODE)
	PAT_WORD = re.compile(ur"\ue00a?[\w\"'\.,\!\@\-\:\;\$\?\(\)/]+",re.UNICODE)
	
	""" generated source for class BoilerpipeHTMLContentHandler """
	# 
	# 	 * Constructs a {@link BoilerpipeHTMLContentHandler} using the given
	# 	 * {@link TagActionMap}.
	# 	 * 
	# 	 * @param tagActions
	# 	 *			The {@link TagActionMap} to use, e.g.
	# 	 *			{@link DefaultTagActionMap}.
	# 	 
	def __init__(self, tagActions=None):
		""" generated source for method __init___0 """
		#super(BoilerpipeHTMLContentHandler, self).__init__()
		if tagActions==None: self.tagActions=defaultTagActionMap
		else: self.tagActions = tagActions


		self.clearTextBuffer()
		self.inBody = 0
		self.inAnchor = 0
		self.inIgnorableElement = 0
		self.textElementIdx = 0
		self.lastStartTag = None
		self.lastEndTag = None
		self.lastEvent = None
		self.offsetBlocks = 0
		self.currentContainedTextElements=set()
		self.flush = False
		self.inAnchorText = False

		self.title = None
		self.tagLevel = 0
		self.blockTagLevel = -1
		self.textBlocks = []
		self.labelStacks = []
		self.fontSizeStack = []
	
	# 
	# 	 * Recycles this instance.
	# 	 
	def recycle(self):
		""" generated source for method recycle """
		self.clearTextBuffer()
		self.inBody = 0
		self.inAnchor = 0
		self.inIgnorableElement = 0
		self.textElementIdx = 0
		self.lastStartTag = None
		self.lastEndTag = None
		self.lastEvent = None
		self.offsetBlocks = 0
		self.currentContainedTextElements=set()
		self.flush = False
		self.inAnchorText = False
		self.textBlocks=[]
		
		#--------- added -------
		self.title = None
		self.tagLevel = 0
		self.blockTagLevel = -1
		self.labelStacks = []
		self.fontSizeStack = []


#------------------------------- SAX Parser methods ----------------------------------------

	#  @Override
	def endDocument(self):
		""" generated source for method endDocument """
		self.flushBlock()

	#  @Override
	def startDocument(self): pass

	#  @Override
	def startElement(self, name,attrs):
		self.labelStacks.append([])
		
		tagAction = self.tagActions.get(name.strip().upper())

		if tagAction != None:
			self.flush |= tagAction.start(self, name, attrs)
			if tagAction.changesTagLevel(): self.tagLevel += 1
		else:
			self.tagLevel += 1
			self.flush = True
		self.lastEvent = self.EVENT_START_TAG
		self.lastStartTag = name

	#  @Override
	def endElement(self, name):
		tagAction = self.tagActions.get(name.strip().upper())

		
		if tagAction != None:
			self.flush |= tagAction.end(self, name)
			if tagAction.changesTagLevel(): self.tagLevel -= 1
		else:
			self.flush = True
			self.tagLevel -= 1

		if self.flush: self.flushBlock()
		self.lastEvent = self.EVENT_END_TAG
		self.lastEndTag = name
		self.labelStacks.pop()

	#  @Override
	def characters(self, content):
		self.textElementIdx += 1
		if self.flush:
			self.flushBlock()
			self.flush = False
		if self.inIgnorableElement != 0: return

		if len(content) == 0:	return
		
		strippedContent=content.strip()
		
		if len(strippedContent) == 0:
			self.addWhitespaceIfNecessary()
			self.lastEvent = self.EVENT_WHITESPACE
			return
		
		startWhitespace=content[0].isspace()
		if startWhitespace: self.addWhitespaceIfNecessary()
		
		if self.blockTagLevel == -1:
			self.blockTagLevel = self.tagLevel			
		self.textBuffer+=strippedContent
		self.tokenBuffer+=strippedContent
		
		endWhitespace=content[-1].isspace()
		if endWhitespace: self.addWhitespaceIfNecessary()
		
		self.lastEvent = self.EVENT_CHARACTERS
		self.currentContainedTextElements.add(self.textElementIdx)

	#  @Override
	def ignorableWhitespace(self, whitespace):
		self.addWhitespaceIfNecessary()

#------------------------------- utility methods ----------------------------------------


	def flushBlock(self):
		""" generated source for method flushBlock """
		if self.inBody == 0:
			if self.lastStartTag.lower()=="title": self.setTitle(self.textBuffer.strip())
			self.clearTextBuffer()
			return
		if len(self.tokenBuffer.strip())==0:
			self.clearTextBuffer()
			return

		tokens = self.tokenize(self.tokenBuffer)
		numWords = 0
		numLinkedWords = 0
		numWrappedLines = 0
		currentLineLength = -1
		#  don't count the first space
		maxLineLength = 80
		numTokens = 0
		numWordsCurrentLine = 0
		
		for token in tokens:
			if token==SpecialTokens.ANCHOR_TEXT_START: self.inAnchorText = True
			elif token==SpecialTokens.ANCHOR_TEXT_END: self.inAnchorText = False
			elif self.isWord(token):
				numTokens += 1
				numWords += 1
				numWordsCurrentLine += 1
				if self.inAnchorText:
					numLinkedWords += 1
				currentLineLength += len(token) + 1
				if currentLineLength > maxLineLength:
					numWrappedLines += 1
					currentLineLength = len(token)
					numWordsCurrentLine = 1
			else:
				numTokens += 1
	
		#if only special tokens (numTokens excludes special tokens)
		if numTokens == 0:
			self.clearTextBuffer()
			return

		if numWrappedLines == 0:
			numWordsInWrappedLines = numWords
			numWrappedLines = 1
		else:
			numWordsInWrappedLines = numWords - numWordsCurrentLine

		tb = document.TextBlock(self.textBuffer.strip(), self.currentContainedTextElements, numWords, numLinkedWords, numWordsInWrappedLines, numWrappedLines, self.offsetBlocks)
		self.currentContainedTextElements = set()
		self.offsetBlocks += 1
		self.clearTextBuffer()
		tb.setTagLevel(self.blockTagLevel)
		self.addTextBlock(tb)
		self.blockTagLevel = -1

	def addTextBlock(self, tb):
		""" generated source for method addTextBlock """
		for fontSize in self.fontSizeStack[::-1]:
			if fontSize != None:
				tb.addLabel("font-" + str(fontSize))
				break
		for labelStack in self.labelStacks:
			for labels in labelStack:
					labels.addTo(tb)
		self.textBlocks.append(tb)


	def isWord(self, token):
		""" generated source for method isWord """
		return self.PAT_VALID_WORD_CHARACTER.search(token)!=None
		
	def tokenize(self,text):
		return self.PAT_WORD.findall(text)

	def getTextBlocks(self):
		""" generated source for method getTextBlocks """
		return self.textBlocks
	
	def getTitle(self):
		""" generated source for method getTitle """
		return self.title

	def setTitle(self, s):
		""" generated source for method setTitle """
		if s == None or len(s)==0: return
		self.title = s

	# 
	# 	 * Returns a {@link TextDocument} containing the extracted {@link TextBlock}
	# 	 * s. NOTE: Only call this after parsing.
	# 	 * 
	# 	 * @return The {@link TextDocument}
	# 	 
	def toTextDocument(self):
		""" generated source for method toTextDocument """
		#  just to be sure
		self.flushBlock()
		return document.TextDocument(self.getTextBlocks(), self.getTitle())

	def addWhitespaceIfNecessary(self):
		""" generated source for method addWhitespaceIfNecessary """
		if len(self.textBuffer)==0 or not self.textBuffer[-1].isspace():
			self.textBuffer+=' '
		if len(self.tokenBuffer)==0 or not self.tokenBuffer[-1].isspace():
			self.tokenBuffer+=' '
	
	def clearTextBuffer(self):
		self.textBuffer=''
		self.tokenBuffer=''
	
	def addToken(self,token):
		self.addWhitespaceIfNecessary()
		self.tokenBuffer+=token
		self.addWhitespaceIfNecessary()

	def addLabelAction(self, la):
		""" generated source for method addLabelAction """
		if len(self.labelStacks)==0: self.labelStacks.append([])
		self.labelStacks[-1].append(la)




class BoilerpipeHTMLParser(HTMLParser,BoilerpipeBaseParser):
	def __init__(self):
		HTMLParser.__init__(self)
		BoilerpipeBaseParser.__init__(self)
		
	def feed(self,data):
		self.startDocument()
		HTMLParser.feed(self,data)
		self.endDocument()
	
	def handle_starttag(self, tag, attrs): self.startElement(tag,attrs)
	def handle_endtag(self, tag): self.endElement(tag)
	def handle_data(self, data): self.characters(data)

class BoilerpipeSAXContentHandler(ContentHandler,BoilerpipeBaseParser):
	def __init__(self):
		ContentHandler.__init__(self)
		BoilerpipeBaseParser.__init__(self)
