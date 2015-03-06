#!/usr/bin/python
import datetime
import MySQLdb
import re
import csv
from collections import Counter




mysql = MySQLdb.connect(host='localhost', port=3306, user='scam', passwd='scam', db='ScamProject')
cursor = mysql.cursor()


INDEX_LIST = ['THREAD_ID', 'ADID', 'NAME', 'EMAIL', 'CATEGORY',  'PRICE', 'SUBJECT', 'TIME', 'CITY', 'NUM_TRANSACTION', \
        'FIRST_RESPONSE',  'NAME_P',  'GREETING_P', 'PHONE_P', 'NUM_CHAR',  'SMARTPHONE_P',  \
        'CONDITION_P', 'PRICE_P', 'PAYPAL_P' , 'EMAIL_P', 'ADEQUATE' , \
        'NUM_RESPONSE' , 'DOUBLE_THEM', 'DOUBLE_US', 'PAYPAL_RECEIPT', \
        'PAYPAL_PAYMENT', 'OTHER_PAYMENT', \
        'RESPONSE_TIME', 'IP_ADDR_CHANGE', 'WHOLE_PAYLOAD']


def extract_phone_number(text):
  phone_re = re.compile(r'(\d{3}[-\.\s]*\d{3}[-\.\s]*\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]\d{4}|\d{3}[-\.\s]\d{4})')
  phone_list = phone_re.findall(text)
        
  if len(phone_list): 
    return True 
  else: 
    return False

def extract_email(text):
  email_list = re.findall(r'[a-zA-Z]+[\w\.-]+[\s]*@[\s]*[a-zA-Z]+\.[a-zA-Z]+', text)

  if len(email_list): 
    return True 
  else: 
    return False

def extract_greeting(text): 
  greeting_list = ['hello', 'hi', 'greeting', 'hey', 'good day']

  for word in greeting_list:
    reg_exp = '(^|\W)'+word+'\W'
    if re.search(reg_exp, text):
      return True

  return False


def handle_first_response(row, email_thread_dic):
  thread_id = row[18]
  email_thread_dic[thread_id] = []
  
  # thread id
  email_thread_dic[thread_id].append(thread_id)
  # ad id
  email_thread_dic[thread_id].append('-')

  # scammer name
  if row[19] != None:
    email_thread_dic[thread_id].append([row[19]])
  else:
    email_thread_dic[thread_id].append([])
  # scammer email address
  email_thread_dic[thread_id].append([row[2]])
  if row[3] != None and row[3] not in email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')]:
    email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')].append(row[3])
  if row[4] != None and row[4] not in email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')]:
    email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')].append(row[4])

  # category (object)
  email_thread_dic[thread_id].append(row[7])
  # price
  email_thread_dic[thread_id].append(row[10])
  # subject
  email_thread_dic[thread_id].append(row[9])
  # time
  email_thread_dic[thread_id].append('-')
  # city
  email_thread_dic[thread_id].append(row[8])
  # number of resulting transactions
  email_thread_dic[thread_id].append('-')
  
  ############################################################

  payload = row[13].lower()
  # payload
  email_thread_dic[thread_id].append(payload)
  # name presence
  if row[19] == '':
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)
  # greeting
  if extract_greeting(payload):
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)
  # phone number
  if extract_phone_number(payload):
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)
  # number of charactres
  email_thread_dic[thread_id].append(len(payload))
  # smart phone
  if any(['iphone' in payload, 'android' in payload, 'blackberry' in payload]):
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)
  # condition?
  if any(['condition' in payload, 'shape' in payload]):
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)
  # price?
  if 'price' in payload:
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)
  # paypal?
  if 'paypal' in payload:
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)
  # email?
  if extract_email(payload):
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)  
  # adequate?
  email_thread_dic[thread_id].append('-')  

  #######################################################

  # number of replies
  email_thread_dic[thread_id].append(0)  
  
  # same responses from a scammer?
  email_thread_dic[thread_id].append([payload])  

  # same reply from us?
  email_thread_dic[thread_id].append([])  

  # paypal receipt?
  email_thread_dic[thread_id].append('-')  

  # paypal mentioned?
  if 'paypal' in payload: 
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)

  # payment method other than paypal mentioned?
  if any(['check' in payload, 'money order' in payload]):
    email_thread_dic[thread_id].append(1)
  else:
    email_thread_dic[thread_id].append(0)  

  # Response time - Reception time of first scammer email
  email_thread_dic[thread_id].append('')

  # IP address change?
  email_thread_dic[thread_id].append([row[5]])

  # Whole Payload
  email_thread_dic[thread_id].append([row[13]])

  #print email_thread_dic



def handle_non_first_response(row, email_thread_dic):
  thread_id = row[18]
  payload = row[13].lower()

  # scammer name
  if row[19] != None and row[19] not in email_thread_dic[thread_id][INDEX_LIST.index('NAME')]:
    email_thread_dic[thread_id][INDEX_LIST.index('NAME')].append(row[19])
  
  # scammer email address
  if row[2] != None and row[2] not in email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')]:
    email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')].append(row[2])
  if row[3] != None and row[3] not in email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')]:
    email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')].append(row[3])
  if row[4] != None and row[4] not in email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')]:
    email_thread_dic[thread_id][INDEX_LIST.index('EMAIL')].append(row[4])


  # number of replies
  email_thread_dic[thread_id][INDEX_LIST.index('NUM_RESPONSE')]+=1  
  
  # same responses from a scammer?
  email_thread_dic[thread_id][INDEX_LIST.index('DOUBLE_THEM')].append(payload)  

  # paypal receipt?
  #email_thread_dic[thread_id].append(0)  

  # PayPal mentioned?
  if 'paypal' in payload and email_thread_dic[thread_id][INDEX_LIST.index('PAYPAL_PAYMENT')] == 0:
    print 'PAYPAL:', payload 
    email_thread_dic[thread_id][INDEX_LIST.index('PAYPAL_PAYMENT')] = \
        email_thread_dic[thread_id][INDEX_LIST.index('NUM_RESPONSE')] + 1

  # payment method other than paypal mentioned?
  if any(['check' in payload, 'money order' in payload]) and email_thread_dic[thread_id][INDEX_LIST.index('OTHER_PAYMENT')] == 0:
    email_thread_dic[thread_id][INDEX_LIST.index('OTHER_PAYMENT')] = \
        email_thread_dic[thread_id][INDEX_LIST.index('NUM_RESPONSE')] + 1

  # Response time - Final 
  if isinstance(email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')], list):
    email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')] = \
        row[11] - email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')][0] 

  # IP address change?
  email_thread_dic[thread_id][INDEX_LIST.index('IP_ADDR_CHANGE')].append(row[5])

  # Whole Payload
  email_thread_dic[thread_id][INDEX_LIST.index('WHOLE_PAYLOAD')].append(row[13])



def handle_our_reply(row, email_thread_dic):
  thread_id = row[18]
  payload = row[13].lower()

  # same reply from us?
  email_thread_dic[thread_id][INDEX_LIST.index('DOUBLE_US')].append(payload)  

  # response time: write sent time.
  if email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')] == '':
    email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')] = [row[11]]

  # Whole Payload
  email_thread_dic[thread_id][INDEX_LIST.index('WHOLE_PAYLOAD')].append(row[13])





def get_responses_per_ad(email_thread_dic, ad_dic):
  for key in email_thread_dic.keys():
    ad_id = email_thread_dic[key][INDEX_LIST.index('SUBJECT')][:10] + email_thread_dic[key][INDEX_LIST.index('CITY')] 
    
    if ad_id not in ad_dic.keys():
      print ad_id
    else:
      ad_dic[ad_id][1] += 1

  for key in email_thread_dic.keys():
    ad_id = email_thread_dic[key][INDEX_LIST.index('SUBJECT')][:10] + email_thread_dic[key][INDEX_LIST.index('CITY')] 
    
    if ad_id not in ad_dic.keys():
      print ad_id
    else:
      email_thread_dic[key][INDEX_LIST.index('NUM_TRANSACTION')] = ad_dic[ad_id][1] / float(ad_dic[ad_id][0])


def post_process(email_thread_dic):
  print '=================================='
  print 'post_process'
  print '=================================='


  for key in email_thread_dic.keys():
    # Response time
    if isinstance(email_thread_dic[key][INDEX_LIST.index('RESPONSE_TIME')], list):
      email_thread_dic[key][INDEX_LIST.index('RESPONSE_TIME')] = ''
    elif isinstance(email_thread_dic[key][INDEX_LIST.index('RESPONSE_TIME')], datetime.timedelta):
      if email_thread_dic[key][INDEX_LIST.index('RESPONSE_TIME')] < datetime.timedelta(0):
        email_thread_dic[key][INDEX_LIST.index('RESPONSE_TIME')] = ''
      else:
        email_thread_dic[key][INDEX_LIST.index('RESPONSE_TIME')] = \
            email_thread_dic[key][INDEX_LIST.index('RESPONSE_TIME')].total_seconds() / 60

    # IP Address change
    if len(email_thread_dic[key][INDEX_LIST.index('IP_ADDR_CHANGE')]) == 1:
      email_thread_dic[key][INDEX_LIST.index('IP_ADDR_CHANGE')] = -1
    elif len(set(email_thread_dic[key][INDEX_LIST.index('IP_ADDR_CHANGE')])) == 1:
      email_thread_dic[key][INDEX_LIST.index('IP_ADDR_CHANGE')] = 0
    else:
      email_thread_dic[key][INDEX_LIST.index('IP_ADDR_CHANGE')] = 1

    # PayPal mentioned, then uncheck other types of payments
    if email_thread_dic[key][INDEX_LIST.index('PAYPAL_PAYMENT')] != 0:
      email_thread_dic[key][INDEX_LIST.index('OTHER_PAYMENT')] = 0






def csv_output(email_thread_dic):
  log_writer = csv.writer(open('sales_email.csv', 'wb'), delimiter=',',quoting=csv.QUOTE_ALL)
  log_writer.writerow(INDEX_LIST)

  for record in email_thread_dic.values():
    scammer_responses = record[INDEX_LIST.index('DOUBLE_THEM')]
    if len(scammer_responses) and Counter(scammer_responses).most_common(1)[0][1] > 1:
      print '=================================='
      print scammer_responses
      print '=================================='
      record[INDEX_LIST.index('DOUBLE_THEM')] = 1
    else:
      record[INDEX_LIST.index('DOUBLE_THEM')] = 0

    our_replies = record[INDEX_LIST.index('DOUBLE_US')]
    if len(our_replies) and Counter(our_replies).most_common(1)[0][1] > 1:
      print '*********************************'
      print our_replies
      print Counter(our_replies).most_common(1)[0] 
      print '*********************************'
      record[INDEX_LIST.index('DOUBLE_US')] = 1
    else:
      record[INDEX_LIST.index('DOUBLE_US')] = 0

    # output to csv file
    log_writer.writerow(record)





def main():
  # global data structure
  ad_dic = {}
  email_thread_dic = {}

 
  # retrieve all Craigslist ads
  query = "SELECT * FROM CraigslistAds;"
  cursor.execute(query)
  result_rows = cursor.fetchall()

  for row in result_rows:
    ad_id = row[5][:10]+row[7]
    if ad_id not in ad_dic.keys():
      ad_dic[ad_id] = [1,0]
    else:
      ad_dic[ad_id][0] += 1


  for key in ad_dic:
    print key, ad_dic[key]
  #sys.exit()

  # retrieve all email data
  query = "SELECT * FROM Emails WHERE Subject NOT LIKE 'POST/EDIT%' ORDER BY ID ASC;"
  cursor.execute(query)
  result_rows = cursor.fetchall()

  for row in result_rows:
    thread_id = row[18]

    # first response from a scammer
    if row[21] == 'received' and thread_id not in email_thread_dic.keys():
      handle_first_response(row, email_thread_dic)
    # non-first responses from a scammer
    elif row[21] == 'received' and thread_id in email_thread_dic.keys():
      handle_non_first_response(row, email_thread_dic)
    # our replies
    elif row[21] and 'sent' in row[21] and thread_id in email_thread_dic.keys():
      handle_our_reply(row, email_thread_dic)
  

  get_responses_per_ad(email_thread_dic, ad_dic)

  post_process(email_thread_dic)

  csv_output(email_thread_dic)
  

  #for record in email_thread_dic.values():
  #  print record


if __name__ == "__main__":
  main()







