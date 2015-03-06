#!/usr/bin/python
import datetime
import MySQLdb
import re
import csv
from collections import Counter




mysql = MySQLdb.connect(host='localhost', port=3306, user='scam', passwd='scam', db='ScamProject')
cursor = mysql.cursor()

CTITLE_LIST = ['ID', 'ThreadID', 'OurEmail', 'ScammerEmail', 'Type', 'Subtype', 'Subject', 'City', 'Category', 'Price', 'TimeStamp', 'Payload', 'WholePayload']

def handle_first_response(row, email_thread_dic):
  thread_id = row[18]
  email_thread_dic[thread_id] = []

  # ad id
  email_thread_dic[thread_id].append('-')
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

  #print email_thread_dic



def handle_non_first_response(row, email_thread_dic):
  thread_id = row[18]
  payload = row[13].lower()

  # number of replies
  email_thread_dic[thread_id][INDEX_LIST.index('NUM_RESPONSE')]+=1  
  
  # same responses from a scammer?
  email_thread_dic[thread_id][INDEX_LIST.index('DOUBLE_THEM')].append(payload)  

  # paypal receipt?
  #email_thread_dic[thread_id].append(0)  

  # PayPal mentioned?
  if 'paypal' in payload:
    email_thread_dic[thread_id][INDEX_LIST.index('PAYPAL_PAYMENT')] = 1

  # payment method other than paypal mentioned?
  if any(['check' in payload, 'money order' in payload]):
    email_thread_dic[thread_id][INDEX_LIST.index('OTHER_PAYMENT')] = 1

  # Response time - Final 
  if isinstance(email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')], list):
    email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')] = \
        row[11] - email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')][0] 

  # IP address change?
  email_thread_dic[thread_id][INDEX_LIST.index('IP_ADDR_CHANGE')].append(row[5])


def handle_our_reply(row, email_thread_dic):
  thread_id = row[18]
  payload = row[13].lower()

  # same reply from us?
  email_thread_dic[thread_id][INDEX_LIST.index('DOUBLE_US')].append(payload)  

  # response time: write sent time.
  if email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')] == '':
    email_thread_dic[thread_id][INDEX_LIST.index('RESPONSE_TIME')] = [row[11]]




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
    if email_thread_dic[key][INDEX_LIST.index('PAYPAL_PAYMENT')] == 1:
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

  log_writer = csv.writer(open('all_emails.csv', 'wb'), delimiter=',',quoting=csv.QUOTE_ALL)
  log_writer.writerow(CTITLE_LIST)

  # retrieve all email data
  query = "SELECT " + ','.join(CTITLE_LIST) + " FROM Emails ORDER BY ID ASC;"
  cursor.execute(query)
  result_rows = cursor.fetchall()

  for row in result_rows:
    log_writer.writerow(row)

  """ 
  # retrieve all Craigslist ads
  query = "SELECT * FROM CraigslistAds;"
  cursor.execute(query)
  result_rows = cursor.fetchall()

  for row in result_rows:
      ad_dic[ad_id][0] += 1
  """


if __name__ == "__main__":
  main()







