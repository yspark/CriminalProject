import random
import datetime
import LocalDef


class PersonalInformation:
  def __init__(self):
    self.last_name_file = './data/name_last.txt'
    self.first_name_file = './data/name_first.txt'
    self.street_address_file = './data/address_street.txt'
    self.city_state_file = './data/address_city_state.txt'
    self.occupation_file = './data/occupation.txt'
  
    self.phone = ''
    self.name = ''
    
  
  def generate_name(self):
    return self.generate_first_name() + ' ' + self.generate_last_name()


  def generate_first_name(self):
    with open(self.first_name_file) as f_first_name:
      name_list = f_first_name.readlines()
      first_name = name_list[random.randint(0, len(name_list)-1)].split()[0].lower()
      first_name = first_name[:1].upper() + first_name[1:]
      
      if self.name == '':
        self.name = first_name
      
    return first_name
  
  
  def generate_last_name(self):
    with open(self.last_name_file) as f_last_name:
      name_list = f_last_name.readlines()
      last_name = name_list[random.randint(0, len(name_list)-1)].split()[0].lower()
      last_name = last_name[:1].upper() + last_name[1:]
      
    return last_name
  
  
  def generate_address_phone(self):
    street_number = str(random.randint(1000, 13000))
    
    with open(self.street_address_file, 'rU') as f_sa:
      list = f_sa.readlines()
      street_address = list[random.randint(0, len(list)-1)]
  
      street_address = street_address.replace('#', '')
      street_address = street_address.replace('(part)', '')
      street_address = street_address.replace('\n', '')
      
      
    with open(self.city_state_file, 'rU') as f_cs:
      list = f_cs.readlines()
      
      
      while True:
        row = list[random.randint(0, len(list)-1)].split('\t')
      
        if len(row) < 4: continue
        
        city = row[0]
        state = row[1]
        zip = row[2].zfill(5)
        
        try:
          area_code = row[3].split()[0][:3]
        except:
          area_code = '403'
          
        if len(area_code) < 3:
          continue
        else:
          area_code = area_code[:3]
        
        break
      #endwhile
        
    phone_number = area_code + '-' + str(random.randint(200, 999)) + '-' + str(random.randint(2000, 9999))  
    address = street_number + ' ' + street_address + ', ' + city + ', ' + state + ' ' + zip
    
    if self.phone == '':
      self.phone = phone_number
    
    return address, self.phone
  
  def generate_date_of_birth(self):
    return str(random.randint(1,12)) + '/' + str(random.randint(1,30)) + '/' + str(random.randint(1960,1984)) 
  
  def generate_martial_status(self):
    answer = ['Yes', 'Married', 'yes', 'married']
    return answer[random.randint(0, len(answer)-1)]
    
  def generate_reason_for_leaving(self):
    answer = ['Got a new job', 'Family', '-', 'Personal', 'private', 'personal problem', 'Moving', 'New job', 'New workplace']
    return answer[random.randint(0, len(answer)-1)]
    
  def generate_current_rent(self):
    return str(random.randint(130, 250)) + '0'
    
  def generate_family_number(self):
    return str(random.randint(2, 4))
    
  def generate_pet(self):
    answer = ['no', 'No', '1 dog', '2 dogs', '1 cat', '2 cats', 'one dog', 'two dogs', 'A cat', '1 cat', '2 cats']
    return answer[random.randint(0, len(answer)-1)]  
  
  def generate_pet_detail(self):
    answer = ['Small, nice, quiet', 'Reasonably small and nice', 'Not that big, nice', 'Small, quiet', 'Quiet, small', 'Nice, quiet, small', 
              'Nice, quiet, small', 'Quiet and nice', 'Small and nice', 'Not big, good', 'Small, good', 'Small and good', 'Quiet and good', 
              'Quiet, small and good', 'Small, good and quiet']
    return answer[random.randint(0, len(answer)-1)]  

  
  def generate_car(self):
    answer = ['1', '2', '3', '1 car', '2 cars', '3 cars', 'One car', 'Two cars', 'Three cars']
    return answer[random.randint(0, len(answer)-1)]  
  
  def generate_occupation(self):
    with open(self.occupation_file) as f_occupation:
      occupation_list = f_occupation.readlines()
      occupation = occupation_list[random.randint(0, len(occupation_list)-1)]
    
    return occupation[:len(occupation)-1]
  
  def generate_movein(self):
    move_term = random.randint(14, 60)
    movein = datetime.date.today() + datetime.timedelta(days=move_term)
    
    return movein.strftime("%m/%d/%y")
    
  def generate_lease_term(self):
    answer = ['1 year', '1 Year', '12 months', '1-year', '1-Year', '2 years', '2-year', 'Two years']
    return answer[random.randint(0, len(answer)-1)]  

  def generate_deposit(self):
    answer = ['1 month + security deposit', '1 month rent + security deposit', 'As you request, up to 2 month rent + security deposit']
    return answer[random.randint(0, len(answer)-1)]  

  def generate_payment_date(self):
    payment_term = random.randint(1, 8)
    payment_date = datetime.date.today() + datetime.timedelta(days=payment_term)
    return payment_date.strftime("%m/%d/%y")  

  def generate_time_to_call(self):
    answer = ['Anytime before 10PM', 'Before 6PM', 'Between 9AM and 6PM', 
              'Anytime', 'anytime', 'Before 7PM', 'before 8pm', 
              'Anytime before 9pm', 'Anytime before 8pm', 'Anytime before 7pm', 
              'Before 6pm', 'Before 8PM', 'Before 9PM']
    return answer[random.randint(0, len(answer)-1)]  

  def generate_smoke(self):
    answer = ['No', 'no']
    return answer[random.randint(0, len(answer)-1)]  

  def generate_drink(self):
    answer = ['No', 'Yes', 'Little', 'yes']
    return answer[random.randint(0, len(answer)-1)]  
  
  def generate_kids(self):
    num = random.randint(1, 3)
    return 'Yes, ' + str(num) + ' kids'
  
  def generate_age(self):
    return str(random.randint(30, 60))  
  
  def generate_key_date(self):
    answer = ['On move-in date', 'Doesn\' matter', 'Any time', 'Anytime', 'Any date']
    return answer[random.randint(0, len(answer)-1)]  
  
  def generate_income(self):
    return '$'+str(random.randint(8, 15)) + '0000 / year'

  
  
  
    
if __name__ == "__main__":
  p = PersonalInformation()

  print p.generate_name()
  print p.generate_address_phone()
  
  
  
  
  
  
  
  
  
  
  
  