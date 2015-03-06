
#######################################################
# global constants
#######################################################


# Gmail SMTP-RELAY account
IMAP_ACCOUNT = 'umdcriminalproject@gmail.com'
IMAP_PASSWD = 'umdscamscam'

SMTP_RELAY_ACCOUNT = 'yspark@stakemail.net'
SMTP_RELAY_PASSWD = 'umdscamscam'

# input files
LEFTOVER_FILE = './data/leftover.txt'
URL_FILE = './data/url.txt'
PROXY_FILE = './data/proxy_list.txt'
PROXY_FLAG_FILE = './data/proxy_flag_list.txt'
MANUAL_RULE_FILE = './data/manual_rule.txt'
EMAIL_FILE = './data/email_account.txt'


# Realtor URL list files
ZILLOW_URL_FILE = './data/zillow_url.txt'
TRULIA_URL_FILE = './data/trulia_url.txt'
REALTOR_URL_FILE = './data/realtor_url.txt'
YAHOO_URL_FILE = './data/yahoo_url.txt'
HOMES_URL_FILE = './data/homes_url.txt'

# Vacation URL list files
VRBO_URL_FILE = './data/vrbo_url.txt'


# Number of pages to read in
AD_PAGE_NUM = 100


# ad flag status
AD_STATUS = {0:'Active', 1:'Flagged', 2:'Deleted', 5:'Legitimate'}
SCAM_LEVEL = {0:'Non-suspicious', 1:'Suspicious, monitoring', 100:'Non-scam', 101:'Scam', 102:'Scam with rent applciation'}

# Rent application
LAST_RENT_APPLICATION = 'm'
