import time, subprocess, django, argparse, re, os, subprocess, sys
from chardet.universaldetector import UniversalDetector
from datetime import date
import pathlib, csv, glob

# Hard coded for now... possibly use environmentle variable
sys.path.append('/home/leetjesus/Desktop/breachpalacev1')
os.environ['DJANGO_SETTINGS_MODULE'] = 'breachpalace.settings'

# Setup Django
django.setup()

from backend_api.models import *
from databreaches.models import *

class DataSetCrator():
    def __init__(self, filename):
        self.filename = filename
    
    def identify_file_suffix(self):
        file_extension_type = pathlib.Path(str(self.filename)).suffix
        
        if file_extension_type == '.csv':
            return 'CSV'
        elif file_extension_type == '.txt':
            return 'TXT'
        elif file_extension_type == '.sql':
            return 'SQL'
        elif file_extension_type == '.json':
            return 'JSON'

    def identify_hash_type(self, hash_string):
        """Identifies the type of a hash based on its length."""
        hash_length = len(hash_string)

        if hash_length == 32 or hash_length == 35:
            md5_hash_pattern = r'\b([a-f0-9]{32})\b'
            matches = re.findall(md5_hash_pattern, hash_string)
            
            if matches:
                return 'MD5'

        elif hash_length == 40:
            return "SHA-1"
        elif hash_length == 64:
            return "SHA-256"
        elif hash_length == 128:
            return "SHA-512"
        else:
            return "Unknown"

    def identify_encoding(self):
        detector = UniversalDetector()
        detector.reset()
        
        for line in open(self.filename, 'rb'):
            detector.feed(line)
            if detector.done: break
        
        detector.close()
        
        return detector.result['encoding']

    def identify_password(self, line):
        # To-do: Create a better regex for finding passwords
        password_pattern = r'(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^a-zA-Z0-9])(?!.*@)([A-Za-z0-9!@#$%^&*()_+={}\[\]:;"\'<>,.?/~`-]{6,})'

        password_match = re.search(password_pattern, line)
        if password_match:
            password = str(password_match.group(1))
            return password 

    def parsing_lines(self, line, file_suffix, data):
        hash_types = {
            'MD5':      'found',
            'SHA-1':    'found',
            'SHA-256':  'found',
            'SHA-512':  'found'
        }
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        
        pattern_match = re.search(email_pattern, line)
        
        if file_suffix == 'TXT':
            if pattern_match:
                email = str(pattern_match.group())
                password = self.identify_password(line=line)
                
                if email not in data:
                    data[email] = {"passwords": [], "line": None}

                if password not in data[email]['passwords']:
                    data[email]['passwords'].append(password)
                
                data[email]["line"] = str(line)

                return data

        elif file_suffix == 'SQL':
            hash_data = line.strip().split(",")
            for hash_string in hash_data:
                hash_type = self.identify_hash_type(hash_string)
                if pattern_match and hash_types.get(hash_type) == 'found':
                    email = str(pattern_match.group())
                    
                    if email not in data:
                        data[email] = {"hashes": set(), "line": None} 

                    data[email]["hashes"].add(hash_string.replace("'", ''))
                    data[email]["line"] = str(line)

    def generate_file_name(self):
        today = date.today()
        base_name = f"{today}-dataset"
        extension = ".csv"

        file_name = f"{base_name}{extension}"
        counter = 0

        while os.path.exists(file_name):
            file_name = f"{base_name}{counter}{extension}"
            
            counter += 1

        return file_name

    def write_data_set(self, data):
        for email, hashes in data.items():
            string = ''.join(hashes['hashes'])
            # print(string[1:].replace(" ", '-'))

        filename = self.generate_file_name()

        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['email', 'hashes', 'line'])

            for email, hashes in data.items():
                hash_value = ''.join(hashes['hashes'])
                writer.writerow([email, hash_value[1:].replace(" ", '-'), hashes['line']]) 

    def reading_files(self):
        data = {}
        encoder = self.identify_encoding()
        file_suffix = self.identify_file_suffix()
        
        count = 0
        
        with open(str(self.filename), 'r', encoding=str(encoder)) as file:
            lines = file.readlines()
            for line in lines:
                self.parsing_lines(line=line, file_suffix=file_suffix, data=data)
            
        self.write_data_set(data)

class BulkEmailAdder:
    def __init__(self, modelName, filename):
        self.modelName = modelName
        self.filename = filename
        self.self = self

    def read_emails(self):
        # Using chunking here
        email_list = []
        for chunk in pd.read_csv(self.filename, chunksize=1000):
            email = chunk["email"]
            for email in email:
                email_list.append(email)

        return email_list

    def main(self):
        objects = []
    
        breachName = globals()[str(self.modelName)]

        og_emails = self.read_emails()

        # Grabbing the latest email id for generating new emails
        try:
            latest_id = emailList.objects.latest('email_id').id
        except emailList.DoesNotExist:
            latest_id = 0


        # # Check to see if the og_emails exist within the table emailList
        existing_emails = set(emailList.objects.filter(email__in=og_emails).values_list('email', flat=True))

        new_emails = []

        for email in og_emails:
            # Check to see any emails within og_emails exist in existing_emails
            if email in existing_emails:
                pass
            else:
                latest_id += 1
                new_emails.append(emailList(email=email, email_id=latest_id))

        ######## This code will then write to the table emailList. ###########
        if new_emails:
            emailList.objects.bulk_create(new_emails, ignore_conflicts=True)
            print(f'ADDED {len(new_emails)} to emailList table')

        all_emails_new_and_exisisting = emailList.objects.filter(email__in=og_emails)
        
        email_dict = {item.email: item for item in emailList.objects.all()}
        all_emails_set = {item.email for item in all_emails_new_and_exisisting}
        
        # Chunking here
        for chunk in pd.read_csv(self.filename, chunksize=500):
            emails = chunk['email']
            lines = chunk['line']
            hashes_list = chunk['hashes']

            for email, line, hashes in zip(emails, lines, hashes_list):
                if email in all_emails_set and email in email_dict:
                    email_instance = email_dict[email]
                    objects.append(breachName(
                        email_id=email_instance, 
                        email=email_instance.email, 
                        hashes=hashes,
                        line=line
                    ))

        # Before adding bulk check for duplicate emails or convert the email in email_id instead...
        try:  
            breachName.objects.bulk_create(objects)
        except django.db.utils.IntegrityError as e:
            print(e)

# database_operations = BulkEmailAdder(filename='2024-10-29-dataset.csv', modelName='EmailhashtestBreach')
# database_operations.main()

# file_opertations = DataSetCrator(filename='intimshop.ru.sql')
# file_opertations.reading_files()
