[Directory]
A. Client side program
B. Input file format
C. Output file format
D. Tools available
E. Reference

#======================================================================================#
A. [Client side program]

	We provided three client programs by different languages (i.e., java, python, and perl) to access whole PubMed pre-annoation and our text mining tools(e.g., tmChem).
	
	[PERL]
	Instruction:
		perl RESTful.client.POST.pl [Input file] [Trigger:tmChem|tmVar|DNorm|GNormPlus] Submit:[E-mail](optional)
		perl RESTful.client.POST.pl [Input file] GNormPlus [taxonomy ID]
	Example:
		$ perl RESTful.client.POST.pl input.json tmChem
		$ perl RESTful.client.POST.pl input.json tmChem Submit:test@gmail.com
		$ perl RESTful.client.POST.pl input.json GNormPlus 10090

	[JAVA]
		Instruction:
			java RESTClientPost [Input file] [Trigger:tmChem|tmVar|DNorm|GNormPlus] Submit:[E-mail](optional)
			java RESTClientPost [Input file] GNormPlus [taxonomy ID]
		Example:
			$ javac RESTClientPost.java
			$ java RESTClientPost input.json tmChem
			$ java RESTClientPost input.json tmChem Submit:test@gmail.com
			$ java RESTClientPost input.json GNormPlus 10090

	[PYTHON]
		Instruction:
			python RESTful.client.post.py -i [Input file] -t [Trigger:tmChem|tmVar|DNorm|GNormPlus] -e [E-mail](optional)
			python RESTful.client.post.py -i [Input file] -t GNormPlus -x [taxonomy ID]
		Example:
			$ python RESTful.client.post.py -i input.json -t tmChem
			$ python RESTful.client.post.py -i input.json -t tmChem -e test@gmail.com
			$ python RESTful.client.post.py -i input.json -t GNormPlus -x 10090
	
	[Input file]: The input file should follow PubTator format, or list of PMID.
	[Trigger]: tmChem, tmVar, DNorm or GNormPlus
	[taxonomy ID]: NCBI Taxonomy identifier. The species you would like to focus on. Only avaliable for GNormPlus.
	[E-mail]: E-mail. Only parameter is submitted, the result will send to your PubTator registered E-mail when finished.
	
b. [Input file format]

	This RESTful API allows four different formats: PubTator, BioC, PubAnnotation(JSON), and PMID list
	
	BioC Format: http://bioc.sourceforge.net/
	
	PubAnnotation: http://pubannotation.org/
	
	PubTator Format: (Keep a blank line between any two articles)
	
		<PMID1>|t|<TITLE>
		<PMID1>|a|<ABSTRACT>
		<PMID1>	<START>	<LAST>	<MENTION>	<TYPE>	<Normalized Form>
		
		<PMID2>|t|<TITLE>
		<PMID2>|a|<ABSTRACT>
		<PMID2>	<START>	<LAST>	<MENTION>	<TYPE>	<Normalized Form>
		...
		
		Example: 
		10022127|t|TIF1gamma, a novel member of the transcriptional intermediary factor 1 family.
		10022127|a|We report the cloning and characterization of a novel member of the Transcriptional Intermediary Factor 1 (TIF1) gene family, human TIF1gamma. Similar to TIF1alpha and TIF1beta, the structure of TIF1beta is characterized by multiple domains: RING finger, B boxes, Coiled coil, PHD/TTC, and bromodomain. Although structurally related to TIF1alpha and TIF1beta, TIF1gamma presents several functional differences. In contrast to TIF1alpha, but like TIF1beta, TIF1 does not interact with nuclear receptors in yeast two-hybrid or GST pull-down assays and does not interfere with retinoic acid response in transfected mammalian cells. Whereas TIF1alpha and TIF1beta were previously found to interact with the KRAB silencing domain of KOX1 and with the HP1alpha, MODI (HP1beta) and MOD2 (HP1gamma) heterochromatinic proteins, suggesting that they may participate in a complex involved in heterochromatin-induced gene repression, TIF1gamma does not interact with either the KRAB domain of KOX1 or the HP1 proteins. Nevertheless, TIF1gamma, like TIF1alpha and TIF1beta, exhibits a strong silencing activity when tethered to a promoter. Since deletion of a novel motif unique to the three TIF1 proteins, called TIF1 signature sequence (TSS), abrogates transcriptional repression by TIF1gamma, this motif likely participates in TIF1 dependent repression.

		10072587|t|Cloning of a novel gene (ING1L) homologous to ING1, a candidate tumor suppressor.
		10072587|a|The ING1 gene encodes p33(ING1), a putative tumor suppressor for neuroblastomas and breast cancers, which has been shown to cooperate with p53 in controlling cell proliferation. We have isolated a novel human gene, ING1L, that potentially encodes a PHD-type zinc-finger protein highly homologous to p33(ING1). Fluorescence in situ hybridization and radiation-hybrid analyses assigned ING1L to human chromosome 4. Both ING1 and ING1L are expressed in a variety of human tissues, but we found ING1L expression to be significantly more pronounced in tumors from several colon-cancer patients than in normal colon tissues excised at the same surgical sites. Although the significance of this observation with respect to carcinogenesis remains to be established, the data suggest that ING1L might be involved in colon cancers through interference with signal(s) transmitted through p53 and p33(ING1).

		10072769|t|Selection of cDNAs encoding putative type II membrane proteins on the cell surface from a human full-length cDNA bank.
		10072769|a|We have developed a simple method to test whether a hydrophobic segment near the N-terminus of a protein functions as a type II signal anchor (SA) in which the N-terminus faces the cytoplasm. A cDNA fragment containing the putative SA sequence of a target clone was fused in-frame to the 5' end of a cDNA fragment encoding the protease domain of urokinase-type plasminogen activator (u-PA). The resulting fused gene was expressed in COS7 cells. Fibrinolytic activity on the cell surface was measured by placing a fibrin sheet in contact with the transfected COS7 cells after removing the medium. When the cDNA fragment encoded a SA, the fibrin sheet was lysed by the u-PA expressed on the cell surface. The fibrinolytic activity was not detected in the culture medium, suggesting that the u-PA remains on the cell surface anchored via the SA in the membrane without being cleaved by signal peptidase. This fibrin sheet method was successfully applied to select five novel cDNA clones encoding putative type II membrane proteins from a human full-length cDNA bank.
		

	PMID list format:
	
		<PMID1>
		<PMID2>
		<PMID3>
		<PMID4>
		<PMID5>
		....
		
		Example:
		10022127
		10072587
		10072769
		10092817
		10192385

C. [Output file format]

	Three different formats are allowed to export: PubTator, BioC, and JSON(refer to PubAnnotation)
	
	BioC Format: http://bioc.sourceforge.net/
	
	PubAnnotation: http://pubannotation.org/
	
	PubTator Format:
	
		<PMID1>|t|<TITLE>
		<PMID1>|a|<ABSTRACT>
		<PMID1>	<START>	<LAST>	<MENTION>	<TYPE>	<Normalized Form>
		
		<PMID2>|t|<TITLE>
		<PMID2>|a|<ABSTRACT>
		<PMID2>	<START>	<LAST>	<MENTION>	<TYPE>	<Normalized Form>
		...
		
		Example: 
		10022127|t|TIF1gamma, a novel member of the transcriptional intermediary factor 1 family.
		10022127|a|We report the cloning and characterization of a novel member of the Transcriptional Intermediary Factor 1 (TIF1) gene family, human TIF1gamma. Similar to TIF1alpha and TIF1beta, the structure of TIF1beta is characterized by multiple domains: RING finger, B boxes, Coiled coil, PHD/TTC, and bromodomain. Although structurally related to TIF1alpha and TIF1beta, TIF1gamma presents several functional differences. In contrast to TIF1alpha, but like TIF1beta, TIF1 does not interact with nuclear receptors in yeast two-hybrid or GST pull-down assays and does not interfere with retinoic acid response in transfected mammalian cells. Whereas TIF1alpha and TIF1beta were previously found to interact with the KRAB silencing domain of KOX1 and with the HP1alpha, MODI (HP1beta) and MOD2 (HP1gamma) heterochromatinic proteins, suggesting that they may participate in a complex involved in heterochromatin-induced gene repression, TIF1gamma does not interact with either the KRAB domain of KOX1 or the HP1 proteins. Nevertheless, TIF1gamma, like TIF1alpha and TIF1beta, exhibits a strong silencing activity when tethered to a promoter. Since deletion of a novel motif unique to the three TIF1 proteins, called TIF1 signature sequence (TSS), abrogates transcriptional repression by TIF1gamma, this motif likely participates in TIF1 dependent repression.
		10022127	0	9	TIF1gamma	Gene	51592
		10022127	211	220	TIF1gamma	Gene	51592
		10022127	233	242	TIF1alpha	Gene	8805
		...

D. [Tools avaliable]
	
	http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/tmTools/

