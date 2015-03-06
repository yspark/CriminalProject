
import ScamMysql
import httplib2, re

class FlaggedAdChecker:
  def __init__(self):
    # mysql
    self.mysql = ScamMysql.ScamMysql()
    self.mysql.connect() 

    #self.driver = webdriver.Chrome()

  # end def __init__()
  
  def done(self):
    #self.driver.quit()
        
    self.mysql.disconnect()      
  # end def done()
  
  def check(self):
    # get URLs of ads
    adList = self.mysql.getAdURL()
    deletedAdDic = {}
    
    for ad in adList:
      adURL = ad[0]
      adCity = ad[1]
      adID = ad[2]
      adSubject = ad[3]
      adCategory = ad[4]
     
      if 'http' not in adURL:
        continue 
      #print adCity, adURL
      
      http = httplib2.Http()
      headers, body = http.request(adURL)
        
      if 'This posting has expired' in body:
        self.mysql.updateAdStatus(adID, 'Expired')
        print '(%d, %s) is expired' % (int(adID), adCity)
      elif ('This posting has been flagged for removal' in body) or ('Page Not Found' in body):        
        self.mysql.updateAdStatus(adID, 'Deleted')
        
        if adCity in deletedAdDic.keys():
          deletedAdDic[adCity] = deletedAdDic[adCity] + 1          
        else:
          deletedAdDic[adCity] = 1          
        #endif
        print '(%d, %s, %s, %s) is blocked' % (int(adID), adCity, adSubject, adCategory)
      #endif        
    #end for
    
    for city in deletedAdDic.keys():
      if deletedAdDic[city] > 3:
        print '%s blocked' % city
    
  #end def
  
# end class Craigslist



if __name__ == '__main__':
  TEST = False
              

  
  flaggedAdChecker = FlaggedAdChecker()

  flaggedAdChecker.check()
  flaggedAdChecker.done()

       
    
