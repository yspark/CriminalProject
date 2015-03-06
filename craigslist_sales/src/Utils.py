import os
import LocalDef
import re

# load Craigslist links to visit
def load_url_list(url_file):
    
    url_list = []
    
    with open(url_file) as url_f:
      url_lines = url_f.readlines()
    
    for line in url_lines:
      if len(line) < 3 or 'EOF' in line or line is None: break
      url_list.append(line.rstrip())
    #endif

    return url_list
#end def

# laod proxy list 
def load_proxy_list(proxy_file):
    proxy_list = []
    
    with open(proxy_file) as proxy_f:
      proxy_lines = proxy_f.readlines()
    
    for line in proxy_lines:
      if len(line) < 3 or 'EOF' in line or line is None: break
      proxy_list.append(line.rstrip())
    #endif

    return proxy_list
#end def



def load_email_list(email_file):
  email_list = []
  password_list = []
  
  with open(email_file) as email_f:
    email_lines = email_f.read().split('\r')
  
  for line in email_lines:  
    if line[0] == '#': continue
    
    line_list = line.rstrip().split('\t')
  
    email_list.append(line_list[0])
    password_list.append(line_list[1])
  
  return email_list, password_list


def check_duplicate_process(process_name):
  
  tmp = os.popen("ps -Af").read()
  proc_count = tmp.count(process_name)

  print proc_count

  if proc_count > LocalDef.DUPLICATE_PROCESS_NUM:
    print(proc_count, ' processes running of ', process_name, 'type')
    return True
  else:
    return False
  
  
def get_num(x):
  return int('0'+''.join(ele for ele in x if ele.isdigit()))



def remove_index_of_invalid_street_addr(street_addr_list):
  index_to_remove = []
  
  for i in range(len(street_addr_list)):
    street_addr_list[i] = street_addr_list[i].strip()
    
    if check_addr_validity(street_addr_list[i]) == False:
      index_to_remove.append(i)
    
  return index_to_remove


def check_addr_validity(street_addr):
  word_list = ''.join(c if c.isalnum() else ' ' for c in street_addr).split()
  
  if not word_list: return False
    
  if not word_list[0][0].isdigit():
    return False
  elif len(word_list) <= 2 or len(street_addr) <= 6:
    return False
  elif 'th' in word_list[0] or 'st' in word_list[0] or 'nd' in word_list[0] or 'rd' in word_list[0]:
    return False
  
  return True  
  
  
def remove_html_tag(html):
  tag_re = re.compile(r"<[^>]+>")
  return tag_re.sub('', html)  
  