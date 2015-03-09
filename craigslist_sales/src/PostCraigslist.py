#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import traceback
import random
import os
import time
from datetime import datetime
from datetime import timedelta

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium import *

from EmailList import *
from AdsList import *
from PersonalInformation import *
import ScamMysql
import EmailHandler


class Craigslist:
	def __init__(self, adDic, emailDic, emailHandler):
		# MySQL instance
		self.mysqlInstance = mysqlInstance

		# email handler
		self.emailHandler = emailHandler

		# email information
		self.email = emailDic["EMAIL"]
		self.craigsAccount = emailDic["CRAIGSLIST_ACCOUNT"]
		self.password = emailDic["PASSWD"]
		self.phone = emailDic["PHONE"]
		# city information
		self.city = emailDic["ID"]
		self.cityName = emailDic["CITY"]
		self.nameMode = emailDic["NAME"]
		self.mediumMode = emailDic["MEDIUM"]

		# Ad information
		self.category = adDic["CATEGORY"]
		self.title = adDic["TITLE"] + " (" + emailDic["CITY"] + ")"
		self.content = adDic["CONTENTS"]
		# Add sentences according to the selected mode.
		self.content = self.modifyContent(self.content, self.nameMode, self.mediumMode)
		self.adURL = ''

		print self.content

		# Goods
		self.price = adDic["PRICE"]
		self.imageFile = os.path.dirname(os.path.realpath(__file__)) + '/pics/' + adDic["PICTURE"]
		self.categoryDic = categoryDic;


		# Create a new instance of the Chrome driver
		if 'PROXY' in emailDic:
			self.proxy = emailDic['PROXY']
		else:
			self.proxy = None

	# end def __init__()

	def setupWebdriver(self):
		if self.proxy:
			options = webdriver.ChromeOptions()
			options.add_argument('--proxy-server=%s' % self.proxy)

			self.driver = webdriver.Chrome(chrome_options=options)
			print '\tproxy: %s' % self.proxy
		else:
			self.driver = webdriver.Chrome()

		# endif

	'''
	def login(self):
		self.driver.get("https://accounts.craigslist.org/login")
		self.sendKeyToElement("input", "name", "inputEmailHandle", self.email)
		self.sendKeyToElement("input", "name", "inputPassword", self.password)
		self.clickElement("button", "type", "submit")
		self.driver.implicitly_wait(5)
	# end def login()
	'''

	def postGoodsCraigslist(self):
		self.setupWebdriver()

		# load Craigslist post page
		print '\t\t0'
		self.driver.get("https://post.craigslist.org")

		self.clickElement("option", "value", self.city)
		self.clickElement("button", "value", "Continue")

		# page 1: select type of posting
		print '\t\t1'
		self.clickElement("input", "value", "fso")

		# page 2: select category
		self.clickElement("input", "value", self.categoryDic[self.category])
		print '\t\t2'

		# page 3: click the first area (may not exist)
		self.clickElement("input", "value", "1", True)
		print '\t\t3'

		# page 4: click "bypass this step" for the best fitting locating (may not exist)
		#self.clickElement("input", "value", "0", True)
		#print '\t\t4'

		# page 5: set text inputs and click "Continue"
		self.sendKeyToElement("input", "id", "FromEMail", self.email)
		self.sendKeyToElement("input", "id", "ConfirmEMail", self.email)
		self.sendKeyToElement("input", "id", "PostingTitle", self.title)
		self.sendKeyToElement("input", "id", "Ask", self.price)
		self.sendKeyToElement("input", "id", "postal_code", "00000")
		self.sendKeyToElement("textarea", "id", "PostingBody", self.content)

		if self.mediumMode == "phone":
			self.clickElement("input", "id", "A")
		if self.mediumMode == "phone" or self.mediumMode == "both":
			self.clickElement("input", "id", "contact_phone_ok")
			self.clickElement("input", "id", "contact_text_ok")
			self.sendKeyToElement("input", "id", "contact_phone", self.phone)

		self.clickElement("button", "value", "Continue")
		print '\t\t5'

		# page 5.5: do not include map
		self.clickElement("button", "class", "skipmap")
		print '\t\t5.5'

		# page 6: "Images"
		self.clickElement("a", "id", "classic", flagOptional=True)
		time.sleep(2)
		self.sendKeyToElement("input", "type", "file", self.imageFile)
		time.sleep(10)
		self.clickElement("button", "value", "Done with Images")
		print '\t\t6'

		# page 7: "Publish"
		self.clickElement("button", "value", "Continue")
		print '\t\t7'

		# Done.

	# end def postGoodsCraigslist()


	def modifyContent(self, content, nameMode, mediumMode):
		print "\tExperimental Condition: NAME(%s), MEDIUM(%s)" % (nameMode, mediumMode)

		content += "\n"
		nameSentence = ["My name is ", "Please find ", "I am ", "Note that my name is ", "Find "]
		if nameMode.lower() == "female":
			index = random.randint(0, 300)
			firstName = open('./data/female_name_first.txt', 'r').readlines()[index].split(" ")[0]
			firstName = firstName[0].upper() + firstName[1:].lower()
			content += nameSentence[random.randint(0, len(nameSentence) - 1)] + firstName + ". "
		elif nameMode.lower() == "male":
			index = random.randint(0, 300)
			firstName = open('./data/male_name_first.txt', 'r').readlines()[index].split(" ")[0]
			firstName = firstName[0].upper() + firstName[1:].lower()
			content += nameSentence[random.randint(0, len(nameSentence) - 1)] + firstName + ". "

		phoneSentence = ["Please text or call me if you are interested!\n",
										 "Text or call me if you are interested in buying.\n",
										 "Text/call me for further information.\n",
										 "Please text/call me for further information.\n",
										 "Text/call me if you wnat more information.\n",
										 "Please text/call me if you wnat more information.\n",
										 "Please use my phone number to reach me.\n",
										 "Use my phone number to reach me.\n",
										 "Please refer to my phone number to reach me.\n",
										 "Refer to my phone number to reach me.\n",
		]
		bothSentence = ["Please email, text or call me if you are interested!\n",
										"Email, Text or call me if you are interested in buying.\n",
										"Email/Text/call me for further information.\n",
										"Please email/text/call me for further information.\n",
										"Email/text/call me if you wnat more information.\n",
										"Please email/text/call me if you wnat more information.\n",
										"Please use my email or phone number to reach me.\n",
										"Use my mail or phone number to reach me.\n",
										"Please refer to my email address or phone number to reach me.\n",
										"Refer to my email or phone number to reach me.\n",
		]

		emailSentence = ["Please email me if you are interested!\n",
										 "Email me if you are interested in buying.\n",
										 "Email me for further information.\n",
										 "Please email me for further information.\n",
										 "Email me if you wnat more information.\n",
										 "Please email me if you wnat more information.\n",
										 "Please use my email address to reach me.\n",
										 "Use my email address to reach me.\n",
										 "Please refer to my email address to reach me.\n",
										 "Refer to my email to reach me.\n",
		]
		if mediumMode.lower() == "phone":
			content += phoneSentence[random.randint(0, len(phoneSentence) - 1)]
		elif mediumMode.lower() == "both":
			content += bothSentence[random.randint(0, len(bothSentence) - 1)]
		elif mediumMode.lower() == "email":
			content += emailSentence[random.randint(0, len(emailSentence) - 1)]

		return content


	def confirmEmail(self):
		waitTime = 5
		print '\twait %d seconds for confirmation email...' % waitTime
		time.sleep(waitTime)

		while True:
			if self.confirmGmail():
				break
			else:
				print '\tanother 10 seconds....'
				time.sleep(10)
				#end while

	#end def

	def confirmGmail(self):
		confirmLink = self.emailHandler.readCraigslistConfirmEmail(self.email)

		if confirmLink == None:
			return False

		# go to confirmation page
		self.setupWebdriver()
		self.driver.get(confirmLink)

		# click agree term
		self.clickElement("button", "type", "submit")

		# get a link to the ad.
		linkList = self.driver.find_elements_by_partial_link_text('http://')

		for link in linkList:
			if ('post.craigslist.org' in link.text) or ('accounts.craigslist.org' in link.text):
				continue
			else:
				self.adURL = link.text
				break
				#end if
		#end for

		return True

	#end def

	'''
	def testFunction(self):
		# go to confirmation page
		self.setupWebdriver()
		self.driver.get('https://post.craigslist.org/k/vMkaVua74hGlfyB3vp2Eww/7amq3?s=redirect')

		# get a link to the ad.
		linkList = self.driver.find_elements_by_partial_link_text('http://')

		self.adURL = ''

		for link in linkList:
			if ('post.craigslist.org' in link) or ('accounts.craigslist.org' in link):
				continue
			else:
				self.adURL = link


		print self.adURL
		sys.exit()
	#end def
	'''


	def insertDB(self, verified=True):
		adDic = {}

		adDic['Email'] = self.email
		adDic['BaseAccount'] = self.craigsAccount
		adDic['Category'] = self.category
		adDic['Subject'] = self.title
		adDic['Price'] = self.price
		adDic['City'] = self.cityName
		adDic['URL'] = self.adURL
		adDic['NameMode'] = self.nameMode
		adDic['MediumMode'] = self.mediumMode
		adDic['Content'] = self.content

		if verified == True:
			adDic['Status'] = 'Verified'
		else:
			adDic['Status'] = 'NotVerified'
		self.mysqlInstance.insertCraigslistAd(adDic)

	def done(self):
		self.driver.quit()

	# end def done()


	def clickElement(self, inputType, category, categoryValue, flagOptional=False, flagContains=False):
		if flagContains == False:
			xpath = "//%s[@%s='%s']" % (inputType, category, categoryValue)
		else:
			xpath = "//%s[contains(@%s, '%s')]" % (inputType, category, categoryValue)

		try:
			inputElement = WebDriverWait(self.driver, 10).until(lambda driver: self.driver.find_element_by_xpath(xpath))
		except TimeoutException:
			if flagOptional == False:
				traceback.print_exc(file=sys.stdout)
				sys.exit()
		else:
			inputElement.click()

	# end def clickButtonByValue()


	def sendKeyToElement(self, inputType, category, targetCategory, inputText, flagOptional=False):
		xpath = "//%s[@%s='%s']" % (inputType, category, targetCategory)

		try:
			inputElement = WebDriverWait(self.driver, 10).until(lambda driver: self.driver.find_element_by_xpath(xpath))
		except TimeoutException:
			if flagOptional == False:
				traceback.print_exc(file=sys.stdout)
				sys.exit()
		else:
			inputElement.send_keys(inputText)
			# end def clickRadioButtonByValue()


# end class Craigslist



def getRandomEmailIndexList(targetCity, mysqlInstance):
	# targetEmailList = [email for email in emailList if email['CITY'] == targetCity and ('STATUS' not in email.keys() or email['STATUS'] != 'Blocked')]
	#print len(targetEmailList), targetEmailList

	availableEmailIndexList = []
	allEmailIndexList = random.sample(range(len(emailList)), len(emailList))

	for emailIndex in allEmailIndexList:
		if emailList[emailIndex]['CITY'] != targetCity:
			continue
		if 'STATUS' in emailList[emailIndex] and emailList[emailIndex]['STATUS'] == 'Blocked':
			continue

		lastPostingTime = mysqlInstance.checkCraigslistAccountAvailability(emailList[emailIndex]["CRAIGSLIST_ACCOUNT"])

		if (lastPostingTime) and (datetime.datetime.utcnow() < lastPostingTime + timedelta(hours=56)):
			#print 'remove %d: used within the last 48 hours' % emailIndex
			continue
		#endif

		availableEmailIndexList.append(emailIndex)
	#end for

	print availableEmailIndexList
	print '%d Craigslist accounts are available' % len(availableEmailIndexList)

	if len(availableEmailIndexList) < 1:
		print 'halt'
		sys.exit()
	else:
		print "Available emailNum", len(availableEmailIndexList)
		return availableEmailIndexList
		#end if


# end def


def getRandomAdIndexList(targetCity, mysqlInstance):
	adIndexList = random.sample(range(len(goodsAdsList)), len(goodsAdsList))

	unavailableEmailIndexList = []
	unavailableAdTitleList = mysqlInstance.getRecentAds(targetCity)
	if unavailableAdTitleList:
		for i in range(len(goodsAdsList)):
			for subject in unavailableAdTitleList:
				if goodsAdsList[i]['TITLE'] in subject:
					unavailableEmailIndexList.append(i)
		adIndexList = list(set(random.sample(range(len(goodsAdsList)), len(goodsAdsList))) - set(unavailableEmailIndexList))

	return adIndexList

#end def



def checkAvailableHour(mysqlInstance):
	availableHourList = mysqlInstance.getCraiglistAvailableHourList()

	print 'availableHourList'
	print availableHourList

	if len(availableHourList) > 0 and datetime.datetime.utcnow().hour not in availableHourList:
		print 'Not available hour: %d' % datetime.datetime.utcnow().hour
		sys.exit()
	else:
		print 'Available hour: %d' % datetime.datetime.utcnow().hour

#end def





if __name__ == '__main__':
	_TEST_ = False

	#################################
	# Post goods ads
	#################################
	print 'argv:%s\n' % sys.argv
	if len(sys.argv) == 2:
		targetCity = sys.argv[1]
	else:
		print './PostCraigslist.py <City>'
		sys.exit()
	# end if

	# mysql
	mysqlInstance = ScamMysql.ScamMysql()
	mysqlInstance.connect()

	# check if it is good time to post Craigslist ads
	checkAvailableHour(mysqlInstance)

	# name generator
	#personalInformation = PersonalInformation()

	# build emailIndexList
	if len(sys.argv) <= 2:
		emailIndexList = getRandomEmailIndexList(targetCity, mysqlInstance)
	else:
		emailIndexList = list(range(len(emailList)))
	#endif

	# build adIndexList
	adIndexList = getRandomAdIndexList(targetCity, mysqlInstance)

	print emailIndexList
	print adIndexList


	for emailIndex, adIndex in zip(emailIndexList, adIndexList):
		print emailIndex, adIndex

		print '*********************************************'
		print '%d, EmailAccount: %s, CraigslistAccount:%s' \
					% (emailIndex, emailList[emailIndex]['EMAIL'], emailList[emailIndex]['CRAIGSLIST_ACCOUNT'])

		print '    Ad %d, %s, %s' \
					% (adIndex, goodsAdsList[adIndex]['TITLE'], goodsAdsList[adIndex]['CATEGORY'])


		# Gmail IMAP login
		emailHandler = EmailHandler.EmailHandler(email_dic=emailList[emailIndex])
		if not emailHandler.login(ImapOnly=True):
			sys.exit()

		craigslist = Craigslist(goodsAdsList[adIndex], emailList[emailIndex], emailHandler)

		if not _TEST_:
			# Post Craigslist AD
			craigslist.postGoodsCraigslist()
			# Close webdriver
			craigslist.done()
			# Confirm email
			craigslist.confirmEmail()

		# If confirmation is successful, insert into DB
		if craigslist.adURL != '':
			print '\tinsert into DB...'
			craigslist.insertDB(verified=True)
		else:
			print '\tnon-verified craigslist account...'
			craigslist.insertDB(verified=False)
			sys.exit()
		#endif

		# close webdriver
		craigslist.done()

		# Wait random time
		randTime = random.randint(45, 90)
		print '\twaiting %d seconds...' % randTime
		time.sleep(randTime)
		#end

		# email hander logout
		emailHandler.logout()
		# use only one email
		if _TEST_:
			break

	#end for

	# mysql
	mysqlInstance.disconnect()