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
# package: de.l3s.boilerpipe.document
import copy,sys

# 
#  * Some pre-defined labels which can be used in conjunction with
#  * {@link TextBlock#addLabel(String)} and {@link TextBlock#hasLabel(String)}.
#  * 
#  * @author Christian Kohlschtter
#  
class DefaultLabels(object):
	""" generated source for class DefaultLabels """
	TITLE = "de.l3s.boilerpipe/TITLE"
	ARTICLE_METADATA = "de.l3s.boilerpipe/ARTICLE_METADATA"
	INDICATES_END_OF_TEXT = "de.l3s.boilerpipe/INDICATES_END_OF_TEXT"
	MIGHT_BE_CONTENT = "de.l3s.boilerpipe/MIGHT_BE_CONTENT"
	STRICTLY_NOT_CONTENT = "de.l3s.boilerpipe/STRICTLY_NOT_CONTENT"
	HR = "de.l3s.boilerpipe/HR"
	MARKUP_PREFIX = "<"

# 
#  * A text document, consisting of one or more {@link TextBlock}s.
#  * 
#  * @author Christian Kohlschtter
#  
class TextDocument(object):
	#	  * Creates a new {@link TextDocument} with given {@link TextBlock}s and
	#	  * given title.
	#	  * 
	#	  * @param title
	#	  *			The "main" title for this text document.
	#	  * @param textBlocks
	#	  *			The text blocks of this document.
	def __init__(self, textBlocks, title=None):
		self.title = title
		self.textBlocks = textBlocks

	#	  * Returns the {@link TextBlock}s of this document.
	#	  * 
	#	  * @return A list of {@link TextBlock}s, in sequential order of appearance.
	#	  
	def getTextBlocks(self):
		""" generated source for method getTextBlocks """
		return self.textBlocks

	def setTextBlocks(self,textBlocks): self.textBlocks=textBlocks

	# 
	#	  * Returns the "main" title for this document, or <code>null</code> if no
	#	  * such title has ben set.
	#	  * 
	#	  * @return The "main" title.
	def getTitle(self):
		""" generated source for method getTitle """
		return self.title

	# 
	#	  * Updates the "main" title for this document.
	#	  * 
	#	  * @param title
	def setTitle(self, title):
		""" generated source for method setTitle """
		self.title = title

	# 
	#	  * Returns the {@link TextDocument}'s content.
	#	  * 
	#	  * @return The content text.
	def getContent(self):
		""" generated source for method getContent """
		return self.getText(True, False)

	# 
	#	  * Returns the {@link TextDocument}'s content, non-content or both
	#	  * 
	#	  * @param includeContent Whether to include TextBlocks marked as "content".
	#	  * @param includeNonContent Whether to include TextBlocks marked as "non-content".
	#	  * @return The text.
	def getText(self, includeContent, includeNonContent):
		sb = ""
		for block in self.getTextBlocks():
			if block.isContent():
				if not includeContent:
					continue 
			else:
				if not includeNonContent:
					continue 
			sb+=block.getText()+'\n'
		return sb

	#	  * Returns detailed debugging information about the contained {@link TextBlock}s.
	#	  * @return Debug information.
	def debugString(self):
		sb = ""
		for tb in self.getTextBlocks():
			sb+=str(tb)+"\n"
		return sb





# 
#  * Describes a block of text.
#  * 
#  * A block can be an "atomic" text element (i.e., a sequence of text that is not
#  * interrupted by any HTML markup) or a compound of such atomic elements.
#  * 
#  * @author Christian Kohlschtter
#  

class TextBlock(object):
	""" generated source for class TextBlock """

	def __init__(self, text, containedTextElements=set(), numWords=0, numWordsInAnchorText=0, numWordsInWrappedLines=0, numWrappedLines=0, offsetBlocks=0):
		self._isContent = False
		self.labels = set()
		self.numFullTextWords = 0
		self.tagLevel = 0
		
		self.text = text
		self.containedTextElements = containedTextElements
		self.numWords = numWords
		self.numWordsInAnchorText = numWordsInAnchorText
		self.numWordsInWrappedLines = numWordsInWrappedLines
		self.numWrappedLines = numWrappedLines
		self.offsetBlocksStart = offsetBlocks
		self.offsetBlocksEnd = offsetBlocks
		self.initDensities()

	def initDensities(self):
		""" generated source for method initDensities """
		if self.numWordsInWrappedLines == 0:
			self.numWordsInWrappedLines = self.numWords
			self.numWrappedLines = 1
		self.textDensity = self.numWordsInWrappedLines / float(self.numWrappedLines)
		self.linkDensity = 0 if self.numWords==0 else self.numWordsInAnchorText / float(self.numWords)
		
	def isContent(self):
		""" generated source for method isContent """
		return self._isContent

	def setIsContent(self, isContent):
		""" generated source for method setIsContent """
		if isContent != self._isContent:
			self._isContent = isContent
			return True
		else:
			return False

	def getText(self):
		""" generated source for method getText """
		return self.text

	def getNumWords(self):
		""" generated source for method getNumWords """
		return self.numWords

	def getNumWordsInAnchorText(self):
		""" generated source for method getNumWordsInAnchorText """
		return self.numWordsInAnchorText

	def getTextDensity(self):
		""" generated source for method getTextDensity """
		return self.textDensity

	def getLinkDensity(self):
		""" generated source for method getLinkDensity """
		return self.linkDensity

	def mergeNext(self, nextTextBlock):
		""" generated source for method mergeNext """
		if self.text==None: self.text=""
		self.text+='\n'+nextTextBlock.text
		self.numWords += nextTextBlock.numWords
		self.numWordsInAnchorText += nextTextBlock.numWordsInAnchorText
		self.numWordsInWrappedLines += nextTextBlock.numWordsInWrappedLines
		self.numWrappedLines += nextTextBlock.numWrappedLines
		self.offsetBlocksStart = min(self.offsetBlocksStart, nextTextBlock.offsetBlocksStart)
		self.offsetBlocksEnd = max(self.offsetBlocksEnd, nextTextBlock.offsetBlocksEnd)
		self.initDensities()
		self._isContent |= nextTextBlock.isContent()
		self.containedTextElements|=nextTextBlock.containedTextElements
		self.numFullTextWords += nextTextBlock.numFullTextWords
		self.labels|=nextTextBlock.labels
		self.tagLevel = min(self.tagLevel, nextTextBlock.tagLevel)

	def getOffsetBlocksStart(self):
		""" generated source for method getOffsetBlocksStart """
		return self.offsetBlocksStart

	def getOffsetBlocksEnd(self):
		""" generated source for method getOffsetBlocksEnd """
		return self.offsetBlocksEnd

	def __repr__(self):
		""" generated source for method toString """
		return "[" + str(self.offsetBlocksStart) + "-" + str(self.offsetBlocksEnd) + ";tl=" + str(self.tagLevel) + "; nw=" + str(self.numWords) + ";nwl=" + str(self.numWrappedLines) + ";ld=" + str(self.linkDensity) + "]\t" + ("CONTENT" if self.isContent else "boilerplate") + "," + str(self.labels) + "\n" + str(self.getText())

	# 
	#	  * Adds an arbitrary String label to this {@link TextBlock}.
	#	  * 
	#	  * @param label The label
	#	  
	def addLabel(self, label):
		""" generated source for method addLabel """
		self.labels.add(label)

	# 
	#	  * Checks whether this TextBlock has the given label.
	#	  * 
	#	  * @param label The label
	#	  * @return <code>true</code> if this block is marked by the given label.
	#	  
	def hasLabel(self, label):
		""" generated source for method hasLabel """
		return label in self.labels

	def removeLabel(self, label):
		""" generated source for method removeLabel """
		try:
			self.labels.remove(label)
			return True
		except KeyError:
			return False

	# 
	#	  * Returns the labels associated to this TextBlock, or <code>null</code> if no such labels
	#	  * exist.
	#	  * 
	#	  * to the data structure. However it is recommended to use the label-specific methods in {@link TextBlock}
	#	  * whenever possible.
	#	  * 
	#	  * @return Returns the set of labels, or <code>null</code> if no labels was added yet.
	#	  
	def getLabels(self):
		""" generated source for method getLabels """
		return self.labels

	# 
	#	  * Adds a set of labels to this {@link TextBlock}.
	#	  * <code>null</code>-references are silently ignored.
	#	  * 
	#	  * @param labels The labels to be added. 
	#	  
	def addLabels(self, *labels):
		""" generated source for method addLabels """
		if len(labels)==0 or labels[0] == None: return
		if self.labels == None:	self.labels = set()
		elif len(labels)==1 and (type(labels[0])==set or type(labels[0])==list): self.labels|=set(labels[0])
		else: self.labels|=set(labels)


	# 
	#	  * Returns the containedTextElements BitSet, or <code>null</code>.
	#	  * @return
	#	  
	def getContainedTextElements(self):
		""" generated source for method getContainedTextElements """
		return self.containedTextElements

	def clone(self):
		try:
			clone = copy.copy(self)
		except copy.error:
			raise copy.error
		if self.labels != None:	clone.labels = self.labels.copy()
		if self.containedTextElements != None: clone.containedTextElements = self.containedTextElements.copy()
		return clone

	def getTagLevel(self):
		""" generated source for method getTagLevel """
		return self.tagLevel

	def setTagLevel(self, tagLevel):
		""" generated source for method setTagLevel """
		self.tagLevel = tagLevel

TextBlock.EMPTY_START = TextBlock("", set(), 0, 0, 0, 0, -1)
TextBlock.EMPTY_END = TextBlock("", set(), 0, 0, 0, 0, sys.maxint)



#  * Provides shallow statistics on a given TextDocument
#  * 
#  * @author Christian Kohlschuetter
#  
class TextDocumentStatistics(object):
	# 
	#	  * Computes statistics on a given {@link TextDocument}.
	#	  *
	#	  * @param doc The {@link TextDocument}.
	#	  * @param contentOnly if true then o
	#	  
	def __init__(self, doc, contentOnly):
		self.numWords=0
		self.numBlocks=0
		for tb in doc.getTextBlocks():
			if contentOnly and not tb.isContent(): continue 
			self.numWords += tb.getNumWords()
			self.numBlocks += 1


	#	  * Returns the average number of words at block-level (= overall number of words divided by
	#	  * the number of blocks).
	#	  * 
	#	  * @return Average
	#	  
	def avgNumWords(self):
		""" generated source for method avgNumWords """
		return self.numWords / float(self.numBlocks)

	# 
	#	  * Returns the overall number of words in all blocks.
	#	  * 
	#	  * @return Sum
	#	  
	def getNumWords(self):
		""" generated source for method getNumWords """
		return self.numWords
