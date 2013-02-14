import unittest
import sys
from boilerpy.document import TextDocument,TextBlock
from boilerpy.filters import *
from boilerpy.extractors import Extractor

def runTests():
	suite = unittest.TestLoader().loadTestsFromTestCase(TestFilters)
	unittest.TextTestRunner(verbosity=2).run(suite)
	suite = unittest.TestLoader().loadTestsFromTestCase(TestParser)
	unittest.TextTestRunner(verbosity=2).run(suite)

def runOneTest():
	testName='test_anchor'
	suite = unittest.TestSuite()
	suite.addTest(TestParser(testName))
	unittest.TextTestRunner(verbosity=2).run(suite)

class TestFilters(unittest.TestCase):
	defaultWords="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec fermentum tincidunt magna, eu pulvinar mauris dapibus pharetra. In varius, nisl a rutrum porta, sem sem semper lacus, et varius urna tellus vel lorem. Nullam urna eros, luctus eget blandit ac, imperdiet feugiat ipsum. Donec laoreet tristique mi a bibendum. Sed pretium bibendum scelerisque. Mauris id pellentesque turpis. Mauris porta adipiscing massa, quis tempus dui pharetra ac. Morbi lacus mauris, feugiat ac tempor ut, congue tincidunt risus. Pellentesque tincidunt adipiscing elit, in fringilla enim scelerisque vel. Nulla facilisi. ".split(' ')
	
	def makedoc(self,wordsArr,numAnchorWordsArr=None,isContentArr=None,labelArr=None):
		textBlocks=[]
		for idx,words in enumerate(wordsArr):
			if type(words)==int:
				numWords=words
				text=' '.join(self.defaultWords[:numWords])
			else:
				text=words
				numWords=text.count(' ')
			try:
				numAnchorWords=numAnchorWordsArr[idx]
			except TypeError,IndexError:
				numAnchorWords=0
			block=TextBlock(text,set(),numWords,numAnchorWords,0,0,idx)
			try:
				block.setIsContent(isContentArr[idx])
			except TypeError,IndexError:
				pass
			try:
				label=labelArr[idx]
				if label==None: pass
				elif type(label)==list:
					for l in label: block.addLabel(l)
				else: block.addLabel(label)
			except TypeError,IndexError:
				pass
				
			textBlocks.append(block)
		
		return TextDocument(textBlocks)
	
	def verifyContent(self,filtr,doc,contentArr,show=False):
		isContentBefore=[block.isContent() for block in doc.getTextBlocks()]
		isChanged=filtr.process(doc)
		isContent=[block.isContent() for block in doc.getTextBlocks()]
		self.assertEqual(isContent,contentArr)
		self.assertEqual(isChanged,isContent!=isContentBefore)
		
	def test_markEveryhingContent(self):
		doc=self.makedoc([5,100,80],None,[False,True,False])
		self.verifyContent(MarkEverythingContentFilter(),doc,[True,True,True])
		
	def test_inverted(self):
		doc=self.makedoc([5,100,80],None,[False,True,False])
		self.verifyContent(InvertedFilter(),doc,[True,False,True])
		
	def test_boilerplateBlock(self):
		#keeps if isContent
		doc=self.makedoc([5,100,10,50,80],None,[False,True,False,True,False])
		initBlocks=doc.getTextBlocks()
		finalBlocks=[initBlocks[1],initBlocks[3]]
		filtr=BoilerplateBlockFilter()
		isChanged=filtr.process(doc)
		isContent=[block.isContent() for block in doc.getTextBlocks()]
		self.assertEqual(doc.getTextBlocks(),finalBlocks)
		self.assertEqual(isContent,[True,True])
		self.assertEqual(isChanged,True)
		
	def test_minWords(self):
		#rejects if #words<k
		doc=self.makedoc([10,50],None,[True,True])
		self.verifyContent(MinWordsFilter(20),doc,[False,True])

	def test_minClauseWords(self):
		#reject block if max(#words for each clause in block)<k
		doc=self.makedoc(["This is a clause, because it is separated by a comma.","Real short","Lots of, very, very, very, small, clauses.","If acceptClausesWithoutDelimiter is false then clauses that dont end in punctuation dont count"],None,[True,True,True,True])
		self.verifyContent(MinClauseWordsFilter(5,False),doc,[True,False,False,False])

	def test_splitParagraphs(self):
		#split paragraphs intpo separate blocks
		doc=self.makedoc(["A single paragraph.","Multiple paragraphs.\n\nParagraph 2 is here."],None,[True,False])
		filtr=SplitParagraphBlocksFilter()
		isChanged=filtr.process(doc)
		textArr=[block.getText() for block in doc.getTextBlocks()]
		isContent=[block.isContent() for block in doc.getTextBlocks()]
		self.assertEqual(textArr,["A single paragraph.","Multiple paragraphs.","Paragraph 2 is here."])
		self.assertEqual(isContent,[True,False,False])
		self.assertEqual(isChanged,True)

	def test_surroundContent(self):
		#accept block if prev and next blocks are content and condition is met
		doc=self.makedoc([10,20,10,5,10,20,20,10],[0,0,0,5,0,0,0,0],[True,False,True,False,True,False,False,True])
		defaultCondition=lambda tb:tb.getLinkDensity()==0 and tb.getNumWords()>6
		self.verifyContent(SurroundingToContentFilter(defaultCondition),doc,[True,True,True,False,True,False,False,True])

	def test_labelToBoilerplate(self):
		#reject block if it has a particular label
		lb_not=DefaultLabels.STRICTLY_NOT_CONTENT
		lb_maybe=DefaultLabels.MIGHT_BE_CONTENT
		doc=self.makedoc([10,10,10,10],None,[True,True,True,True],[lb_not,lb_maybe,[lb_not,lb_maybe],None])
		self.verifyContent(LabelToBoilerplateFilter(DefaultLabels.STRICTLY_NOT_CONTENT),doc,[False,True,False,True])

	def test_labelToContent(self):
		#accept block if it has a particular label
		lb_not=DefaultLabels.STRICTLY_NOT_CONTENT
		lb_maybe=DefaultLabels.MIGHT_BE_CONTENT
		doc=self.makedoc([10,10,10,10],None,[False,False,False,False],[lb_not,lb_maybe,[lb_not,lb_maybe],None])
		self.verifyContent(LabelToContentFilter(DefaultLabels.MIGHT_BE_CONTENT),doc,[False,True,True,False])


	def test_simpleBlockFusion(self):
		#join blocks with the same number of words per line
		doc=self.makedoc(["two words","three fucking words","another three words"],None,[False,False,False])
		filtr=SimpleBlockFusionProcessor()
		isChanged=filtr.process(doc)
		blockIdxs=[(block.getOffsetBlocksStart(),block.getOffsetBlocksEnd()) for block in doc.getTextBlocks()]
		self.assertEqual(blockIdxs,[(0,0),(1,2)])
		self.assertEqual(isChanged,True)

	def test_contentFusion(self):
		#join blocks with low link density
		filtr=ContentFusion()
		
		#merge
		doc=self.makedoc([10,10],[0,0],[True,False])
		isChanged=filtr.process(doc)
		self.assertEqual(len(doc.getTextBlocks()),1)
		self.assertEqual(isChanged,True)

		#dont merge if tagged not content
		doc=self.makedoc([10,10],[0,0],[True,False],[None,DefaultLabels.STRICTLY_NOT_CONTENT])
		isChanged=filtr.process(doc)
		self.assertEqual(len(doc.getTextBlocks()),2)
		self.assertEqual(isChanged,False)

		#dont merge if link density is high
		doc=self.makedoc([10,10],[0,8],[True,False])
		isChanged=filtr.process(doc)
		self.assertEqual(len(doc.getTextBlocks()),2)
		self.assertEqual(isChanged,False)

		#multiple pass merging
		doc=self.makedoc([10,10,10,10],[0,0,0,0],[True,False,True,False])
		isChanged=filtr.process(doc)
		self.assertEqual(len(doc.getTextBlocks()),1)
		self.assertEqual(isChanged,True)

	def test_labelFusion(self):
		#fuse blocks with identical labels - ONLY LOOKS AT LABELS with markup prefix
		
		lb1=DefaultLabels.MARKUP_PREFIX+".title"
		lb2=DefaultLabels.MARKUP_PREFIX+".menu"
		doc=self.makedoc([10,10,10,10,10,10,10],None,None,[None,None,lb1,lb1,lb2,lb2,[lb1,lb2]])
		filtr=LabelFusion()
		isChanged=filtr.process(doc)
		blockIdxs=[(block.getOffsetBlocksStart(),block.getOffsetBlocksEnd()) for block in doc.getTextBlocks()]
		self.assertEqual(blockIdxs,[(0,1),(2,3),(4,5),(6,6)])
		self.assertEqual(isChanged,True)

	def test_blockProximity(self):
		#fuse blocks close to each other
		doc=self.makedoc([10,10,10,10,10,10,10],None,[False,True,True,True,True,True,False])
		filtr=BlockProximityFusion(1,True,False)
		isChanged=filtr.process(doc)
		blockIdxs=[(block.getOffsetBlocksStart(),block.getOffsetBlocksEnd()) for block in doc.getTextBlocks()]
		self.assertEqual(blockIdxs,[(0,0),(1,5),(6,6)])
		self.assertEqual(isChanged,True)

	def test_largestBlock(self):
		#choose largest block
		doc=self.makedoc([10,10,50,10],None,[False,True,True,True])
		self.verifyContent(KeepLargestBlockFilter(),doc,[False,False,True,False])

	def test_expandTitleToContent(self):
		#marks all between title and content start
		lb1=DefaultLabels.MIGHT_BE_CONTENT
		doc=self.makedoc([10,10,10,10],None,[False,False,False,True],[lb1,[lb1,DefaultLabels.TITLE],lb1,lb1])
		self.verifyContent(ExpandTitleToContentFilter(),doc,[False,True,True,True])

	def test_articleMetadata(self):
		#marks as content and tags blocks with date/time data
		doc=self.makedoc([" May 1, 2009 8:00pm EST","May not be date 1","By Frank Sinatra","By looking at this sentence, you can see there is no author"],None,[False,False,False,False])
		self.verifyContent(ArticleMetadataFilter(),doc,[True,False,True,False])
		labels=[block.getLabels() for block in doc.getTextBlocks()]
		self.assertIn(DefaultLabels.ARTICLE_METADATA,labels[0])

	def test_largestBlock(self):
		#accept largest block and reject all others
		doc=self.makedoc([10,10,50,10],None,[False,True,True,True])
		self.verifyContent(KeepLargestBlockFilter(),doc,[False,False,True,False])

	def test_addPrecedingLabels(self):
		#add prefix+preceding label to each block
		lb1=DefaultLabels.TITLE
		lb2=DefaultLabels.MIGHT_BE_CONTENT
		prefix="^"
		doc=self.makedoc([10,10,10],None,None,[lb1,lb2,None])
		filtr=AddPrecedingLabelsFilter(prefix)
		isChanged=filtr.process(doc)
		labels=[block.getLabels() for block in doc.getTextBlocks()]
		self.assertEqual(labels,[set([lb1]),set([prefix+lb1,lb2]),set([prefix+lb2])])
		self.assertEqual(isChanged,True)
		
	def test_documentTitleMatch(self):
		#add title label to blocks matching sections of the title
		doc=self.makedoc(["News","This is the real title","Red herring"])
		doc.setTitle("News - This is the real title")
		filtr=DocumentTitleMatchClassifier(None,True)
		isChanged=filtr.process(doc)
		labels=[block.getLabels() for block in doc.getTextBlocks()]
		self.assertEqual(labels,[set(),set([DefaultLabels.TITLE]),set()])
		self.assertEqual(isChanged,True)

	def test_minFulltextWords(self):
		#choose largest block
		doc=self.makedoc([10,50],None,[True,True])
		self.verifyContent(MinFulltextWordsFilter(30),doc,[False,True])

	def test_largestFulltextBlock(self):
		#accept largest block that has been marked as content and reject all others
		doc=self.makedoc([10,50,80,10],None,[True,True,False,False])
		self.verifyContent(KeepLargestFulltextBlockFilter(),doc,[False,True,False,False])

	def test_ignoreBlocksAfterContent(self):
		#rejects all blocks after(&including) first block with ENDOFTEXT label
		#Also: ENDOFTEXT labels are ignored until the total number of words in content blocks reaches a certain number
		lb=DefaultLabels.INDICATES_END_OF_TEXT
		doc=self.makedoc([10,30,50,80,20],None,[False,True,True,True,True],[lb,None,None,lb,None])
		self.verifyContent(IgnoreBlocksAfterContentFilter(60),doc,[False,True,True,False,False])

	def test_ignoreBlocksAfterContentFromEnd(self):
		#rejects all blocks with ENDOFTEXT label
		#works backwards until the total number of words in content blocks reaches 200 and then halts
		lb=DefaultLabels.INDICATES_END_OF_TEXT
		doc=self.makedoc([80,80,80,80,80],None,[True,True,True,True,True],[lb,None,None,lb,None])
		self.verifyContent(IgnoreBlocksAfterContentFromEndFilter(),doc,[True,True,True,False,True])

	def test_terminatingBlocks(self):
		#add ENDOFTEXT label at detected beginning of comments section
		lb=DefaultLabels.INDICATES_END_OF_TEXT
		s1="Comments can be the first word of article text.  If there are many words in the block, it is not comments"
		s2="Thanks for your comments - this feedback is now closed"
		doc=self.makedoc(["Comments","Please have your say","48 Comments today",s1,s2])
		filtr=TerminatingBlocksFinder()
		isChanged=filtr.process(doc)
		hasLabel=[(lb in block.getLabels()) for block in doc.getTextBlocks()]
		self.assertEqual(hasLabel,[True,True,True,False,True])
		self.assertEqual(isChanged,True)

	def test_numWordsClassifier(self):
		#accepts or rejects block based on machine-trained decision tree rules
		#using features from previous, current and next block
		filtr=NumWordsRulesClassifier()
		
		doc=self.makedoc([2,10,10],[0,0,0],[True,True,True])
		isChanged=filtr.process(doc)
		#test middle block only
		self.assertEqual(doc.getTextBlocks()[1].isContent(),False)
		
		doc=self.makedoc([10,10,10],[0,0,0],[True,True,True])
		isChanged=filtr.process(doc)
		self.assertEqual(doc.getTextBlocks()[1].isContent(),True)

	def test_densityClassifier(self):
		#accepts or rejects block based on a different set of machine-trained decision tree rules
		#using features from previous, current and next block
		doc=self.makedoc([10,10,5],[10,0,0],[True,True,True])
		isChanged=DensityRulesClassifier().process(doc)
		self.assertEqual(doc.getTextBlocks()[1].isContent(),False)

	def test_canolaClassifier(self):
		#accepts or rejects block based on a different set of machine-trained decision tree rules
		#using features from previous, current and next block
		doc=self.makedoc([5,10,30],[5,10,0],[True,False,True])
		isChanged=CanolaFilter().process(doc)
		self.assertEqual(doc.getTextBlocks()[1].isContent(),True)



class TestParser(unittest.TestCase):
	extractor=Extractor(None)
	defaultWords="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec fermentum tincidunt magna, eu pulvinar mauris dapibus pharetra. In varius, nisl a rutrum porta, sem sem semper lacus, et varius urna tellus vel lorem. Nullam urna eros, luctus eget blandit ac, imperdiet feugiat ipsum. Donec laoreet tristique mi a bibendum. Sed pretium bibendum scelerisque. Mauris id pellentesque turpis. Mauris porta adipiscing massa, quis tempus dui pharetra ac. Morbi lacus mauris, feugiat ac tempor ut, congue tincidunt risus. Pellentesque tincidunt adipiscing elit, in fringilla enim scelerisque vel. Nulla facilisi. ".split(' ')

	def contentitem(self,s):
		if type(s)==int:
			return ' '.join(self.defaultWords[:s])
		else: return s

	def makecontent(self,strArr):
		return [self.contentitem(s) for s in strArr]

	def makedoc(self,template,contentArr):
		templateArr=template.split('*')
		s=""
		for i,j in zip(templateArr[:-1],contentArr):
			s+=i+j
		s+=templateArr[-1]
		doc=self.extractor.parseDoc(s)
		return doc
	
	def test_blocks(self):
		template="<html><body><p>*</p><div>*<p>*</p>*</div></body></html>"
		content=self.makecontent([4,5,6,7])
		doc=self.makedoc(template,content)
		
		blocks=doc.getTextBlocks()
		textArr=[block.getText() for block in blocks]
		numWords=[block.getNumWords() for block in blocks]
		self.assertEqual(textArr,content)
		self.assertEqual(numWords,[4,5,6,7])
	
	def test_anchor(self):
		template="<html><body><p>*</p><div>*<a href='half.html'>*</a></div><a href='full.html'><p>*</p></a></body></html>"
		content=self.makecontent([6,"end with space ",3,6])
		doc=self.makedoc(template,content)
		
		blocks=doc.getTextBlocks()
		textArr=[block.getText() for block in blocks]
		densityArr=[block.getLinkDensity() for block in blocks]
		numAnchorWords=[block.getNumWordsInAnchorText() for block in blocks]
		self.assertEqual(textArr,[content[0],content[1]+content[2],content[3]])
		self.assertEqual(numAnchorWords,[0,3,6])
		self.assertEqual(densityArr,[0.0,0.5,1.0])
	
	def test_title(self):
		titleText="THIS IS TITLE"
		s="<html><head><title>"+titleText+"</title></head><body><p>THIS IS CONTENT</p></body></html>"
		doc=self.extractor.parseDoc(s)
		self.assertEqual(doc.getTitle(),titleText)
	
	def test_body(self):
		bodyText="THIS IS CONTENT"
		s="<html><head><p>NOT IN BODY</p></head><body><p>"+bodyText+"</p></body></html>"
		doc=self.extractor.parseDoc(s)
		textArr=[block.getText() for block in doc.getTextBlocks()]
		self.assertEqual(textArr,[bodyText])
	
	def test_inline(self):
		template="<html><body><div><h1>*</h1><h4>*</h4></div><div><span>*</span><b>*</b></div></body></html>"
		content=['AA','BB','CC','DD']
		doc=self.makedoc(template,content)
		
		blocks=doc.getTextBlocks()
		textArr=[block.getText() for block in blocks]
		numWords=[block.getNumWords() for block in blocks]
		self.assertEqual(textArr,[content[0],content[1],content[2]+content[3]])
	
	def test_ignorable(self):
		template="<html><body><p>*</p><option><p>*</p></option></body></html>"
		content=self.makecontent([10,12])
		doc=self.makedoc(template,content)
		
		blocks=doc.getTextBlocks()
		textArr=[block.getText() for block in blocks]
		self.assertEqual(textArr,[content[0]])

	def assertRange(self,val,minval,maxval):
		self.assertTrue(val>=minval and val<=maxval)

	def test_textDensity(self):
		template="<html><body><p>*</p><p>*</p></body></html>"
		content=self.makecontent([80,"one, !!! two"])
		doc=self.makedoc(template,content)
		
		blocks=doc.getTextBlocks()
		numArr=[[block.getNumWords(),block.numWordsInWrappedLines,block.numWrappedLines,block.getTextDensity()] for block in blocks]
		
		#exact values are unknown, approximate value range to check
		self.assertEqual(blocks[0].getNumWords(),80)
		self.assertRange(blocks[0].numWordsInWrappedLines,60,80)
		self.assertRange(blocks[0].numWrappedLines,4,7)
		self.assertRange(blocks[0].getTextDensity(),8,16)
		
		self.assertEqual(numArr[1],[2,2,1,2])
	
	def test_blockIdxs(self):
		template="<html><body><p>*  </p>  <p> * </p><p>*  </p><p>*  </p></body></html>"
		content=self.makecontent([11,12,13,14])
		doc=self.makedoc(template,content)
		
		blocks=doc.getTextBlocks()
		idxArr=[[block.getOffsetBlocksStart(),block.getOffsetBlocksEnd()] for block in blocks]
		self.assertEqual(idxArr,[[0,0],[1,1],[2,2],[3,3]])
	
	def test_tagLevel(self):
		template="<html><body><div><p><span><a href='x.html'>*</a></span></p>*</div></body></html>"
		content=self.makecontent([5,6])
		doc=self.makedoc(template,content)
		
		blocks=doc.getTextBlocks()
		levelArr=[block.getTagLevel() for block in blocks]
		self.assertEqual(levelArr,[5,3])
	
	def test_merge(self):
		block1=TextBlock("AA BB CC ",set([0]),3,3,3,1,0)
		block2=TextBlock("DD EE FF GG HH II JJ .",set([1]),6,0,6,2,1)
		block1.addLabels(DefaultLabels.MIGHT_BE_CONTENT)
		block2.addLabels(DefaultLabels.ARTICLE_METADATA)
		block1.mergeNext(block2)
		self.assertEqual(block1.getText(),"AA BB CC \nDD EE FF GG HH II JJ .")
		self.assertEqual(block1.getNumWords(),9)
		self.assertEqual(block1.getNumWordsInAnchorText(),3)
		self.assertAlmostEqual(block1.getLinkDensity(),1.0/3.0)
		self.assertEqual(block1.getTextDensity(),3)
		self.assertEqual(block1.getLabels(),set([DefaultLabels.MIGHT_BE_CONTENT,DefaultLabels.ARTICLE_METADATA]))
		self.assertEqual(block1.getOffsetBlocksStart(),0)
		self.assertEqual(block1.getOffsetBlocksEnd(),1)

runTests()
