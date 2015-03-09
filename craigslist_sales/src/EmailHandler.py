#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import re
import datetime
import csv
import random
import time
import imaplib
import smtplib
import mimetypes
import email

from dateutil import parser

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEAudio import MIMEAudio
from email.MIMEImage import MIMEImage
from email.Encoders import encode_base64
import PersonalInformation
import CommonDef
import ScamMysql
import Utils
from EmailList import emailList
import LocalDef


class EmailHandler:
	def __init__(self, email_dic=None, TEST_FLAG=False):
		self.smtpServer = smtplib.SMTP('smtp.gmail.com', 587)
		self.imapServer = imaplib.IMAP4_SSL("imap.gmail.com")
		self.webServer = 'http://54.152.213.228'

		self.mysql = ScamMysql.ScamMysql(TEST=TEST_FLAG)
		self.mysql.connect()
		self.pi = PersonalInformation.PersonalInformation()
		self.TEST_FLAG = TEST_FLAG
		self.email_dic = email_dic


	def login(self, ImapOnly=False):
		print 'Gmail IMAP login (%s, %s)' % (self.email_dic['EMAIL'], self.email_dic['PASSWD'])
		try:
			self.imapServer.login(self.email_dic['EMAIL'], self.email_dic['PASSWD'])
		except Exception as e:
			print e
			print 'login failed'
			print sys.exc_info()
			return False

		self.ImapOnly = ImapOnly
		if ImapOnly == True:
			return True

		print 'Gmail SMTP login (%s, %s)' % (self.email_dic['EMAIL'], self.email_dic['PASSWD'])
		self.smtpServer.ehlo()
		self.smtpServer.starttls()
		self.smtpServer.ehlo()
		try:
			self.smtpServer.login(self.email_dic['EMAIL'], self.email_dic['PASSWD'])
		except:
			print 'smtp login failed'
			print sys.exc_info()
			return False

		return True

	def logout(self):
		try:
			self.imapServer.logout()
		except:
			print 'logout not necessary'
		if self.ImapOnly == False:
			self.smtpServer.quit()


	#########################################################
	#
	# Handle Craigslist Confirmation Email
	#
	#########################################################
	def readCraigslistConfirmEmail(self, emailAccount):
		print '\tReading Craigslist confirm email..'

		# emailAccount  = "tracysankar74+vincentschumann@gmail.com"

		# Open inbox					
		while True:
			self.imapServer.select('INBOX')
			status, data = self.imapServer.search(None, '(UNSEEN)')
			emailIds = data[0].split()
			if len(emailIds):
				latest_email_id = int(emailIds[-1])
				break
			else:
				print '\tNo new email yet.. wait another 5 seconds...'
				time.sleep(5)
				continue
		#end while

		for i in emailIds:
			typ, data = self.imapServer.fetch(i, '(BODY.PEEK[])')
			email_message = email.message_from_string(data[0][1])
			payload = self.getFirstTextPayload(email_message)

			#print '++++++++++++++++++++++++++++++++++++++++++++++++++++'
			#print email_message

			if email_message['To'] != emailAccount:
				continue

			print '\tFound Craigslist confirm email..'

			if payload:
				for line in payload.splitlines():
					if 'https://post.craigslist.org/' in line:
						typ, data = self.imapServer.fetch(i, '(RFC822)')
						return line
		#end for

		return None



	#########################################################
	#
	# IMAP: Read unseen emails
	#
	#########################################################
	def read_emails(self):
		# Open inbox
		self.imapServer.select('INBOX')

		# Count the unread emails
		status, data = self.imapServer.status('INBOX', "(UNSEEN)")
		unreadCount = int(data[0].split()[2].strip(').,]'))

		if unreadCount == 0:
			print 'No unread emails left'
			return

		status, uids = self.imapServer.uid('search', None, "UNSEEN")
		if status != 'OK':
			self.logout()
			sys.exit()
		else:
			uidList = uids[0].split()

		# Handle each unread email
		for uid in uidList:
			self.emailInfo = {}

			print '==================================================='
			print 'IMAP:' + uid
			self.emailInfo['UID'] = uid

			# fetch the email body (RFC822) for the given ID
			#if self.TEST_FLAG:
			status, data = self.imapServer.uid('fetch', uid, '(BODY.PEEK[])')
			#else:
			#	status, data = self.imapServer.uid('fetch', uid, '(RFC822)')

			email_message = email.message_from_string(data[0][1])

			# Receiver information
			self.emailInfo['To'] = email_message['To']
			self.emailInfo['ReceiverName'], self.emailInfo['ReceiverEmail'] = email.utils.parseaddr(email_message['To'])

			# Sender information
			self.emailInfo['From'] = email_message['From']
			self.emailInfo['SenderName'], self.emailInfo['SenderEmail'] = email.utils.parseaddr(email_message['From'])
			# Reply-to information
			replyToName, self.emailInfo['Reply-To'] = email.utils.parseaddr(email_message['Reply-To'])
			# Actual mail sender
			realSenderName, self.emailInfo['RealSenderEmail'] = email.utils.parseaddr(email_message['Sender'])

			# Get the IP address of the sender
			wholeSenderEmail = email_message['From']
			if email_message['Sender']:
				wholeSenderEmail += email_message['Sender']

			if 'gmail.com' not in wholeSenderEmail and 'hotmail.com' not in wholeSenderEmail and 'outlook.com' not in wholeSenderEmail:
				senderInfo = email_message.get_all('Received')[-1]
				try:
					self.emailInfo['SenderIP'] = re.findall(r'[0-9]+(?:\.[0-9]+){3}', senderInfo)[0]
				except:
					self.emailInfo['SenderIP'] = ''
			else:
				self.emailInfo['SenderIP'] = ''


			# Email details
			self.emailInfo['Subject'] = email_message['Subject']
			if self.emailInfo['Subject'] is None:
				print 'null subject'
				continue

			if '=?utf-8?' in self.emailInfo['Subject']:
				self.emailInfo['Subject'], encoding = email.Header.decode_header(self.emailInfo['Subject'])[0]
				print 'decode utf-8 subject: %s' % self.emailInfo['Subject']

			timeUTC = parser.parse(email_message['Date']).utctimetuple()
			self.emailInfo['Date'] = datetime.datetime(*timeUTC[:6]).strftime('%Y-%m-%d %H:%M:%S')
			self.emailInfo['MessageID'] = email_message['Message-ID']
			self.emailInfo['References'] = email_message['References']

			# Thread ID
			result, data = self.imapServer.uid('fetch', uid, '(X-GM-THRID X-GM-MSGID)')
			self.emailInfo['ThreadID'] = data[0].split()[2]

			# Email payload
			self.emailInfo['Payload'] = self.getFirstTextPayload(email_message)
			self.emailInfo['CorePayload'] = self.removeQuotes(self.emailInfo['Payload'])

			print '=========================='
			print self.emailInfo['Subject']
			print self.emailInfo['Payload']
			print '=========================='
			payload = self.emailInfo['Payload'].lower()


			# validation
			if 'POST/EDIT/DELETE' in self.emailInfo['Subject']:
				print 'INVALID: CRAIGSLIST EMAIL'
				continue
			elif 'google.com' in self.emailInfo['From']:
				print 'INVALID: GOOGLE EMAIL'
				self.imapServer.uid('fetch', uid, '(RFC822)')
				continue

			# classification
			if 'paypal' in self.emailInfo['SenderEmail'].lower() \
					or 'paypal' in self.emailInfo['SenderName'].lower() \
					or 'pay pal' in self.emailInfo['SenderName'].lower() \
					or 'payment' in self.emailInfo['Subject'].lower():
				print 'paypal notification'
				self.emailInfo['Type'] = 'paypal'
				self.mysql.insertReceivedPaypalNoti(self.emailInfo)
			else:
				replyPayload = self.generateReply(self.emailInfo['CorePayload'])
				if replyPayload == '':
					self.emailInfo['Type'] = 'unknown'
					print '--------------------------'
					print 'Insert received unknown email into Mysql'
					print '--------------------------'
					self.mysql.insertUnknown(self.emailInfo)
				else:
					self.emailInfo['Type'] = 'conversation'
					print '--------------------------'
					print 'Insert received conversation into Mysql'
					self.mysql.insertReceivedConversation(self.emailInfo)
					print 'Send Reply'
					self.sendReply(self.emailInfo, replyPayload)
					print '--------------------------'
			#endif

			if self.TEST_FLAG:
				return
			else:
				self.imapServer.uid('fetch', uid, '(RFC822)')
			#endfor
		#end def



	#########################################################
	#
	#	Send reply email to scammer
	#
	#########################################################
	def sendReply(self, emailInfo, replyPayload):
		self.emailInfo = emailInfo

		replyEmail = MIMEMultipart()

		# Embed an image
		replyImagePayload = self.generateReplyImage()

		# Extract email from payload
		embeddedEmailAddress = self.extractEmailAddress(self.emailInfo['CorePayload'])

		#print '=========================='
		#print replyPayload
		#print replyImagePayload
		#print '=========================='

		# Reply email header
		replyEmail['Message-ID'] = email.utils.make_msgid()
		replyEmail['In-Reply-To'] = self.emailInfo['MessageID']
		replyEmail['References'] = self.emailInfo['MessageID']
		if self.emailInfo['References']:
			replyEmail['References'] += self.emailInfo['References']

		replyEmail['Subject'] = self.emailInfo['Subject']
		if 're:' not in replyEmail['Subject'].lower():
			replyEmail['Subject'] = 'Re: ' + replyEmail['Subject']
		replyEmail['From'] = self.emailInfo['To']
		replyEmail['To'] = embeddedEmailAddress or self.emailInfo['Reply-To'] or self.emailInfo['From']

		# Compose reply email
		replyEmail.attach(MIMEText(replyPayload, 'plain'))
		replyEmail.attach(MIMEText(replyImagePayload, 'html'))

		# Append original messages
		receivedContents = '-----Original Message-----\n' \
							+ 'From: ' + self.emailInfo['From'] + '\n'	\
							+ 'Date: ' + self.emailInfo['Date'] + '\n'	\
							+ 'To: ' + self.emailInfo['To'] + '\n'	\
							+ 'Subject: ' + self.emailInfo['Subject'] + '\n'	\
							+ self.emailInfo['Payload']

		replyEmail.attach(MIMEText(receivedContents, 'plain'))

		self.mysql.insertSentConversation(self.emailInfo, replyEmail, replyPayload)

		print replyPayload

		# SMTP email send.
		if self.TEST_FLAG:
			return

		self.smtpServer.sendmail(self.emailInfo['To'], self.emailInfo['From'], replyEmail.as_string())

		print('Sent email to %s' % self.emailInfo['From'])
	#enddef


	def generateReplyImage(self):
		replyTo = self.emailInfo['Reply-To'] or self.emailInfo['From']

		replyImage = '<html><body><img src="%s/%s/%s.jpg"></body></html>' \
					% ( self.webServer, self.emailInfo['ThreadID'], datetime.datetime.now().strftime("%m%d%y"))

		return replyImage
	#enddef


	def extractEmailAddress(self, payload):
		match = re.findall(r"[\w\.-]+@[\w\.-]+\.com", payload)
		if match: return match[0]
		else: return None


	def generateReply(self, corePayload):
		replyText = ''
		quoteText = corePayload.lower()

		print quoteText

		# 3rd++ reply: ignore
		paypalWordList = ['made', 'paid']
		for paypalWord in paypalWordList:
			if paypalWord in quoteText:
				return replyText

		# 2nd reply, paypal:
		if "paypal" in quoteText:
			replyText = replyText + "Sounds great. My paypal account is %s.\nPlease let me know when the payment is done!!\nThanks!" % self.myEmailDic['EMAIL']
			self.emailInfo['Subtype'] = 'sent_2_paypal'

		# 2nd reply, check or money order: ask if paypal is possible
		elif ("check" in quoteText) or ("money order" in quoteText):
			replyText = replyText + "I'm sorry but could you pay the money via paypal please?\nThanks!"
			self.emailInfo['Subtype'] = 'sent_2_check'

		# 1st reply:
		else:
			# still available for sale?
			if "sale" in quoteText:
				replyText = replyText + "Yes, it's still on sale."
			elif "available" in quoteText:
				replyText = replyText + "Yes, the product is still available.\n"
			elif "still" in quoteText:
				replyText = replyText + "I still have it for sale.\n"

			# firm price?
			if "firm" in quoteText:
				replyText = replyText + "The firm price as written in the ad.\n"
			elif "final price" in quoteText:
				replyText = replyText + "The final price is as written in the ad.\n"
			elif "last price" in quoteText:
				replyText = replyText + "The price in the ad is the last one.\n"
			elif "price" in quoteText:
				replyText = replyText + "The price is firm.\n"

			# condition?
			if ("condition" in quoteText) or ("shape" in quoteText) or ("detail" in quoteText):
				replyText = replyText + "The condition is almost perfect since it was not used frequently.\n"

			# why do you sell this?
			if "why" in quoteText:
				replyText = replyText + "I'm selling this since just because it's not in use.\n"
			elif "reason" in quoteText:
				replyText = replyText + "I'm trying to sell it since I got a similar one recently.\n"

			# append the last sentence.
			if replyText != '':
				replyText = 'Hi,\n\n' + replyText + 'Please let me know if you need more information.\n'
				self.emailInfo['Subtype'] = 'sent_1'

		#end if


		return replyText
	#enddef







	#########################################################
	#
	#	operation mode 1, 3:
	#	send out the first responses to the potential scam ads
	#
	#########################################################

	def handle_first_victim_response(self, scam_id_list, scam_level=0):
		if scam_id_list == None:
			print 'find out suspicious ads in the database and send out the first scam response if not sent yet.'
			print 'not yet ready'
			# scam_id_list = get_suspicious_ads()
			return
		else:
			print scam_id_list


		# smtp login
		if self.login() is False:
			return

		for scam_id in scam_id_list:
			print '================================'
			print scam_id
			print '================================'
			# ID, CraigslistURL, Title, PostingBody, PostingBodyEmail, ContactBodyEmail, ScamLevel
			scam_ad_data = self.mysql.getAdByID(scam_id)

			if len(scam_ad_data) == 0:
				print scam_id, 'not exists'
				return

			# extract necessary fields
			ad_id = scam_ad_data[0]
			craigslist_url = scam_ad_data[1]
			ad_title = scam_ad_data[2]
			ad_content = scam_ad_data[3]

			if scam_level == 0:
				ad_scam_level = scam_ad_data[6]
			else:
				ad_scam_level = scam_level

			if scam_level == 12:
				# print ad_content
				ad_email = re.search(r'[a-z]+ @ yahoo \(dot\) com', ad_content).group(0)
			else:
				ad_email = scam_ad_data[4] or scam_ad_data[5]

			if ad_email == '': continue
			print "scammer email: ", ad_email

			# get email account / password corresponding to Craigslist URL of the ad
			# index = self.craigslist_url_list.index(craigslist_url)
			index = random.randint(0, len(self.email_account_list) - 1)

			self.myEmailDic = {"EMAIL": self.email_account_list[index],
			                   "PASSWD": self.email_password_list[index]}

			# my name 
			my_name = self.pi.generate_name()

			# compose the first response to scam ad
			response_content = self.compose_first_victim_response(ad_title, ad_content, my_name)

			# send the first response to scam ad
			self.send_first_victim_response(ad_id, ad_email, ad_title, response_content, my_name, ad_scam_level)

			time.sleep(5)
		# endfor

		# smtp logout
		self.logout()


	def get_suspicious_ads(self):
		scam_id_list = self.mysql.getSuspiciousAds()
		return scam_id_list


	def compose_first_victim_response(self, ad_title, ad_content, my_name):
		body = ad_content.lower()

		room_type = 'house'
		if 'apartment' in body or 'apt' in body:
			room_type = 'apartment'
		elif 'condo' in body:
			room_type = 'condo'

		email_text = ''

		# 1st sentence
		sentence_list = ['Hi,\n\n', 'Hello,\n\n', 'Hi there,\n\n', 'Dear homeowner,\n\n', 'Dear owner,\n\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		# 2nd sentence
		sentence_list = ['May I ask if your house is still available for rent?\n',
		                 'May I ask if your house is still available?\n',
		                 'May I ask if your place is still available for rent?\n',
		                 'May I ask if your place is still available?\n',
		                 'Is your house still available for rent?\n',
		                 'Is your house still available?\n',
		                 'I saw your ad on Craigslist and I\'d like to ask if you are still looking for a tenant for your home. ',
		                 'I\'m about to move to your area soon, so I wonder if your place is still available.\n',
		                 'Are you still looking for a tenant?',
		                 'Do you still look for a tenant?',
		                 'Do you still have your house on the market?']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		"""
		# 2nd sentence
		sentence_list = ['I saw your rental ad on Craigslist.  ', 
											'I\'m looking for a place to stay and I saw your ad on Craigslist.  ', 
											'I saw your ad on Craigslist and I\'d like to ask if you are still looking for a tenant for your home. ',
											'I\'m about to move to your area soon, so I\'m looking for a house or condo for my family.  ',
											'I have read your rental posting on Craigslist. ',
											'I am looking for a place for my family and I think your home looks good enough for my family! ']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
		# 3rd sentence
		sentence_list = ['Your %s looks pretty nice, and I\'m really interested in renting your place.  Is it still available for the rent?',
												'I think your %s is suitable for my family so I\'d like to ask if I would be able to rent your house.  ',
												'Can we meet up so that I can take a look at your %s?  ',
												'\nCould you please let me know when I would be able to look at your %s?  ',
												'\nI wonder if I can look around your %s anytime soon. ',
												'\nWould it be possible to meet you and see your %s? ']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)] % (room_type)
					
		# 4th sentence
		sentence_list = ['', 
											'I\'m looking forward to hearing from you!', 
											'',
											'Please let me know any time soon!',
											'Please let me know if you have any questions about me.',
											'I am looking forward to meeting you soon!',
											'',
											'I would really appreciate it if I can take a look at your place!']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		"""

		# last sentence
		sentence_list = ['\n\nThanks!\n',
		                 '\n\nThank you.\n',
		                 '\n\n\nSincerely,\n',
		                 '\n\nRegards,\n',
		                 '\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]
		email_text += my_name

		return email_text


	def send_first_victim_response(self, ad_id, ad_email, ad_title, response_content, my_name, scam_level):
		tmp = self.myEmailDic['EMAIL'].split("@");
		self.myEmailDic['EMAIL'] = tmp[0] + '+' + str(ad_id) + '@' + tmp[1]

		# email addr edit
		ad_email = ad_email.replace(' ', '')
		ad_email = ad_email.replace('(dot)', '.')

		if self.TEST_FLAG:
			ad_email = 'KenStaley52@gmail.com'

		responseEmail = MIMEMultipart()

		replyImagePayload = self.generateEmbeddedImage(ad_id)

		responseEmail['Message-ID'] = ""
		responseEmail['In-Reply-To'] = ""
		responseEmail['References'] = ""

		responseEmail['Subject'] = ad_title

		our_email = my_name + ' <' + self.myEmailDic['EMAIL'] + '>'
		responseEmail['From'] = our_email
		# responseEmail['From'] = self.myEmailDic['EMAIL']
		responseEmail['TO'] = ad_email
		responseEmail['Payload'] = response_content

		responseEmail['ScamLevel'] = str(scam_level)

		responseEmail.attach(MIMEText(response_content, 'plain'))
		responseEmail.attach(MIMEText(replyImagePayload, 'html'))

		self.mysql.insertFirstVictimResponseEmail(responseEmail)

		#print responseEmail
		print('Sent first victim response to %s from %s' % (ad_email, self.myEmailDic['EMAIL']))


	def generateEmbeddedImage(self, ad_id):
		# 54.91.110.171
		#137.110.222.195: Damon's internal server, accessible from another damon's server.
		#169.228.66.98
		replyImagePayload = '<html><body>\
		<img src="http://54.86.198.213/email/email_sig.jpg?id=%s" width=1 height=1>\
		</body></html>' % ad_id

		return replyImagePayload




	def getFirstTextPayload(self, email_message_instance):
		maintype = email_message_instance.get_content_maintype()
		if maintype == 'multipart':
			for part in email_message_instance.walk():
				if part.get_content_type() == 'text/plain':
					return part.get_payload(decode=True)

			for part in email_message_instance.get_payload():
				if part.get_content_maintype() == 'text':
					return part.get_payload(decode=True)

		elif maintype == 'text':
			return email_message_instance.get_payload(decode=True)
		# end def


	def removeQuotes(self, payload):
		if payload == None:
			return ''
		payloadArray = payload.splitlines()
		corePayload = ''

		for line in payloadArray:
			if (re.search('<.+@.+\..+>', line)) or (re.search('----', line)):
				break
			else:
				corePayload += line + '\n'

		return corePayload
		# end def


	def send_second_victim_response(self, emailInfo):
		replyEmail = MIMEMultipart()

		# Generate reply payload		
		replyPayload = self.compose_second_victim_response(emailInfo)

		print 'reply payload:'
		print replyPayload

		if replyPayload == '':
			print 'Skip reply'
			return

		# Embed an image
		replyImagePayload = self.generateEmbeddedImage(emailInfo['AdID'])

		# Reply email header
		replyEmail['Message-ID'] = email.utils.make_msgid()
		replyEmail['In-Reply-To'] = emailInfo['MessageID']
		replyEmail['References'] = emailInfo['MessageID']
		if emailInfo['References']:
			replyEmail['References'] += emailInfo['References']

		replyEmail['Subject'] = emailInfo['Subject']
		if 're:' not in replyEmail['Subject'].lower():
			replyEmail['Subject'] = 'Re: ' + replyEmail['Subject']
		replyEmail['From'] = emailInfo['To']
		replyEmail['To'] = emailInfo['Reply-To'] or emailInfo['From']
		replyEmail['Payload'] = replyPayload

		# Compose reply email
		replyEmail.attach(MIMEText(replyPayload, 'plain'))
		replyEmail.attach(MIMEText(replyImagePayload, 'html'))

		# Append original messages
		receivedContents = '-----Original Message-----\n' \
		                   + 'From: ' + emailInfo['From'] + '\n' \
		                   + 'Date: ' + emailInfo['Date'] + '\n' \
		                   + 'To: ' + emailInfo['To'] + '\n' \
		                   + 'Subject: ' + emailInfo['Subject'] + '\n' \
		                   + emailInfo['Payload']

		replyEmail.attach(MIMEText(receivedContents, 'plain'))

		replyEmail['AdID'] = str(emailInfo['AdID'])

		self.mysql.insertSecondVictimResponseEmail(replyEmail)



		# SMTP email send.	
		if self.TEST_FLAG:
			print('Send second victim response to %s' % 'Youngsam Park <yspark@gmail.com>')
			self.smtpServer.sendmail(self.smtp_account, 'Youngsam Park <yspark@gmail.com>', replyEmail.as_string())
		else:
			print('Send second victim response to %s' % replyEmail['To'])
			self.smtpServer.sendmail(self.smtp_account, replyEmail['To'], replyEmail.as_string())

		time.sleep(3)
		# enddef


	def compose_second_victim_response(self, emailInfo):

		print 'compose_second_victim_response'

		email_text = ''

		# 1st sentence
		sentence_list = ['Hi,\n\n', 'Hello,\n\n', 'Hey,\n\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		# 2nd sentence
		sentence_list = ['',
		                 'Thanks for your response. ',
		                 'Okay, I understand your situation now. ',
		                 'Great to know that the rent is still available!\n',
		                 'It is good to know that the house is still available for the rent.\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		# 3rd sentence
		sentence_list = [
			'We are going to move to your area next month. So I wonder if it would be okay to start the rent from next month.\n',
			'I guess it would be little bit hard to meet you and take a look at the house.\n',
			'I would like to rent your house from next month if possible. Please let me know how I can proceed the rent process.\n',
			'I want to rent your house any time soon in two weeks.\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		# 4th sentence
		sentence_list = ['How do I make the first rent with the deposit?\n',
		                 'Also please let me know how I would make the rent and deposit.\n',
		                 'May I ask how I would be able to make the rent and deposit?\n',
		                 'Please let me know how I need to make the first rent and deposit.\n',
		                 'I want to make a payment soon, so let me know how you want me to make it!\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]


		# rent application
		if emailInfo['ScamLevel'] == 102:
			email_text += self.compose_rent_application(emailInfo)


		# last sentence
		sentence_list = ['\n\nThanks!\n',
		                 '\n\nThank you.\n',
		                 '\n\n\nSincerely,\n\n',
		                 '\n\nRegards,\n',
		                 '\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		email_text += '\n\n\n\n'

		return email_text


	FIRST_RENT_TEMPLATE_INDEX = 'a'
	LAST_RENT_TEMPLATE_INDEX = 'n'

	def get_application_template(self, payload):

		for index in xrange(ord(self.FIRST_RENT_TEMPLATE_INDEX), ord(self.LAST_RENT_TEMPLATE_INDEX) + 1):
			filename = './rent_application/rent_' + chr(index) + '.txt'
			with open(filename, 'r') as template_file:
				template = template_file.read().splitlines()

				flag = True
				for template_line in template[0:4]:
					if not template_line in payload:
						flag = False
						break
					else:
						print 'Match: ', template_line
						print template[0:4]

				if flag == True:
					print 'Found template:'
					print template

					return template

		return None

	def is_application_scam(self, payload):
		for index in xrange(ord(self.FIRST_RENT_TEMPLATE_INDEX), ord(self.LAST_RENT_TEMPLATE_INDEX) + 1):
			filename = './rent_application/rent_' + chr(index) + '.txt'
			with open(filename, 'r') as template_file:
				template = template_file.read().splitlines()

				if template[0].lower() in payload:
					return True

		return False


	def compose_rent_application(self, emailInfo):
		pi = PersonalInformation.PersonalInformation()
		template = self.get_application_template(emailInfo['Payload'])
		email_text = ''

		# 1st sentence
		sentence_list = ['Here I\'m attaching my rent application.\n\n\n',
		                 'Please refer to my rent application.\n\n',
		                 'Please refer to my rent application form.\n\n\n',
		                 'I also prepared for the rent application form.\n\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]


		# pre-defined templates
		if template:
			email_text += template[0] + '\n\n'

			for line in template[1:]:
				new_line = self.get_application_line(line, pi)
				if len(new_line) >= 1:
					email_text += new_line + '\n'
		# uncovered application form
		else:
			# find out the application form
			payload_lines = emailInfo['Payload'].split('\n')

			application_flag = False
			for line in payload_lines:
				if application_flag == False and ('_____' in line or 'name?' in line):
					application_flag = True
					print 'APPLICATION START: ' + line

				if application_flag:
					if len(line) < 3:
						break

					answer = self.get_application_line(line, pi) + '\n'

					if len(answer) > 5:
						email_text += answer

		return email_text


	def get_application_line(self, ori_line, pi):
		ori_line = ori_line.rstrip('\r\n')
		ori_line = ori_line.rstrip('\n')
		ori_line = ori_line.replace('_', '')
		ori_line = ori_line.replace('?', '')
		if ':' not in ori_line:
			ori_line = ori_line + ': '

		line = ori_line.lower()
		print line

		# name
		if ('full' in line and 'name' in line) or line[0:4] == 'name':
			return ori_line + '  ' + pi.generate_name()
		elif 'first name' in line:
			return ori_line + '  ' + pi.generate_first_name()
		elif 'last name' in line or 'surname' in line:
			return ori_line + '  ' + pi.generate_last_name()
		# Date of Birth
		elif 'birth' in line:
			return ori_line + '  ' + pi.generate_date_of_birth()
		# Address & Phone
		elif 'address' in line and 'phone' in line:
			address, phone = pi.generate_address_phone()
			return ori_line + ' ' + address + ', ' + phone
		# Address
		elif 'address' in line:
			address, phone = pi.generate_address_phone()
			return ori_line + ' ' + address
		# Phone
		elif 'phone' in line and 'landlord' not in line:
			address, phone = pi.generate_address_phone()
			return ori_line + ' ' + phone
		# age & martial status
		elif 'age' in line and 'martial' in line:
			return ori_line + ' ' + pi.generate_age() + ', ' + pi.generate_martial_status()
		# age
		elif 'age' in line:
			return ori_line + ' ' + pi.generate_age()
		# martial status
		elif 'married' in line or 'martial' in line or 'marital' in line:
			return ori_line + ' ' + pi.generate_martial_status()
		# reason for leaving
		elif 'reason' in line or 'leaving' in line:
			return ori_line + ' ' + pi.generate_reason_for_leaving()
		# Family number
		elif 'how many people' in line or 'occupant' in line:
			return ori_line + ' ' + pi.generate_family_number()
		# pet
		elif 'pet' in line and 'personality' not in line and 'kind' not in line:
			return ori_line + '  ' + pi.generate_pet()
		elif 'personality' in line or 'kind of pet' in line:
			return ori_line + '  ' + pi.generate_pet_detail()
		# cat
		elif 'car' in line:
			return ori_line + '  ' + pi.generate_car()
		# occupation
		elif 'occupation' in line or 'profession' in line:
			return ori_line + ' ' + pi.generate_occupation()
		# move in
		elif 'move in' in line or 'move-in' in line or 'movein' in line or 'moving in' in line:
			return ori_line + '  ' + pi.generate_movein()
		# lease term
		elif 'how long' in line or 'length' in line:
			return ori_line + ' ' + pi.generate_lease_term()
		# deposit how many?
		elif 'how many months' in line:
			return ori_line + ' ' + pi.generate_deposit()
		# key/document
		elif 'key' in line or 'document' in line:
			return ori_line + ' ' + pi.generate_key_date()
		# payment date
		elif 'deposit payment' in line or 'pay the deposit' in line or 'how soon' in line:
			return ori_line + ' ' + pi.generate_payment_date()
		# time to call
		elif 'time to call' in line or 'time to reach' in line:
			return ori_line + '  ' + pi.generate_time_to_call()
		# smoke?
		elif 'smoke' in line:
			return ori_line + '  ' + pi.generate_smoke()
		# smoke?
		elif 'drink' in line:
			return ori_line + '  ' + pi.generate_drink()
		# kids
		elif 'kid' in line:
			return ori_line + '  ' + pi.generate_kids()
		# sex
		elif 'sex' in line:
			return ori_line + '  Male'
		# income
		elif 'income' in line:
			return ori_line + '  ' + pi.generate_income()
		# work late night
		elif 'work late' in line:
			return ori_line + '  ' + 'No'
		# do you have payment?
		elif 'do you have payment' in line:
			return ori_line + '  ' + 'Yes'
		# Rent
		elif 'rent' in line:
			return ori_line + '  ' + pi.generate_current_rent()
		else:
			return ''





		#########################################################
		#
		# Operation mode 2 :

	#	Send out third victim responses
	#
	#########################################################		
	def send_third_victim_response(self, emailInfo):

		# check the keywords		
		payload = emailInfo['Payload'].lower()
		payload = payload.replace('\r\n', '')
		payload = payload.replace('\n', '')
		payload = payload.replace(' ', '')

		keyword_list = ['howtomake', 'westernunion', 'moneygram', 'paypal', 'getbacktome', 'vanillaprepaid', 'fedex',
		                'getbacktome']

		flag = False
		for keyword in keyword_list:
			if keyword in payload:
				flag = True
				break

		if flag == False:
			if emailInfo['ScamLevel'] != 102:
				return


		# repalyEmail
		replyEmail = MIMEMultipart()

		# Generate reply payload		
		replyPayload = self.compose_third_victim_response(emailInfo)

		print replyPayload

		if replyPayload == '':
			print 'Skip reply'
			return

		# Embed an image
		replyImagePayload = self.generateEmbeddedImage(emailInfo['AdID'])

		# Reply email header
		replyEmail['Message-ID'] = email.utils.make_msgid()
		replyEmail['In-Reply-To'] = emailInfo['MessageID']
		replyEmail['References'] = emailInfo['MessageID']
		if emailInfo['References']:
			replyEmail['References'] += emailInfo['References']

		replyEmail['Subject'] = emailInfo['Subject']
		if 're:' not in replyEmail['Subject'].lower():
			replyEmail['Subject'] = 'Re: ' + replyEmail['Subject']
		replyEmail['From'] = emailInfo['To']
		replyEmail['To'] = emailInfo['Reply-To'] or emailInfo['From']
		replyEmail['Payload'] = replyPayload

		# Compose reply email
		replyEmail.attach(MIMEText(replyPayload, 'plain'))
		replyEmail.attach(MIMEText(replyImagePayload, 'html'))

		# Append original messages
		receivedContents = '-----Original Message-----\n' \
		                   + 'From: ' + emailInfo['From'] + '\n' \
		                   + 'Date: ' + emailInfo['Date'] + '\n' \
		                   + 'To: ' + emailInfo['To'] + '\n' \
		                   + 'Subject: ' + emailInfo['Subject'] + '\n' \
		                   + emailInfo['Payload']

		replyEmail.attach(MIMEText(receivedContents, 'plain'))

		replyEmail['AdID'] = str(emailInfo['AdID'])

		self.mysql.insertSecondVictimResponseEmail(replyEmail)



		# SMTP email send.	
		if self.TEST_FLAG:
			print('Send third victim response to %s' % 'Youngsam Park <yspark@gmail.com>')
			self.smtpServer.sendmail(self.smtp_account, 'Youngsam Park <yspark@gmail.com>', replyEmail.as_string())
		#self.smtpServer.sendmail(self.smtp_account, 'Vm As <vmas596@yahoo.com>', replyEmail.as_string())
		else:
			print('Send third victim response to %s' % replyEmail['To'])
			self.smtpServer.sendmail(self.smtp_account, replyEmail['To'], replyEmail.as_string())

		time.sleep(3)

	#enddef



	def compose_third_victim_response(self, emailInfo):

		print 'compose_third_victim_response'

		email_text = ''

		# 1st sentence
		sentence_list = ['Hi,\n\n', 'Hello,\n\n', 'Hey,\n\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		# 2nd sentence
		sentence_list = ['',
		                 'Thanks for your response. It\'s really great to hear that I can rent your house.',
		                 'It\'s really great that I can rent your house!!\n. ',
		                 'I\'m so happy that I can rent your house.',
		                 'Thanks!\n',
		                 'I really appreciate it.',
		                 'I appreciate it!!\n',
		                 'Thank you so much!',
		                 'Thanks you!\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		# 3rd sentence
		sentence_list = ['Please let me know how to make the payment.\n',
		                 'Could you please let me know how to make the payment?\n',
		                 'Could you let me know how to make the payment?\n',
		                 'Could you please let me know how I can make the payment?\n',
		                 'Could you let me know how I can make the payment?\n',
		                 'May I ask how to make the payment?  Once I get the information, I will make the payment!\n',
		                 'May I ask how I can make the payment?\n',
		                 'Sure, I will make the payment per your instruction.  Please let me know how.\n',
		                 'I will make the payment as your instruction, so please let me know how I can make the payment.\n',
		                 'So how can I make the payment?\n',
		                 'How can I make the payment??\n',
		                 'How do I make the payment??\n',
		                 'Please let me know how to make the payment.\n',
		                 'Please let me know how I can make the payment.\n',
		                 'Please let me know how to proceed further.\n',
		                 'Let me know how to proceed the rent process.I will try to make the payment asap.\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]


		# rent application
		if emailInfo['ScamLevel'] == 102:
			email_text += self.compose_rent_application(emailInfo)


		# last sentence
		sentence_list = ['\n\nThanks!\n',
		                 '\n\nThank you.\n',
		                 '\n\n\nSincerely,\n\n',
		                 '\n\nRegards,\n',
		                 '\n']
		email_text += sentence_list[random.randint(0, len(sentence_list) - 1)]

		email_text += '\n\n\n\n'

		return email_text  # endclass


if __name__ == "__main__":
	TEST_FLAG = False
	if TEST_FLAG:
		test_email_dic = {
			"EMAIL":"umdcriminalproject@gmail.com",
			"PASSWD":"umdscamscam",
		}
		e = EmailHandler(email_dic = test_email_dic, TEST_FLAG=TEST_FLAG)
		e.login()
		e.read_emails()
		e.logout()
		sys.exit()

	count = 0
	for emailDic in emailList:
		print '==============================================='
		print count, emailDic['EMAIL'], emailDic['CITY']
		print '==============================================='
		e = EmailHandler(email_dic = emailDic, TEST_FLAG=TEST_FLAG)
		e.login()
		e.read_emails()
		e.logout()
		count += 1
