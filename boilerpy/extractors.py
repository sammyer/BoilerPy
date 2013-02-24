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
# package: de.l3s.boilerpipe.extractors

# 
#  * The base class of Extractors. Also provides some helper methods to quickly
#  * retrieve the text that remained after processing.
#  * 
#  * @author Christian Kohlschtter
#


from xml.sax import parseString, SAXException
import HTMLParser
from . import filters
from . import parser
import urllib2
import re

class Extractor(object):
	def __init__(self,filtr):
		self.filter=filtr	
	
	def getContent(self, text):
		doc=self.parseDoc(text)
		self.filter.process(doc)
		return doc.getContent()
	
	def getContentFromUrl(self, url):
		doc=self.getDocFromUrl(url)
		self.filter.process(doc)
		return doc.getContent()
	
	def getContentFromFile(self, filename):
		doc=self.getDocFromFile(filename)
		self.filter.process(doc)
		return doc.getContent()
	
	def getDocFromFile(self,filename):
		f=open(filename,'r')
		text=f.read()
		f.close()
		try:
			text=text.decode('utf8')
		except UnicodeDecodeError: pass
		return self.parseDoc(text)
	
	def getDocFromUrl(self,url):
		f=urllib2.urlopen(url)
		text=f.read()
		encoding=self.getUrlEncoding(f)
		f.close()
		try:
			text=text.decode(encoding)
		except UnicodeDecodeError: pass
		return self.parseDoc(text)

	def getUrlEncoding(self,f):
		try:
			return f.headers['content-type'].split('charset=')[1].split(';')[0]
		except: return 'utf8'
	
	def parseDoc(self,inputStr):
		bpParser=parser.BoilerpipeHTMLParser()
		try:
			bpParser.feed(inputStr)
		except:
			#in case of error, try again, first removing script tag content
			bpParser=parser.BoilerpipeHTMLParser()
			inputStr=re.sub(r'<(?:script|SCRIPT)[^>]*>.*?</(?:script|SCRIPT)>','<script></script>',inputStr,0,re.DOTALL)
			try:
				bpParser.feed(inputStr)
			except:
				print "Error parsing HTML : "+str(e)
				return None
		doc=bpParser.toTextDocument()
		return doc



# class ArticleExtractor
#  * A full-text extractor which is tuned towards news articles. In this scenario
#  * it achieves higher accuracy than {@link DefaultExtractor}.
articleFilterChain=filters.FilterChain([
	filters.TerminatingBlocksFinder(),
	filters.DocumentTitleMatchClassifier(None,True),
	filters.NumWordsRulesClassifier(),
	filters.IgnoreBlocksAfterContentFilter(),
	filters.BlockProximityFusion(1,False,False),
	filters.BoilerplateBlockFilter(),
	filters.BlockProximityFusion(1,True,False),
	filters.KeepLargestBlockFilter(),
	filters.ExpandTitleToContentFilter()
])
# 	 * Works very well for most types of Article-like HTML.
ARTICLE_EXTRACTOR = Extractor(articleFilterChain)



# class DefaultExtractor
# 	 * Usually worse than {@link ArticleExtractor}, but simpler/no heuristics.
#  * A quite generic full-text extractor. 
defaultFilterChain=filters.FilterChain([
	filters.SimpleBlockFusionProcessor(),
	filters.BlockProximityFusion(1,False,False),
	filters.DensityRulesClassifier()
])
DEFAULT_EXTRACTOR = Extractor(defaultFilterChain)



# class LargestContentExtractor(ExtractorBase):
#  * A full-text extractor which extracts the largest text component of a page.
#  * For news articles, it may perform better than the {@link DefaultExtractor},
#  * but usually worse than {@link ArticleExtractor}.
largestContentFilterChain=filters.FilterChain([
	filters.NumWordsRulesClassifier(),
	filters.BlockProximityFusion(1,False,False),
	filters.KeepLargestBlockFilter()
])
# 	 * Like {@link DefaultExtractor}, but keeps the largest text block only.
LARGEST_CONTENT_EXTRACTOR = Extractor(largestContentFilterChain)




# class CanolaExtractor
# 	 * Trained on krdwrd Canola (different definition of "boilerplate"). You may
# 	 * give it a try.
CANOLA_EXTRACTOR = Extractor(filters.CanolaFilter())




# class KeepEverythingExtractor
#  * Marks everything as content.
# 	 * Dummy Extractor; should return the input text. Use this to double-check
# 	 * that your problem is within a particular {@link BoilerpipeExtractor}, or
# 	 * somewhere else.
KEEP_EVERYTHING_EXTRACTOR = Extractor(filters.MarkEverythingContentFilter())




# Java class NumWordsRulesExtractor
#
#  * A quite generic full-text extractor solely based upon the number of words per
#  * block (the current, the previous and the next block).
NUM_WORDS_RULES_EXTRACTOR=Extractor(filters.NumWordsRulesClassifier())



# class ArticleSentencesExtractor
#  * A full-text extractor which is tuned towards extracting sentences from news articles.
ARTICLE_SENTENCES_EXTRACTOR=Extractor(filters.FilterChain([
	articleFilterChain,
	filters.SplitParagraphBlocksFilter(),
	filters.MinClauseWordsFilter()
]))


#  * A full-text extractor which extracts the largest text component of a page.
#  * For news articles, it may perform better than the {@link DefaultExtractor},
#  * but usually worse than {@link ArticleExtractor}.
class KeepEverythingWithMinKWordsFilter(filters.FilterChain):
	def __init__(self, kMin):
		filterArr = [
			filters.SimpleBlockFusionProcessor(),
			filters.MarkEverythingContentFilter(),
			filters.MinWordsFilter(kMin)
		]
		super(KeepEverythingWithMinKWordsFilter, self).__init__(filters)
