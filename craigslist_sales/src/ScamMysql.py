import MySQLdb
import sys

import os
import time
import datetime

class ScamMysql:
  def __init__(self, user='scam', passwd='scam', db='CriminalProject', host='127.0.0.1', TEST=False):
      self.user = user
      self.passwd = passwd
      self.db = db
      self.host = host
      
      self.sshTunnel = None
      self.localPort = 3306
                           
      self.TEST = TEST
      
  def connect(self):    
      self.mysql = MySQLdb.connect(host=self.host, port=self.localPort, user=self.user, passwd=self.passwd, db=self.db)
      
      with self.mysql:
          self.cursor = self.mysql.cursor()                        

          # Table for Craigslist ads
          try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS \
                  CraigslistAds(ID INT UNSIGNED NOT NULL AUTO_INCREMENT, \
                              Email VARCHAR(60), \
                              BaseEmail VARCHAR(60), \
                              Category VARCHAR(16), \
                              Subject VARCHAR(120), \
                              Mode INT, \
                              Price INT, \
                              City VARCHAR(30), \
                              PostingTime DATETIME, \
                              Status VARCHAR(20), \
                              DeletedTime DATETIME, \
                              URL VARCHAR(120), \
                              NameMode VARCHAR(10), \
                              MediumMode VARCHAR(10), \
                              Content TEXT, \
                              PRIMARY KEY (ID) ) ")
          except:
            print 'Table CraigslistAds already exists'
          
          
          # Table for Email Conversations
          try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS \
                  Emails(ID INT UNSIGNED NOT NULL AUTO_INCREMENT, \
                          OurEmail VARCHAR(60), \
                          ScammerEmail VARCHAR(60), \
                          ScammerReplyTo VARCHAR(60), \
                          RealScammerEmail VARCHAR(60), \
                          ScammerName VARCHAR(30), \
                          ScammerIP VARCHAR(20), \
                          Subject VARCHAR(100), \
                          Type VARCHAR(20), \
                          Subtype VARCHAR(20), \
                          TimeStamp DATETIME, \
                          Shipping TEXT, \
                          Payload TEXT, \
                          WholePayload TEXT, \
                          PRIMARY KEY (ID), \
                          MessageID VARCHAR(100), \
                          ThreadID VARCHAR(100),  \
                          GroupID INT )")
          except:
            print 'Table Emails already exists'
          

          
  def disconnect(self):
    os.system("kill $(pgrep -f 'ssh -f')")
    #self.sshTunnel.kill()



  #####################################################################
	# Email conversation
	#####################################################################
  def insertCraigslistAd(self, craigslistAdDic):

    query = ( "INSERT INTO CraigslistAds"
              "(Email,"
              "BaseEmail,"
              "Category,"
              "Subject,"
              "Price,"
              "City,"
              "PostingTime,"
              "URL,"
              "Status,"
              "NameMode,"
              "MediumMode,"
              "Content) "
              "VALUES"
              "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" )

    parameter = (craigslistAdDic['Email'],\
                 craigslistAdDic['BaseAccount'],\
                 craigslistAdDic['Category'],\
                 craigslistAdDic['Subject'],\
                 int(craigslistAdDic['Price']),\
                 craigslistAdDic['City'],\
                 datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),\
                 craigslistAdDic['URL'],\
                 craigslistAdDic['Status'],\
                 craigslistAdDic['NameMode'],\
                 craigslistAdDic['MediumMode'],\
                  craigslistAdDic['Content'])
    print query
    print parameter

    if not self.TEST:
      self.cursor.execute(query, parameter)
      self.mysql.commit()
  #enddef



	#####################################################################
	# Email conversation
	#####################################################################
  def insertReceivedConversation(self, emailDic):
      query = ("INSERT INTO Emails"
               "(OurEmail,"
               "ScammerEmail,"
               "ScammerReplyTo," 
               "RealScammerEmail,"
               "ScammerName,"
               "ScammerIP,"
							 "Subject,"
               "Type,"
               "Subtype,"
               "TimeStamp,"
               "Payload,"
               "WholePayload, "
               "MessageID, "
               "ThreadID) "                 
               "VALUES"
               "(%s, %s, %s, %s, %s, "
               "%s, %s, %s, %s, %s,"
               "%s, %s, %s, %s)" )
               
      parameter = (emailDic['ReceiverEmail'],\
                   emailDic['SenderEmail'],\
                   emailDic['Reply-To'],\
                   emailDic['RealSenderEmail'],\
                   emailDic['SenderName'],\
                   emailDic['SenderIP'],\
									 emailDic['Subject'],\
                   emailDic['Type'],\
                   'received',\
                   emailDic['Date'],\
                   emailDic['CorePayload'],\
                   emailDic['Payload'], \
                   emailDic['MessageID'], \
                   emailDic['ThreadID'])        
      
      if not self.TEST:
        self.cursor.execute(query, parameter)
        self.mysql.commit()                            
  
  
  def insertSentConversation(self, receivedEmailDic, sentEmailDic, sentPayload):
      #AdID, AdPostingTime, AdCity = self.getCraigslistAd(receivedEmailDic)
              
      query = ("INSERT INTO Emails"
               "(OurEmail,"
               "ScammerEmail,"
               "ScammerReplyTo," 
               "RealScammerEmail,"
               "ScammerName,"
               "ScammerIP,"
							 "Subject,"
               "Type,"
               "Subtype,"         
               "TimeStamp,"
               "Payload,"
               "MessageID,"
               "ThreadID) "
               "VALUES "
               "(%s, %s, %s, %s, %s,"
               "%s, %s, %s, %s, %s,"
               "%s, %s, %s)" )
               
               
      parameter = (receivedEmailDic['ReceiverEmail'],\
                   receivedEmailDic['SenderEmail'],\
                   receivedEmailDic['Reply-To'], \
                   receivedEmailDic['RealSenderEmail'],\
                   receivedEmailDic['SenderName'],\
                   receivedEmailDic['SenderIP'],\
									 receivedEmailDic['Subject'],\
                   receivedEmailDic['Type'], \
                   receivedEmailDic['Subtype'], \
                   datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),\
                   sentPayload, \
                   sentEmailDic['Message-ID'], \
                   receivedEmailDic['ThreadID'])        
      
  
      print query
      print parameter
      
      if not self.TEST:
        self.cursor.execute(query, parameter)
        self.mysql.commit()  


  def insertReceivedPaypalNoti(self, emailDic):            
      query = ("INSERT INTO Emails"
               "(OurEmail,"
               "ScammerEmail,"
               "ScammerReplyTo," 
               "RealScammerEmail,"
               "ScammerIP,"
               "Type,"
               "Subject,"
               "TimeStamp," 
               "Payload,"
               "WholePayload, "
               "MessageID, " 
               "ThreadID) "
               "VALUES"
               "(%s, %s, %s, %s, %s, " 
               "%s, %s, %s, %s, %s, "
               "%s, %s)")
               
      parameter = (emailDic['ReceiverEmail'],\
                   emailDic['SenderEmail'],\
                   emailDic['Reply-To'],\
                   emailDic['RealSenderEmail'],\
                   emailDic['SenderIP'],\
                   emailDic['Type'],\
                   emailDic['Subject'],\
                   emailDic['Date'],\
                   emailDic['CorePayload'],\
                   emailDic['Payload'], \
                   emailDic['MessageID'], \
                   emailDic['ThreadID'])

      #print query
      #print parameter
      
      if not self.TEST:
        self.cursor.execute(query, parameter)
        self.mysql.commit()         


  def insertUnknown(self, emailDic):
    query = ("INSERT INTO Emails"
             "(OurEmail,"
             "ScammerEmail,"
             "ScammerReplyTo," 
             "RealScammerEmail,"
             "ScammerIP,"
							"Subject,"
             "Type,"
             "TimeStamp,"
             "Payload,"
             "WholePayload, "
             "MessageID, " 
             "ThreadID) "                              
             "VALUES"
             "(%s, %s, %s, %s, %s, " 
             "%s, %s, %s, %s, %s, "
             "%s, %s)")
             
    parameter = (emailDic['ReceiverEmail'],\
                 emailDic['SenderEmail'],\
                 emailDic['Reply-To'],\
                 emailDic['RealSenderEmail'],\
                 emailDic['SenderIP'],\
								 emailDic['Subject'],\
                 emailDic['Type'],\
                 emailDic['Date'],\
                 emailDic['CorePayload'],\
                 emailDic['Payload'], \
                 emailDic['MessageID'], \
                 emailDic['ThreadID'])
    
    #print query
    #print parameter
    
    if not self.TEST:
      self.cursor.execute(query, parameter)
      self.mysql.commit()    

  '''
  def getCraigslistAd(self, emailDic):
      
      query = ("SELECT ID, PostingTime, City FROM CraigslistAds "
               "WHERE Price=%s AND Email=%s AND Category=%s "
               "ORDER BY ID DESC LIMIT 1")
      parameter = (emailDic['AdPrice'], emailDic['ReceiverEmail'], emailDic['AdCategory'])
      
      self.cursor.execute(query, parameter)
      #self.cursor.execute(query)
      result = self.cursor.fetchall()
      
      if result:
        return int(result[0][0]), result[0][1], result[0][2]
      else:
        return -1, '0000-00-00 00:00:00', ''
	'''

  def getThreadID(self, emailDic, email):
    query = ("SELECT ThreadID FROM Emails "
             "WHERE (ScammerEmail = %s"
             " or ScammerReplyTo = %s"
             " or RealScammerEmail = %s) "
             "AND (OurEmail = %s)")
  
    parameter = (email, 
                 email,
                 email,
                 emailDic['ReceiverEmail'])
  
    self.cursor.execute(query, parameter)
    
    result = self.cursor.fetchall()

    if result:
      print 'found ThreadID for paypal: %s' % result[0][0]
      return result[0][0]  
    else:
      return None


  #######################################################################
  #  PostCraigslistAd.py
  #######################################################################
  def checkCraigslistAccountAvailability(self, baseEmail):
    query = ("SELECT PostingTime FROM CraigslistAds "
             "WHERE BaseEmail=%s "
             "ORDER BY ID DESC LIMIT 1;")
    parameter = [baseEmail]
        
    self.cursor.execute(query, parameter)    
    result = self.cursor.fetchall()      
    
    if result:
      return result[0][0]
    else:
      return None 
  #def
  
  def getCraiglistAvailableHourList(self):
    query = ("SELECT HOUR(PostingTime) FROM CraigslistAds "
             "WHERE Status IS NULL "
             "GROUP BY HOUR(PostingTIme) "
             "ORDER BY COUNT(*) ASC " 
             "LIMIT 10")
        
    self.cursor.execute(query)
    resultRows = self.cursor.fetchall()      
    
    availableHourList = []
    
    
    for row in resultRows:
      availableHourList.append(row[0])          
        
    return availableHourList
  #def

  def getRecentAds(self, targetCity):
    query = ("SELECT Subject FROM CraigslistAds "
             "WHERE PostingTime > (UTC_TIMESTAMP() - INTERVAL 51 HOUR) AND City = %s")
    parameter = [targetCity]
    self.cursor.execute(query, parameter)
    result = self.cursor.fetchall()

    recentlyUsedSubject = list(set([row[0] for row in result]))

    if len(recentlyUsedSubject)>0:
      return recentlyUsedSubject
    else:
      return None



    
  #######################################################################
  #  FlaggedAdChecker
  #######################################################################
  def getAdURL(self):
    query = ("SELECT URL, City, ID, Subject, Category FROM CraigslistAds WHERE URL IS NOT NULL AND Status='Verified'")
    self.cursor.execute(query)
    resultRows = self.cursor.fetchall()      
    
    adList = []    
        
    for row in resultRows:
      adList.append(row)                
        
    return adList
  #def
  
  def updateAdStatus(self, adID, status, option=False):    
    if option==False:
      query = ("UPDATE CraigslistAds "
               "SET Status=%s, DeletedTime=%s "
               "WHERE ID=%s")
    else:
       query = ("UPDATE CraigslistAds2 "
               "SET Status=%s, DeletedTime=%s "
               "WHERE ID=%s")
  
    parameter = (status, datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), adID)
    '''
    query = ("UPDATE CraigslistAds "
             "SET Status=%s "
             "WHERE ID=%s")
    parameter = (status, adID)
    '''
    
    self.cursor.execute(query, parameter)
    self.mysql.commit()
  #def
    
  
  
if __name__ == "__main__":
    mysql = ScamMysql()
    mysql.connect()
    
    
        
    
