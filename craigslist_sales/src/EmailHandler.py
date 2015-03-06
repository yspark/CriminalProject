#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import re
from dateutil import parser
import datetime
import csv
import random
import time

import imaplib
import smtplib
import mimetypes

import email
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
import LocalDef

class EmailHandler:
	def __init__(self, myEmailDic = None, first_victim_response = False, TEST_FLAG = False):
		self.smtpServer = smtplib.SMTP('smtp-relay.gmail.com', LocalDef.SMTP_RELAY_PORT)
		self.imapServer = imaplib.IMAP4_SSL("imap.gmail.com")
	
		self.imap_account = CommonDef.IMAP_ACCOUNT
		self.imap_passwd = CommonDef.IMAP_PASSWD
	
		self.smtp_account = CommonDef.SMTP_RELAY_ACCOUNT
		self.smtp_passwd = CommonDef.SMTP_RELAY_PASSWD
	
		self.mysql = ScamMysql.ScamMysql(TEST = TEST_FLAG)
		#self.mysql.createTable()

		self.pi = PersonalInformation.PersonalInformation()

		self.TEST_FLAG = TEST_FLAG
	
		if first_victim_response:		
			self.init_first_victim_response()
		else:
			self.myEmailDic = myEmailDic
		
	
	def login(self, ImapOnly = False):
			
		print 'Gmail IMAP login (%s, %s)' % (self.imap_account, self.imap_passwd)
		try:
			self.imapServer.login(self.imap_account, self.imap_passwd)
		except Exception as e:
			print e
			print 'login failed'
			print sys.exc_info()
			return False

		self.ImapOnly = ImapOnly
		if ImapOnly == True:
			return True

		print 'Gmail SMTP login (%s, %s)' % (self.smtp_account, self.smtp_passwd)
		self.smtpServer.ehlo()
		self.smtpServer.starttls()
		self.smtpServer.ehlo()
		try:
			self.smtpServer.login(self.smtp_account, self.smtp_passwd)
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
	
	
	def init_first_victim_response(self):
		self.craigslist_url_list = Utils.load_url_list(CommonDef.URL_FILE)
		self.email_account_list, self.email_password_list = Utils.load_email_list(CommonDef.EMAIL_FILE)


	#########################################################
	#
	#	Handle Craigslist Confirmation Email
	#
	#########################################################
	def readCraigslistConfirmEmail(self, emailAccount):
		print '\tReading Craigslist confirm email..'

		#emailAccount  = "tracysankar74+vincentschumann@gmail.com"
		
		# Open inbox					
		while True: 		
			self.imapServer.select('INBOX')
			status, data = self.imapServer.search(None, '(UNSEEN)')
			emailIds = data[0].split()
			if len(emailIds):
				latest_email_id = int( emailIds[-1])
				break
			else:
				print '\tNo new email yet.. wait another 5 seconds...'
				time.sleep(5)
				continue
		#end while

		for i in emailIds:
			typ, data = self.imapServer.fetch( i, '(BODY.PEEK[])' )
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
						typ, data = self.imapServer.fetch( i, '(RFC822)' )
						return line
		#end for
		
		return None

	
	
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
			#scam_id_list = get_suspicious_ads()
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
				#print ad_content
				ad_email = re.search(r'[a-z]+ @ yahoo \(dot\) com', ad_content).group(0)	
			else:
				ad_email = scam_ad_data[4] or scam_ad_data[5]	

			if ad_email == '': continue
			print "scammer email: ", ad_email
	
			# get email account / password corresponding to Craigslist URL of the ad
			#index = self.craigslist_url_list.index(craigslist_url)
			index = random.randint(0, len(self.email_account_list)-1)
			
			self.myEmailDic = {"EMAIL":self.email_account_list[index],
									"PASSWD":self.email_password_list[index]}
			
			# my name 
			my_name = self.pi.generate_name()
			
			# compose the first response to scam ad
			response_content = self.compose_first_victim_response(ad_title, ad_content, my_name)
				
			# send the first response to scam ad
			self.send_first_victim_response(ad_id, ad_email, ad_title, response_content, my_name, ad_scam_level)
			
			time.sleep(5)
		#endfor
					
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
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
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
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
		
		
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
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]												
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
		#responseEmail['From'] = self.myEmailDic['EMAIL']
		responseEmail['TO'] = ad_email
		responseEmail['Payload'] = response_content
		
		responseEmail['ScamLevel'] = str(scam_level)
				
		responseEmail.attach(MIMEText(response_content, 'plain'))
		responseEmail.attach(MIMEText(replyImagePayload, 'html'))
		
		


		self.mysql.insertFirstVictimResponseEmail(responseEmail)
		
		#print responseEmail
		print('Sent first victim response to %s from %s' % (ad_email, self.myEmailDic['EMAIL']))


	def generateEmbeddedImage(self, ad_id):
		#54.91.110.171 
		#137.110.222.195: Damon's internal server, accessible from another damon's server.
		#169.228.66.98
		replyImagePayload = '<html><body>\
		<img src="http://54.86.198.213/email/email_sig.jpg?id=%s" width=1 height=1>\
		</body></html>' % ad_id

		return replyImagePayload





	#########################################################
	#
	#	Operation mode 2 : 
	#	Read in emails and send out second victim responses
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
		#else:
		#	print data
		
		
		#status, emailIds = imapServer.search(None, '(UNSEEN)')
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
			if self.TEST_FLAG:
				status, data = self.imapServer.uid('fetch', uid, '(BODY.PEEK[])')
			else:
				status, data = self.imapServer.uid('fetch', uid, '(RFC822)')
							
			email_message = email.message_from_string(data[0][1])
	
			# Check if the received email is vaild one.
			if not re.search(r'\+[0-9]+@gmail.com', email_message['To']):
				print 'Irrelevant email: ', email_message['To']
				self.imapServer.uid('store', uid, '+FLAGS', '(\Deleted)')
				continue
	
			# Receiver information			
			self.emailInfo['To'] =  email_message['To']			 
			self.emailInfo['ReceiverName'], self.emailInfo['ReceiverEmail'] = email.utils.parseaddr(email_message['To'])
	
			# extract proper id from the email address
			ad_id = int(re.split('[+@]', self.emailInfo['ReceiverEmail'])[1])
			self.emailInfo['AdID'] = ad_id
			
			# Get number of received/sent emails in this thread
			num_rcvd_email, scam_level = self.mysql.getRecvdEmailInfo(ad_id)
			if num_rcvd_email:
				num_sent_email = self.mysql.getSentEmailInfo(ad_id)
			else:
				num_sent_email = 0
			
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
					self.emailInfo['ScammerIP'] = re.findall( r'[0-9]+(?:\.[0-9]+){3}', senderInfo)[0]
				except:
					self.emailInfo['ScammerIP'] = ''
			else:
				self.emailInfo['ScammerIP'] = ''
			
			

		
			# Email details
			self.emailInfo['Subject'] = email_message['Subject']
			if self.emailInfo['Subject'] is None:
				print 'null subject'
				continue

			if '=?utf-8?' in self.emailInfo['Subject']:				
				self.emailInfo['Subject'], encoding = email.Header.decode_header(self.emailInfo['Subject'])[0]
				print 'decode utf-8 subject: %s' % self.emailInfo['Subject']
			
			
			timeUTC = parser.parse(email_message['Date']).utctimetuple()					
			self.emailInfo['Date'] = datetime.datetime(*timeUTC[:6]).	strftime('%Y-%m-%d %H:%M:%S')
			#self.emailInfo['Date'] = email_message['Date']
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
			print '=========================='
			
			payload = self.emailInfo['Payload'].lower()

			#print payload

			# scam level
			# 0: Irrelevant
			# 1: Scam with redirect link
			# 101: Scam
			# 102: Scam with application form request
			if num_rcvd_email == 0 or scam_level != 102:
				scam_level = 0			
				#if 'application' in payload or ('about' in payload and 'yourself' in payload) or 'questionnaire' in payload:
				if self.is_application_scam(payload):
					scam_level = 102
				elif 'africa' in payload or 'trip' in payload or 'moved to' in payload or 'away' in payload:
					scam_level = 101
				elif 'credit score' in payload:
					scam_level = 201					
			#endif
			
			self.emailInfo['ScamLevel'] = scam_level
			
			print '# received email in this thread: ', num_rcvd_email
			print 'scam level: ', scam_level
		
			# insert into database
			self.mysql.insertRcvdEmail(self.emailInfo)

			# send second victim response			
			if num_rcvd_email == 0:			
				print 'send_second_victim_response'
				self.send_second_victim_response(self.emailInfo)
			elif num_sent_email < 2 or (num_sent_email < 4 and (scam_level == 101 or scam_level == 102)):
				print 'send_third_victim_response'
				self.send_third_victim_response(self.emailInfo)
			
			
			if self.TEST_FLAG:
				return
		#endfor	
	#end def	


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
	#end def
	
	
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
	#end def


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
							+ 'From: ' + emailInfo['From'] + '\n'	\
							+ 'Date: ' + emailInfo['Date'] + '\n'	\
							+ 'To: ' + emailInfo['To'] + '\n'	\
							+ 'Subject: ' + emailInfo['Subject'] + '\n'	\
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
	#enddef


	def compose_second_victim_response(self, emailInfo):
		
		print 'compose_second_victim_response'
					
					
		email_text = ''
				
		# 1st sentence
		sentence_list = ['Hi,\n\n', 'Hello,\n\n', 'Hey,\n\n']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
		# 2nd sentence
		sentence_list = ['', 
											'Thanks for your response. ', 
											'Okay, I understand your situation now. ',
											'Great to know that the rent is still available!\n',
											'It is good to know that the house is still available for the rent.\n']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
		# 3rd sentence
		sentence_list = ['We are going to move to your area next month. So I wonder if it would be okay to start the rent from next month.\n',
												'I guess it would be little bit hard to meet you and take a look at the house.\n',
												'I would like to rent your house from next month if possible. Please let me know how I can proceed the rent process.\n',
												'I want to rent your house any time soon in two weeks.\n']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)] 
												
		# 4th sentence
		sentence_list = ['How do I make the first rent with the deposit?\n',
											'Also please let me know how I would make the rent and deposit.\n',
											'May I ask how I would be able to make the rent and deposit?\n',
											'Please let me know how I need to make the first rent and deposit.\n',
											'I want to make a payment soon, so let me know how you want me to make it!\n']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
		
		# rent application
		if emailInfo['ScamLevel'] == 	102:
			email_text += self.compose_rent_application(emailInfo)
		
		
		# last sentence
		sentence_list = ['\n\nThanks!\n',
											'\n\nThank you.\n',
											'\n\n\nSincerely,\n\n',
											'\n\nRegards,\n',
											'\n']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
	
		email_text += '\n\n\n\n'	
												
		return email_text		
	
	
	FIRST_RENT_TEMPLATE_INDEX = 'a'
	LAST_RENT_TEMPLATE_INDEX = 'n'
	def get_application_template(self, payload):
		
		for index in xrange(ord(self.FIRST_RENT_TEMPLATE_INDEX), ord(self.LAST_RENT_TEMPLATE_INDEX)+1):
			filename =  './rent_application/rent_' + chr(index) + '.txt'
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
		for index in xrange(ord(self.FIRST_RENT_TEMPLATE_INDEX), ord(self.LAST_RENT_TEMPLATE_INDEX)+1):
			filename =  './rent_application/rent_' + chr(index) + '.txt'
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
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
		
		# pre-defined templates
		if template:
			email_text += template[0] + '\n\n'
			
			for line in template[1:]:
				new_line = self.get_application_line(line, pi)
				if len(new_line) >= 1:
					email_text += new_line +'\n'
		# uncovered application form
		else:			
			# find out the application form
			payload_lines = emailInfo['Payload'].split('\n') 
			
			application_flag = False
			for line in payload_lines:
				if application_flag == False and ('_____' in line or 'name?' in line):
					application_flag = True
					print 'APPLICATION START: '+line
					
				if application_flag:
					if len(line) < 3:
						break
					
					answer = self.get_application_line(line, pi)+'\n'
			
					if len(answer) > 5: 
						email_text += answer
						
		return email_text
	
	
	def get_application_line(self, ori_line, pi):
		ori_line = ori_line.rstrip('\r\n')
		ori_line = ori_line.rstrip('\n')
		ori_line = ori_line.replace('_','')
		ori_line = ori_line.replace('?','')
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
	#	Operation mode 2 : 
	#	Send out third victim responses
	#
	#########################################################		
	def send_third_victim_response(self, emailInfo):
		
		# check the keywords		
		payload = emailInfo['Payload'].lower()
		payload = payload.replace('\r\n', '')
		payload = payload.replace('\n', '')
		payload = payload.replace(' ', '')
		
		keyword_list = ['howtomake', 'westernunion', 'moneygram', 'paypal', 'getbacktome', 'vanillaprepaid', 'fedex', 'getbacktome']
		
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
							+ 'From: ' + emailInfo['From'] + '\n'	\
							+ 'Date: ' + emailInfo['Date'] + '\n'	\
							+ 'To: ' + emailInfo['To'] + '\n'	\
							+ 'Subject: ' + emailInfo['Subject'] + '\n'	\
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
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
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
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
		
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
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)] 
														
														
		# rent application
		if emailInfo['ScamLevel'] == 	102:
			email_text += self.compose_rent_application(emailInfo)														
			
																	
		# last sentence
		sentence_list = ['\n\nThanks!\n',
											'\n\nThank you.\n',
											'\n\n\nSincerely,\n\n',
											'\n\nRegards,\n',
											'\n']
		email_text += sentence_list[random.randint(0, len(sentence_list)-1)]
	
		email_text += '\n\n\n\n'	
												
		return email_text		
#endclass


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "EmailHandler 1 : Send out first victim responses to suspicious emails"
		print "EmailHandler 2 : Read in emails and send out second victim responses"
		
		print "EmailHandler 3 : send out emails to additional suspicious rental ads"
		sys.exit()
	
	
	if int(sys.argv[1]) == 1:		
		e = EmailHandler(first_victim_response = True, TEST_FLAG = False)
		
		"""
		scam_id_list = [1013441]
		e.handle_first_victim_response(scam_id_list, scam_level=12)
		"""
		
		scam_id_list = [899320, 93433, 88827, 1243901, 71422, 1780480, 1054465, 1214211, 1600263, 1432841, 1121036, 1837325, 1718548, 1174295, 1174297, 84762, 1576731, 1375004, 1398558, 1308961, 1665827, 1064742, 20265, 1905450, 1652526, 88879, 1423664, 42290, 2071347, 1234740, 50998, 1163063, 2023903, 1542472, 1250121, 863562, 50999, 1427792, 1339729, 1178976, 54637, 1649545, 1064824, 1719161, 1627006, 1040768, 58246, 1327497, 1621386, 1342859, 1495438, 67053, 1351569, 1357727, 25506, 1735588, 1662889, 51114, 93612, 1209773, 1648047, 1473970, 55733, 1054141, 1984446, 59381, 1593280, 26567, 26568, 1648073, 900061, 1661899, 1349068, 1443789, 1611728, 2111441, 2038739, 1514969, 909786, 1205725, 1666014, 2065061, 1848299, 1499628, 1805805, 1909170, 894449, 867826, 50942, 1602551, 1911295, 2026069]
		done_list = [505, 1015, 4163, 5243, 5515, 5576, 7070, 7490, 8170, 9767, 10892, 13916, 14031, 15005, 15039, 15212, 16108, 16298, 18430, 19898, 19901, 19902]+[25088, 1666053, 2058246, 1117192, 83980, 1878032, 112658, 53268, 57882, 1093659, 2042908, 53279, 1354785, 53286, 2023976, 1401899, 96301, 80950, 1177143, 1730106, 53307, 20031, 2096396, 112719, 58965, 1737816, 1060441, 2054752, 1118307, 1721960, 1643119, 35721, 1129585, 77426, 33395, 1734261, 1376889, 1082492, 1994877, 1118846, 2010757, 1706177, 1712270, 1777812, 1910421, 1777823, 1610405, 1911977, 1319112, 1433779, 96443, 1977536, 1013441, 45003, 1846472, 1081778, 1143501, 1998030, 898258, 2112733, 84702, 84703, 1652449, 84711, 1610476, 1432815, 1907441, 1785077, 1756918, 29229, 1013441, 1499570] + [55733, 1082492, 1121036, 1243901, 1375004, 1398558, 1473970, 1666053, 1721960, 1730106, 1735588, 1909170]
		scam_id_list = list(set(scam_id_list) - set(done_list))
		#[55733, 1082492, 1121036, 1243901, 1375004, 1398558, 1473970, 1666053, 1721960, 1730106, 1735588, 1909170]
		e.handle_first_victim_response(scam_id_list)
	else:
		e = EmailHandler(first_victim_response = False, TEST_FLAG = False)
		e.login()
		e.read_emails()
		e.logout()
