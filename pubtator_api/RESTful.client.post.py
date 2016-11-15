import urllib2
import time
import sys
import getopt

inputfile = ''
trigger = ''
taxonomy = ''
email = ''
PubTator_username = ''
url_Submit = ''

try:
	options, remainder = getopt.getopt(sys.argv[1:], 'i:t:x:e:', ['inputfile=','trigger=','taxonomy=','email='])
except getopt.GetoptError, err:
	print "\npython RESTful.client.post.py -i [inputfile] -t [trigger:tmChem|DNorm|tmVar|GNormPlus] -e [E-mail](optional)\n"
	print "\npython RESTful.client.post.py -i [inputfile] -t GNormPlus -x [taxonomy]\n"
	sys.exit(0)
														 
for opt, arg in options:
	if opt in ('-i', '--inputfile'):
		inputfile = arg
	elif opt in ('-t', '--trigger'):
		trigger = arg
	elif opt in ('-x', '--taxonomy'):
		taxonomy = arg
	elif opt in ('-e', '--PubTator'):
		email = arg

#Submit

if taxonomy != '':
	url_Submit = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/" + trigger + "/" + taxonomy + "/"
elif email != '':
	url_Submit = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/" + trigger + "/Submit:" + email + "/"
else:
	url_Submit = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/" + trigger + "/Submit/"

fh = open(inputfile)
InputSTR=''
for line in fh:
	InputSTR = InputSTR + line

urllib_submit = urllib2.urlopen(url_Submit, InputSTR)
urllib_result = urllib2.urlopen(url_Submit, InputSTR)
SessionNumber = urllib_submit.read()

if PubTator_username != '':
	print "Thanks for your submission (Session number: " + SessionNumber + ").\nThe result will be sent to your E-mail: " + email + ".\n"
else:
	print "Thanks for your submission. The session number is : "+ SessionNumber + "\n"
	print "\nThe request is received and processing....\n\n"
	#Receive
	url_Receive = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/" + SessionNumber + "/Receive/"
	
	code=404
	while(code == 404 or code == 501):
		time.sleep(5)
		try:
			urllib_result = urllib2.urlopen(url_Receive)
		except urllib2.HTTPError as e:
			code = e.code
		except urllib2.URLError as e:
			code = e.code
		else:
			code = urllib_result.getcode()

	print urllib_result.read()
