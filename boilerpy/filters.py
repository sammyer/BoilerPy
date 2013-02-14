#!/usr/bin/env python
""" generated source for module MarkEverythingContentFilter """
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


#-----------------------------------------------------------------------
#                           FILTER MANIFEST
#-----------------------------------------------------------------------
# --------------------- Simple Filters: -----------------------
# MarkEverythingContentFilter - Marks all blocks as content.
# InvertedFilter - Reverts the "isContent" flag for all TextBlocks
# BoilerplateBlockFilter - Removes TextBlocks which have explicitly been marked as "not content". 
# MinWordsFilter - Keeps only those content blocks which contain at least k words.
# MinClauseWordsFilter - Keeps only blocks that have at least one segment fragment ("clause") with at least k words
# SplitParagraphBlocksFilter - Splits TextBlocks at paragraph boundaries
# SurroundingToContentFilter
# LabelToBoilerplateFilter - Marks all blocks that contain a given label as "boilerplate".
# LabelToContentFilter - Marks all blocks that contain a given label as "content".
#
# --------------------- Heuristic Filters: -----------------------
# SimpleBlockFusionProcessor - Merges two subsequent blocks if their text densities are equal.
# ContentFusion
# LabelFusion - Fuses adjacent blocks if their labels are equal.
# BlockProximityFusion - Fuses adjacent blocks if their distance (in blocks) does not exceed a certain limit.
# KeepLargestBlockFilter - Keeps the largest {@link TextBlock} only (by the number of words)
# ExpandTitleToContentFilter - Marks all TextBlocks "content" which are between the headline and the part that has already been marked content, if they are marked MIGHT_BE_CONTENT
# ArticleMetadataFilter
# AddPrecedingLabelsFilter - Adds the labels of the preceding block to the current block, optionally adding a prefix.
# DocumentTitleMatchClassifier - Marks TextBlocks which contain parts of the HTML TITLE tag
#
# --------------------- English-trained Heuristic Filters: -----------------------
# MinFulltextWordsFilter - Keeps only those content blocks which contain at least k full-text words
# KeepLargestFulltextBlockFilter - Keeps the largest TextBlock only (by the number of words)
# IgnoreBlocksAfterContentFilter - Marks all blocks as "non-content" that occur after blocks that have been marked INDICATES_END_OF_TEXT
# IgnoreBlocksAfterContentFromEndFilter - like above
# TerminatingBlocksFinder - Finds blocks which are potentially indicating the end of an article text and marks them with INDICATES_END_OF_TEXT
# NumWordsRulesClassifier - Classifies TextBlocks as content/not-content through rules that have been determined using the C4.8 machine learning algorithm
# DensityRulesClassifier - lassifies TextBlocks as content/not-content through rules that have been determined using the C4.8 machine learning algorithm
# CanolaFilter - A full-text extractor trained on krdwrd Canola




import re
from . import document
from document import DefaultLabels

# Boilerpipe abstract interface

class BoilerpipeFilter(object):
	def process(self, doc): pass
	
	def subtractBlocks(self,blockArr,blocksToRemove):
		#inefficient but in place: for block in blocksToRemove: blockArr.remove(blocksToRemove)
		#efficiently subtracts second array from first assuming blocksToRemove shows up in the same order as blocArr
		if len(blocksToRemove)==0: return blockArr
		newBlockArr=[]
		removeIter=iter(blocksToRemove)
		curBlockToRemove=removeIter.next()
		for idx,block in enumerate(blockArr):
			if block==curBlockToRemove:
				try:
					curBlockToRemove=removeIter.next()
				except StopIteration:
					#add the rest
					newBlockArr.extend(blockArr[idx+1:])
					break
			else: newBlockArr.append(block)
		return newBlockArr

# chain together multiple filters in sequence
class FilterChain(BoilerpipeFilter):
	def __init__(self,filterArr):
		super(FilterChain, self).__init__()
		self.filterArr=filterArr
		
	def process(self,doc):
		isUpdated=False
		for filtr in self.filterArr:
			isUpdated|=filtr.process(doc)
		return isUpdated


#-----------------------------------------------------------------------
#                           SIMPLE FILTERS
#-----------------------------------------------------------------------



# 
#  * Marks all blocks as content.
#  * 
#  * @author Christian Kohlschtter
#  
class MarkEverythingContentFilter(BoilerpipeFilter):
	def process(self, doc):
		""" generated source for method process """
		changes = False
		for tb in doc.getTextBlocks():
			if not tb.isContent():
				tb.setIsContent(True)
				changes = True
		return changes


# 
#  * Reverts the "isContent" flag for all {@link TextBlock}s
#  * 
#  * @author Christian Kohlschtter
#  
class InvertedFilter(BoilerpipeFilter):

	def process(self, doc):
		""" generated source for method process """
		tbs = doc.getTextBlocks()
		if len(tbs)==0: return False
		for tb in tbs: tb.setIsContent(not tb.isContent())
		return True


# 
#  * Removes {@link TextBlock}s which have explicitly been marked as "not content". 
#  * 
#  * @author Christian Kohlschtter
#  
class BoilerplateBlockFilter(BoilerpipeFilter):
	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		newBlocks=[tb for tb in textBlocks if tb.isContent()]
		hasChanges = len(newBlocks)<len(textBlocks)
		doc.setTextBlocks(newBlocks)

		return hasChanges


# 
#  * Keeps only those content blocks which contain at least <em>k</em> words.
#  * 
#  * @author Christian Kohlschtter
#  
class MinWordsFilter(BoilerpipeFilter):
	def __init__(self, minWords):
		super(MinWordsFilter, self).__init__()
		self.minWords = minWords

	def process(self, doc):
		changes = False
		for tb in doc.getTextBlocks():
			if not tb.isContent(): continue 
			if tb.getNumWords() < self.minWords:
				tb.setIsContent(False)
				changes = True
		return changes


# 
#  * Keeps only blocks that have at least one segment fragment ("clause") with at
#  * least <em>k</em> words (default: 5).
#  * 
#  * NOTE: You might consider using the {@link SplitParagraphBlocksFilter}
#  * upstream.
#  * 
#  * @author Christian Kohlschtter
#  * @see SplitParagraphBlocksFilter
#  
class MinClauseWordsFilter(BoilerpipeFilter):
	def __init__(self, minWords=5, acceptClausesWithoutDelimiter=False):
		super(MinClauseWordsFilter, self).__init__()
		self.minWords = minWords
		self.acceptClausesWithoutDelimiter = acceptClausesWithoutDelimiter

	PAT_CLAUSE_DELIMITER = re.compile(r"\b[\,\.\:\;\!\?]+(?:\s+|\Z)",re.UNICODE)
	PAT_WHITESPACE = re.compile("\s+")

	def process(self, doc):
		""" generated source for method process """
		changes = False
		for tb in doc.getTextBlocks():
			if not tb.isContent(): continue 
			hasClause = False
			possibleClauseArr=self.PAT_CLAUSE_DELIMITER.split(tb.getText())
			for possibleClause in possibleClauseArr[:-1]:
				hasClause = self.isClauseAccepted(possibleClause)
				if hasClause: break
			
			#  since clauses should *always end* with a delimiter, we normally
			#  don't consider text without one
			if self.acceptClausesWithoutDelimiter:
				hasClause |= self.isClauseAccepted(possibleClauseArr[-1])
			if not hasClause:
				tb.setIsContent(False)
				changes = True
				#  System.err.println("IS NOT CONTENT: " + text);
		return changes

	def isClauseAccepted(self, text):
		""" generated source for method isClause """
		n = 1
		for match in self.PAT_WHITESPACE.finditer(text):
			n += 1
			if n >= self.minWords: return True
		return n >= self.minWords


# 
#  * Splits TextBlocks at paragraph boundaries.
#  * 
#  * NOTE: This is not fully supported (i.e., it will break highlighting support
#  * via #getContainedTextElements()), but this one probably is necessary for some other
#  * filters.
#  * 
#  * @author Christian Kohlschtter
#  * @see MinClauseWordsFilter
#  
class SplitParagraphBlocksFilter(BoilerpipeFilter):
	def process(self, doc):
		changes = False
		blocks = doc.getTextBlocks()
		blocksNew = []
		for tb in blocks:
			text = tb.getText();
			paragraphs = re.split(r"[\n\r]+",text)
			if len(paragraphs)<2:
				blocksNew.append(tb)
				continue 
			isContent = tb.isContent()
			labels = tb.getLabels()
			for p in paragraphs:
				tbP=document.TextBlock(p)
				tbP.setIsContent(isContent)
				tbP.addLabels(labels)
				blocksNew.append(tbP)
				changes = True
				
		if changes: doc.setTextBlocks(blocksNew)
		return changes
		

class SurroundingToContentFilter(BoilerpipeFilter):
	# this is now default when no arguments are passed
	#INSTANCE_TEXT = SurroundingToContentFilter(TextBlockCondition())
	
	#ctor - condition is an function for an additional condition to determine if it can be made content
	def __init__(self, condition=lambda tb:tb.getLinkDensity()==0 and tb.getNumWords()>6):
		super(SurroundingToContentFilter, self).__init__()
		self.cond=condition

	def process(self, doc):
		""" generated source for method process """
		tbs = doc.getTextBlocks()
		n=len(tbs)
		hasChanges=False
		i=1
		while i<n-1:
			prev=tbs[i-1]
			cur=tbs[i]
			next=tbs[i+1]
			if not cur.isContent() and prev.isContent() and next.isContent() and self.cond(cur):
				cur.setIsContent(True)
				hasChanges = True
				i+=2
			else: i+=1
			# WARNING: POSSIBLE BUG - in original i+=2 regardless of whether content is found.  this seems illogica to me - should be +=1

		return hasChanges

# 
#  * Marks all blocks that contain a given label as "boilerplate".
#  * 
#  * @author Christian Kohlschtter
#  
class LabelToBoilerplateFilter(BoilerpipeFilter):
	""" generated source for class LabelToBoilerplateFilter """
	#INSTANCE_STRICTLY_NOT_CONTENT = LabelToBoilerplateFilter(DefaultLabels.STRICTLY_NOT_CONTENT)

	def __init__(self, *labels):
		super(LabelToBoilerplateFilter, self).__init__()
		self.labels = labels

	def process(self, doc):
		changes = False
		for tb in doc.getTextBlocks():
			if tb.isContent() and any(tb.hasLabel(label) for label in self.labels):
				tb.setIsContent(False)
				changes = True
		return changes


# 
#  * Marks all blocks that contain a given label as "content".
#  * 
#  * @author Christian Kohlschtter
#  
class LabelToContentFilter(BoilerpipeFilter):
	""" generated source for class LabelToContentFilter """
	def __init__(self, *labels):
		""" generated source for method __init__ """
		super(LabelToContentFilter, self).__init__()
		self.labels = labels

	def process(self, doc):
		changes = False
		for tb in doc.getTextBlocks():
			if not tb.isContent() and any(tb.hasLabel(label) for label in self.labels):
				tb.setIsContent(True)
				changes = True
		return changes





#-----------------------------------------------------------------------
#                       GENERIC HEURISTIC FILTERS
#-----------------------------------------------------------------------



# 
#  * Merges two subsequent blocks if their text densities are equal.
#  * 
#  * @author Christian Kohlschtter
#  
class SimpleBlockFusionProcessor(BoilerpipeFilter):
	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		changes = False
		if len(textBlocks) < 2: return False
		prevBlock = textBlocks[0]
		blocksToRemove=[]
		for block in textBlocks[1:]:
			if prevBlock.getTextDensity() == block.getTextDensity():
				prevBlock.mergeNext(block)
				blocksToRemove.append(block)
				changes = True
			else:
				prevBlock = block

		if changes: doc.setTextBlocks(self.subtractBlocks(textBlocks,blocksToRemove))
		return changes



class ContentFusion(BoilerpipeFilter):
	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		if len(textBlocks) < 2: return False
		#WARNNING: POSSIBLE BUG FOUND : shouldn't prevBlock be reset every passthrough?
		changes=False
		#changedOnPass - if it has been changed on the previous passthrough
		changedOnPass=True
		while changedOnPass:
			changedOnPass = False
			prevBlock = textBlocks[0]
			blocksToRemove=[]
			for block in textBlocks[1:]:
				if prevBlock.isContent() and block.getLinkDensity() < 0.56 and not block.hasLabel(DefaultLabels.STRICTLY_NOT_CONTENT):
					prevBlock.mergeNext(block)
					blocksToRemove.append(block)
					changedOnPass=True
					changes = True
				else:
					prevBlock = block
				textBlocks=self.subtractBlocks(textBlocks,blocksToRemove)
		if changes: doc.setTextBlocks(textBlocks)

		return changes


# 
#  * Fuses adjacent blocks if their labels are equal.
#  * 
#  * @author Christian Kohlschtter
#  
class LabelFusion(BoilerpipeFilter):
	#INSTANCE = LabelFusion("")

	# 
	#	  * Creates a new {@link LabelFusion} instance.
	#	  *
	#	  * @param maxBlocksDistance The maximum distance in blocks.
	#	  * @param contentOnly 
	#	  
	def __init__(self, labelPrefix=""):
		""" generated source for method __init__ """
		super(LabelFusion, self).__init__()
		self.labelPrefix = labelPrefix

	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		if len(textBlocks) < 2: return False
		changes = False
		prevBlock = textBlocks[0]
		blocksToRemove=[]
		for block in textBlocks[1::]:
			if self.equalLabels(prevBlock.getLabels(), block.getLabels()):
				prevBlock.mergeNext(block)
				blocksToRemove.append(block)
				changes = True
			else:
				prevBlock = block
		
		if changes: doc.setTextBlocks(self.subtractBlocks(textBlocks,blocksToRemove))

		return changes

	def equalLabels(self, labels1, labels2):
		""" generated source for method equalLabels """
		if labels1 == None or labels2 == None: return False
		#NOTE: Should blocks be merged if neither of them have labels???  i.e. labels1==labels2==empty set
		return self.markupLabelsOnly(labels1) == self.markupLabelsOnly(labels2)

	def markupLabelsOnly(self, labels):
		return set([label for label in labels if label.startswith(DefaultLabels.MARKUP_PREFIX)])



# 
#  * Fuses adjacent blocks if their distance (in blocks) does not exceed a certain limit.
#  * This probably makes sense only in cases where an upstream filter already has removed some blocks.
#  * 
#  * @author Christian Kohlschtter
#  
class BlockProximityFusion(BoilerpipeFilter):
	""" generated source for class BlockProximityFusion """
	#MAX_DISTANCE_1 = BlockProximityFusion(1, False, False)
	#MAX_DISTANCE_1_SAME_TAGLEVEL = BlockProximityFusion(1, False, True)
	#MAX_DISTANCE_1_CONTENT_ONLY = BlockProximityFusion(1, True, False)
	#MAX_DISTANCE_1_CONTENT_ONLY_SAME_TAGLEVEL = BlockProximityFusion(1, True, True)

	# 
	#	  * Creates a new {@link BlockProximityFusion} instance.
	#	  *
	#	  * @param maxBlocksDistance The maximum distance in blocks.
	#	  * @param contentOnly 
	#	  
	def __init__(self, maxBlocksDistance=1, contentOnly=False, sameTagLevelOnly=False):
		""" generated source for method __init__ """
		super(BlockProximityFusion, self).__init__()
		self.maxBlocksDistance = maxBlocksDistance
		self.contentOnly = contentOnly
		self.sameTagLevelOnly = sameTagLevelOnly

	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		if len(textBlocks) < 2: return False
		changes = False

		if self.contentOnly:
			startIdx=None
			for idx,block in enumerate(textBlocks):
				if block.isContent():
					startIdx=idx
					break
			if startIdx == None: return False
		else:
			startIdx=0
		
		prevBlock=textBlocks[startIdx]		
		blocksToRemove=[]
		for block in textBlocks[startIdx+1:]:
			if not block.isContent():
				prevBlock = block
				continue 
			diffBlocks = block.getOffsetBlocksStart() - prevBlock.getOffsetBlocksEnd() - 1;
			if diffBlocks <= self.maxBlocksDistance:
				ok=True
				if self.contentOnly:
					if not prevBlock.isContent() or not block.isContent():
						ok = False
				if self.sameTagLevelOnly and prevBlock.getTagLevel() != block.getTagLevel():
					ok = False
				if ok:
					prevBlock.mergeNext(block)
					#remove current block
					blocksToRemove.append(block)
					changes = True
				else:
					prevBlock = block
			else:
				prevBlock = block
				
		if len(blocksToRemove)>0:
			newBlocks=self.subtractBlocks(textBlocks,blocksToRemove)
			doc.setTextBlocks(newBlocks)
			changes=True
			
		return changes



# 
#  * Keeps the largest {@link TextBlock} only (by the number of words). In case of
#  * more than one block with the same number of words, the first block is chosen.
#  * All discarded blocks are marked "not content" and flagged as
#  * {@link DefaultLabels#MIGHT_BE_CONTENT}.
#  * 
#  * Note that, by default, only TextBlocks marked as "content" are taken into consideration.
#  * 
#  * @author Christian Kohlschtter
#  
class KeepLargestBlockFilter(BoilerpipeFilter):
	""" generated source for class KeepLargestBlockFilter """
	#INSTANCE = KeepLargestBlockFilter(False)
	#INSTANCE_EXPAND_TO_SAME_TAGLEVEL = KeepLargestBlockFilter(True)

	def __init__(self, expandToSameLevelText=False):
		""" generated source for method __init__ """
		super(KeepLargestBlockFilter, self).__init__()
		self.expandToSameLevelText = expandToSameLevelText

	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		if len(textBlocks) < 2: return False
		
		try:
			contentBlockIter=(tb for tb in textBlocks if tb.isContent())
			largestBlock=max(contentBlockIter,key=lambda tb:tb.getNumWords())
		except ValueError:
			#no content blocks exist / largest block not found
			largestBlock=None
		
		for tb in textBlocks:
			if tb == largestBlock:
				tb.setIsContent(True)
			else:
				tb.setIsContent(False)
				tb.addLabel(DefaultLabels.MIGHT_BE_CONTENT)
		
		if self.expandToSameLevelText and largestBlock!=None:
			level = largestBlock.getTagLevel()
			largestBlockIdx=textBlocks.index(largestBlock)
			
			for tb in textBlocks[largestBlockIdx::-1]:
				tl=tb.getTagLevel()
				if tl < level: break
				elif tl == level: tb.setIsContent(True)

			for tb in textBlocks[largestBlockIdx:]:
				tl=tb.getTagLevel()
				if tl < level: break
				elif tl == level: tb.setIsContent(True)

		return True


#  * Marks all {@link TextBlock}s "content" which are between the headline and the part that
#  * has already been marked content, if they are marked {@link DefaultLabels#MIGHT_BE_CONTENT}.
#  * 
#  * This filter is quite specific to the news domain.
#  * 
#  * @author Christian Kohlschtter
#  
class ExpandTitleToContentFilter(BoilerpipeFilter):
	def process(self, doc):
		""" generated source for method process """
		i = 0
		titleIdx = -1
		contentStart = -1
		for tb in doc.getTextBlocks():
			if contentStart == -1 and tb.hasLabel(DefaultLabels.TITLE):
				titleIdx = i
			if contentStart == -1 and tb.isContent():
				contentStart = i
			i += 1
			
		if contentStart <= titleIdx or titleIdx == -1: return False
		
		changes = False
		for tb in doc.getTextBlocks()[titleIdx:contentStart]:
			if tb.hasLabel(DefaultLabels.MIGHT_BE_CONTENT):
				changes |= tb.setIsContent(True)
		return changes


class ArticleMetadataFilter(BoilerpipeFilter):
	#checks for date/time/author blocks
	PATTERNS_SHORT = [re.compile(r"^[0-9 \,\./]*\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\b[0-9 \,\:apm\./]*(?:[CPSDMGET]{2,3})?$"), re.compile("^[Bb]y ")];
	
	def process(self, doc):
		""" generated source for method process """
		changed = False
		for tb in doc.getTextBlocks():
			if tb.getNumWords() > 10: continue 
			for p in self.PATTERNS_SHORT:
				text = tb.getText()
				if p.search(text):
					changed = True
					tb.setIsContent(True)
					tb.addLabel(DefaultLabels.ARTICLE_METADATA)
					break
		return changed


# 
#  * Adds the labels of the preceding block to the current block, optionally adding a prefix.
#  * 
#  * @author Christian Kohlschtter
#  
class AddPrecedingLabelsFilter(BoilerpipeFilter):
	#INSTANCE = AddPrecedingLabelsFilter("")
	#INSTANCE_PRE = AddPrecedingLabelsFilter("^")

	# 
	#	  * Creates a new {@link AddPrecedingLabelsFilter} instance.
	#	  *
	#	  * @param maxBlocksDistance The maximum distance in blocks.
	#	  * @param contentOnly 
	#	  
	def __init__(self, labelPrefix=""):
		""" generated source for method __init__ """
		super(AddPrecedingLabelsFilter, self).__init__()
		self.labelPrefix = labelPrefix

	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		if len(textBlocks) < 2: return False
		changes = False
		blockBelow = None
		
		for block in textBlocks[::-1]:
			if blockBelow != None:
				labels=block.getLabels()
				if labels != None and len(labels)>0:
					for l in labels: blockBelow.addLabel(self.labelPrefix + l)
					changes = True
			blockBelow = block

		return changes


# 
#  * Marks {@link TextBlock}s which contain parts of the HTML
#  * <code>&lt;TITLE&gt;</code> tag, using some heuristics which are quite
#  * specific to the news domain.
#  * 
#  * @author Christian Kohlschtter
#  

class DocumentTitleMatchClassifier(BoilerpipeFilter):
	""" generated source for class DocumentTitleMatchClassifier """

	def __init__(self, title, useDocTitle=False):
		""" generated source for method __init__ """
		super(DocumentTitleMatchClassifier, self).__init__()
		self.useDocTitle=useDocTitle
		if useDocTitle: self.potentialTitles=None
		else: self.potentialTitles=self.findPotentialTitles(title)
					
	def findPotentialTitles(self,title):
		if title == None: return None
		title = title.strip()
		if len(title)==0:
			return None
		else:
			potentialTitles = set()
			potentialTitles.add(title)
			p = self.getLongestPart(title, "[ ]*[\||:][ ]*")
			if p != None: potentialTitles.add(p)
			p = self.getLongestPart(title, "[ ]*[\||:\(\)][ ]*")
			if p != None: potentialTitles.add(p)
			p = self.getLongestPart(title, "[ ]*[\||:\(\)\-][ ]*")
			if p != None: potentialTitles.add(p)
			p = self.getLongestPart(title, "[ ]*[\||,|:\(\)\-][ ]*")
			if p != None: potentialTitles.add(p)
		return potentialTitles

	def getPotentialTitles(self):
		""" generated source for method getPotentialTitles """
		return self.potentialTitles

	def getLongestPart(self, title, pattern):
		""" generated source for method getLongestPart """
		parts = re.split(pattern,title)
		if len(parts)==1: return None
		
		longestNumWords = 0
		longestPart = ""
		for p in parts:
			if ".com" in p: continue 
			numWords=self.getNumWords(p)
			if numWords > longestNumWords or len(p)>len(longestPart):
				longestNumWords = numWords
				longestPart = p
		if len(longestPart)==0: return None
		else: return longestPart.strip()

	def getNumWords(self,text):
		return len(re.findall("\w+",text,re.UNICODE))

	def process(self, doc):
		""" generated source for method process """
		if self.useDocTitle: self.potentialTitles=self.findPotentialTitles(doc.getTitle())
		if self.potentialTitles == None: return False
		changes = False
		for tb in doc.getTextBlocks():
			text=tb.getText().strip().lower()
			if any(candidate.lower()==text for candidate in self.potentialTitles):
				tb.addLabel(DefaultLabels.TITLE)
				changes = True
		return changes









#-----------------------------------------------------------------------
#                          ENGLISH HEURISTIC FILTERS
#-----------------------------------------------------------------------
# --- Heuristic Filters that have been trained on English laguage text


# 
#  * Base class for some heuristics that are used by boilerpipe filters.
#  * 
#  * @author Christian Kohlschtter
#  
class HeuristicFilterBase(BoilerpipeFilter):
	def getNumFullTextWords(self, tb, minTextDensity=9):
		if tb.getTextDensity() >= minTextDensity: return tb.getNumWords()
		else: return 0

# 
#  * Keeps only those content blocks which contain at least k full-text words
#  * (measured by {@link HeuristicFilterBase#getNumFullTextWords(TextBlock)}). k is 30 by default.
#  * 
#  * @author Christian Kohlschtter
#  
class MinFulltextWordsFilter(HeuristicFilterBase):
	def __init__(self, minWords=30):
		self.minWords = minWords

	def process(self, doc):
		""" generated source for method process """
		changes = False
		for tb in doc.getTextBlocks():
			if tb.isContent() and self.getNumFullTextWords(tb) < self.minWords:
				tb.setIsContent(False)
				changes = True
		return changes


# 
#  * Keeps the largest {@link TextBlock} only (by the number of words). In case of
#  * more than one block with the same number of words, the first block is chosen.
#  * All discarded blocks are marked "not content" and flagged as
#  * {@link DefaultLabels#MIGHT_BE_CONTENT}.
#  * 
#  * As opposed to {@link KeepLargestBlockFilter}, the number of words are
#  * computed using {@link HeuristicFilterBase#getNumFullTextWords(TextBlock)}, which only counts
#  * words that occur in text elements with at least 9 words and are thus believed to be full text.
#  * 
#  * NOTE: Without language-specific fine-tuning (i.e., running the default instance), this filter
#  * may lead to suboptimal results. You better use {@link KeepLargestBlockFilter} instead, which
#  * works at the level of number-of-words instead of text densities.
#  * 
#  * @author Christian Kohlschtter
#  
class KeepLargestFulltextBlockFilter(HeuristicFilterBase):

	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		if len(textBlocks) < 2: return False
		contentBlocks=[block for block in textBlocks if block.isContent()]
		if len(contentBlocks)==0: return False
		largestBlock=max(contentBlocks,key=self.getNumFullTextWords)

		for tb in textBlocks:
			if tb == largestBlock:
				tb.setIsContent(True)
			else:
				tb.setIsContent(False)
				tb.addLabel(DefaultLabels.MIGHT_BE_CONTENT)
		return True

# 
#  * Marks all blocks as "non-content" that occur after blocks that have been
#  * marked {@link DefaultLabels#INDICATES_END_OF_TEXT}. These marks are ignored
#  * unless a minimum number of words in content blocks occur before this mark (default: 60).
#  * This can be used in conjunction with an upstream {@link TerminatingBlocksFinder}.
#  * 
#  * @author Christian Kohlschtter
#  * @see TerminatingBlocksFinder
#  
class IgnoreBlocksAfterContentFilter(HeuristicFilterBase):
	""" generated source for class IgnoreBlocksAfterContentFilter """
	#DEFAULT_INSTANCE = IgnoreBlocksAfterContentFilter(60)
	#INSTANCE_200 = IgnoreBlocksAfterContentFilter(200)

	def __init__(self, minNumWords=60):
		self.minNumWords = minNumWords

	def process(self, doc):
		""" generated source for method process """
		changes = False
		numWords = 0
		foundEndOfText = False
		for block in doc.getTextBlocks():
			if block.isContent():
				numWords += self.getNumFullTextWords(block)
			if block.hasLabel(DefaultLabels.INDICATES_END_OF_TEXT) and numWords >= self.minNumWords:
				foundEndOfText = True
			if foundEndOfText:
				changes = True
				block.setIsContent(False)

		return changes
# 
#  * Marks all blocks as "non-content" that occur after blocks that have been
#  * marked {@link DefaultLabels#INDICATES_END_OF_TEXT}, and after any content block.
#  * This filter can be used in conjunction with an upstream {@link TerminatingBlocksFinder}.
#  * 
#  * @author Christian Kohlschtter
#  * @see TerminatingBlocksFinder
#  
class IgnoreBlocksAfterContentFromEndFilter(HeuristicFilterBase):

	def process(self, doc):
		""" generated source for method process """
		changes = False
		words = 0
		blocks = doc.getTextBlocks()
		if len(blocks)==0: return False
		for tb in blocks[::-1]:
			if tb.hasLabel(DefaultLabels.INDICATES_END_OF_TEXT):
				tb.addLabel(DefaultLabels.STRICTLY_NOT_CONTENT)
				tb.removeLabel(DefaultLabels.MIGHT_BE_CONTENT)
				tb.setIsContent(False)
				changes = True
			elif tb.isContent():
				words += tb.getNumWords()
				if words > 200: break
		return changes


# 
#  * Finds blocks which are potentially indicating the end of an article text and
#  * marks them with {@link DefaultLabels#INDICATES_END_OF_TEXT}. This can be used
#  * in conjunction with a downstream {@link IgnoreBlocksAfterContentFilter}.
#  * 
#  * @author Christian Kohlschtter
#  * @see IgnoreBlocksAfterContentFilter
#  
class TerminatingBlocksFinder(BoilerpipeFilter):

	#  public static long timeSpent = 0;
	def process(self, doc):
		""" generated source for method process """
		changes = False
		
		for tb in doc.getTextBlocks():
			if tb.getNumWords() >=15: continue
			text=tb.getText().strip()
			if len(text)<8: continue
			textLC = text.lower()
			
			startmatches=(" reuters","please rate this","post a comment")
			inmatches=("what you think...","add your comment","add comment","reader views","have your say","reader comments","rtta artikeln")
			eqmatch="thanks for your comments - this feedback is now closed"
			
			if textLC.startswith("comments") or self.startsWithNumber(textLC, " comments", " users responded in") or any(textLC.startswith(matchStr) for matchStr in startmatches) or any(matchStr in textLC for matchStr in inmatches) or textLC == eqmatch:
				tb.addLabel(DefaultLabels.INDICATES_END_OF_TEXT)
				changes = True
		#  timeSpent += System.currentTimeMillis() - t;
		return changes

	# 
	# 	 * Checks whether the given text t starts with a sequence of digits,
	# 	 * followed by one of the given strings.
	# 	 * 
	# 	 * @param t
	# 	 *			The text to examine
	# 	 * @param len
	# 	 *			The length of the text to examine
	# 	 * @param str
	# 	 *			Any strings that may follow the digits.
	# 	 * @return true if at least one combination matches
	# 	 
	def startsWithNumber(self, text, *matchStrArr):
		""" generated source for method startsWithNumber """
		numberMatch=re.search('\D',text)
		if numberMatch==None: pos=len(text)
		else: pos=numberMatch.start()
		if pos==0: return False
		else: return any(text.startswith(matchStr,pos) for matchStr in matchStrArr)


# 
#  * Classifies {@link TextBlock}s as content/not-content through rules that have
#  * been determined using the C4.8 machine learning algorithm, as described in
#  * the paper "Boilerplate Detection using Shallow Text Features" (WSDM 2010),
#  * particularly using number of words per block and link density per block.
#  * 
#  * @author Christian Kohlschtter
#  
class NumWordsRulesClassifier(BoilerpipeFilter):

	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		hasChanges = False
		
		n=len(textBlocks)
		for i,currentBlock in enumerate(textBlocks):
			if i>0: prevBlock=textBlocks[i-1]
			else: prevBlock=document.TextBlock.EMPTY_START
			if i+1<n: nextBlock=textBlocks[i+1]
			else: nextBlock=document.TextBlock.EMPTY_START
			hasChanges |= self.classify(prevBlock, currentBlock, nextBlock)
		return hasChanges

	def classify(self, prev, curr, next):
		""" generated source for method classify """
		isContent = False
		if curr.getLinkDensity() <= 0.333333:
			if prev.getLinkDensity() <= 0.555556:
				if curr.getNumWords() <= 16:
					if next.getNumWords() <= 15:
						if prev.getNumWords() <= 4:
							isContent = False
						else:
							isContent = True
					else:
						isContent = True
				else:
					isContent = True
			else:
				if curr.getNumWords() <= 40:
					if next.getNumWords() <= 17:
						isContent = False
					else:
						isContent = True
				else:
					isContent = True
		else:
			isContent = False
		return curr.setIsContent(isContent)



# 
#  * Classifies {@link TextBlock}s as content/not-content through rules that have
#  * been determined using the C4.8 machine learning algorithm, as described in the
#  * paper "Boilerplate Detection using Shallow Text Features", particularly using
#  * text densities and link densities.
#  * 
#  * @author Christian Kohlschtter
#  
class DensityRulesClassifier(BoilerpipeFilter):

	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		hasChanges = False
		
		n=len(textBlocks)
		for i,currentBlock in enumerate(textBlocks):
			if i>0: prevBlock=textBlocks[i-1]
			else: prevBlock=document.TextBlock.EMPTY_START
			if i+1<n: nextBlock=textBlocks[i+1]
			else: nextBlock=document.TextBlock.EMPTY_START
			hasChanges |= self.classify(prevBlock, currentBlock, nextBlock)
		return hasChanges

	def classify(self, prev, curr, next):
		""" generated source for method classify """
		isContent = False
		if curr.getLinkDensity() <= 0.333333:
			if prev.getLinkDensity() <= 0.555556:
				if curr.getTextDensity() <= 9:
					if next.getTextDensity() <= 10:
						if prev.getTextDensity() <= 4:
							isContent = False
						else:
							isContent = True
					else:
						isContent = True
				else:
					if next.getTextDensity() == 0:
						isContent = False
					else:
						isContent = True
			else:
				if next.getTextDensity() <= 11:
					isContent = False
				else:
					isContent = True
		else:
			isContent = False
		return curr.setIsContent(isContent)

# 
#  * A full-text extractor trained on <a href="http://krdwrd.org/">krdwrd</a> <a
#  * href
#  * ="https://krdwrd.org/trac/attachment/wiki/Corpora/Canola/CANOLA.pdf">Canola
#  * </a>. Works well with {@link SimpleEstimator}, too.
#  * 
#  * @author Christian Kohlschtter
#  
class CanolaFilter(BoilerpipeFilter):

	def process(self, doc):
		""" generated source for method process """
		textBlocks = doc.getTextBlocks()
		hasChanges = False
		
		n=len(textBlocks)
		for i,currentBlock in enumerate(textBlocks):
			if i>0: prevBlock=textBlocks[i-1]
			else: prevBlock=document.TextBlock.EMPTY_START
			if i+1<n: nextBlock=textBlocks[i+1]
			else: nextBlock=document.TextBlock.EMPTY_START
			hasChanges |= self.classify(prevBlock, currentBlock, nextBlock)
		return hasChanges

	def classify(self, prev, curr, next):
		""" generated source for method classify """
		cond1=curr.getLinkDensity() > 0 and next.getNumWords() > 11
		cond2=curr.getNumWords() > 19
		cond3=next.getNumWords() > 6 and next.getLinkDensity() == 0 and prev.getLinkDensity() == 0 and (curr.getNumWords() > 6 or prev.getNumWords() > 7 or next.getNumWords() > 19)
		isContent = cond1 or cond2 or cond3
		return curr.setIsContent(isContent)

