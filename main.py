#!/usr/bin/env python3
import time, subprocess, django, argparse, re, os, subprocess, sys, time
from chardet.universaldetector import UniversalDetector
from datetime import date
import pathlib, csv, glob
import pandas as pd
from memory_profiler import profile
import cchardet

# Hard coded for now... possibly use environmentle variable
sys.path.append('/home/leetjesus/Desktop/breachpalacev1')
os.environ['DJANGO_SETTINGS_MODULE'] = 'breachpalace.settings'

# Setup Django
django.setup()

from backend_api.models import *
from databreaches.models import *

class BreachDetails:
    # To make life easy you should add metadata from a csv file here instead.
    def __init__(self, modelName, description, breachDate, addedDate, emailCount):
        self.modelName = modelName
        self.description = description
        self.breachDate = breachDate
        self.addedDate = addedDate
        self.emailCount = emailCount

    def create_breach_info(self):
        try:
            latest_id = breachInfo.objects.latest('breach_id').id + 1
        except breachInfo.DoesNotExist:
            latest_id = 0

        print('Creating data breach information...') 
        breachInfo.objects.create(
            breach_id=latest_id,
            name=self.modelName,
            description=self.description,
            BreachDate=self.breachDate,
            AddedDate=self.addedDate,
            emailCount=self.emailCount
        )

class ModelCreator:
    def __init__(self, modelName, modelPath):
        self.modelName = modelName
        self.modelPath = modelPath + '/models.py'
        self.adminPath = modelPath + '/admin.py'

    def create_model(self):
        model_syntax = f"""
class {self.modelName}Breach(models.Model):
    email_id = models.ForeignKey(emailList, on_delete=models.CASCADE)
    email = models.EmailField()
    hashes = models.TextField(null=True, blank=True)
    breach_id = models.ForeignKey(breachInfo, default=0, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '{self.modelName}'
        verbose_name_plural = '{self.modelName}'
        unique_together = ('email_id', 'email')

    def __str__(self):
        return str(self.email_id)\n
"""
        with open(self.modelPath, 'a') as file:
            file.write(model_syntax)
            file.flush()
            os.fsync(file.fileno())  # Ensure file write is completed

    def create_admin_model(self):
        admin_syntax = f"""\n
@admin.register({self.modelName}Breach)
class {self.modelName}BreachAdmin(admin.ModelAdmin):
    fieldsets = [
        ('emaild_id',   {{'fields': ['email_id']}}),
        ('email',       {{'fields': ['email']}}),
        ('hashes',      {{'fields': ['hashes']}}),
        ('breach_id',   {{'fields': ['breach_id']}})
    ]
"""
        with open(self.adminPath, 'a') as file:
            file.write(admin_syntax)
            file.flush() # compel buffer and write to file immediately
            os.fsync(file.fileno())  # Ensure file write is completed

    def make_migrations(self):
        time.sleep(1)
        path = '/home/leetjesus/Desktop/breachpalacev1'
        print("Making migrations...")
        result = subprocess.run(['python', 'manage.py', 'makemigrations', 'databreaches'], capture_output=True, text=True, cwd=path)
        print("Applying migrations...")
        result = subprocess.run(['python', 'manage.py', 'migrate', 'databreaches'], capture_output=True, text=True, cwd=path)

    def verify_paths(self):
        isModel = os.path.isfile(self.modelPath)
        isAdmin = os.path.isfile(self.adminPath)

        if isAdmin and isModel:
           self.create_model()
           self.create_admin_model()
           self.make_migrations()

class SuffixHandler():
    def __init__(self, filename):
        self.filename = filename
    
    def list_wild_card_files(self, wild_card):
        file_list = []

        pwd = os.getcwd()
        
        for file in os.listdir(str(pwd)):
            if file.endswith(str(wild_card)):
                file_list.append(file)

        return file_list

    def detect_wild_card(self):
        if '*.txt' in self.filename:
            file_list = self.list_wild_card_files(wild_card='.txt')
            self.file_opertations = DataSetCrator(filename=None, file_list=file_list)
            self.file_opertations.reading_files()
        elif '*.json' in self.filename:
            print('Json wild card detected!')
            file_list = self.list_wild_card_files(wild_card='.json')
            self.file_opertations = DataSetCrator(filename=None, file_list=file_list)
            self.file_opertations.reading_files()
        elif '*.sql' in self.filename:
            file_list = self.list_wild_card_files(wild_card='.sql')
            self.file_opertations = DataSetCrator(filename=None, file_list=file_list)
            self.file_opertations.reading_files()
        elif '*.csv' in self.filename:
           file_list = self.list_wild_card_files(wild_card='.csv')
           self.file_opertations = DataSetCrator(filename=None, file_list=file_list)
           self.file_opertations.reading_files()
        else:
            self.file_opertations = DataSetCrator(filename=self.filename, file_list=None)
            self.file_opertations.reading_files()
        
class DataSetCrator():
    def __init__(self, filename, file_list):
        self.filename = filename
        self.file_list = file_list
        self.data = {}

    def identify_file_suffix(self, file):
        file_extension_type = pathlib.Path(str(file)).suffix
        
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
        # This should also validate a hash.
        hash_length = len(hash_string)
        
        if hash_length == 32 or hash_length == 35:
            md5_hash_pattern = r'\b([a-f0-9]{32})\b'
            matches = re.findall(md5_hash_pattern, hash_string)
            
            if matches:
                return 'MD5'

        elif hash_length == 40:
            sha1_hash_pattern = r"^[a-fA-F0-9]{40}$"

            matches = re.findall(sha1_hash_pattern, hash_string)
            
            if matches:
                return "SHA-1"
        
        elif hash_length == 64:
            return "SHA-256"
        elif hash_length == 128:
            return "SHA-512"
        else:
            return "Unknown"

    def identify_encoding(self, file):
        # This will open the entire file and parse it..
        # This is why it takes so long for this to run.
        detector = UniversalDetector()
        detector.reset()
        try:
            for line in open(file, 'rb'):
                detector.feed(line)
                if detector.done: break

            detector.close()

            return detector.result['encoding']
        except FileNotFoundError:
            print('File not found.')
            sys.exit()
 
    def filter_by_lengths(self, string_listed):
        result = [] # Store hashes found
        
        # General hash character lengths 
        lengths = [40, 32, 33, 34, 35, 64, 128]
        
        for string in string_listed:
            if len(string.replace("'", "")) in lengths:
                result.append(string.replace("'", "").replace(" ", ""))
        
        return result

    def parsing_lines(self, line, data, file_suffix):
        # The problem here is that it will only parse one hash when it needs to do them all...
        hash_types = {
            'MD5':      'found',
            'SHA-1':    'found',
            'SHA-256':  'found',
            'SHA-512':  'found'
        }
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        pattern_match = re.search(email_pattern, line)
        
        if file_suffix == 'TXT':
            # EVEN IF NO HASHES ARE FOUND IT STILL NEEDS TO ADD IT INTO A DICT OR LIST OF EMAILS
            if pattern_match:
                # What if I add the hash first into the dictionary and do everything after? 
                # Left off here
                email = str(pattern_match.group())
                # Add emails into data dict even if they're a None
                if email not in data:
                    data[email] = {"hashes": set()}

                # Removing all white spaces and add a seperator between strings.
                line = ",".join(line.split())
                
                # Chain multiple characters to be replaced with seperators.
                line = line.replace(" ", ",").replace(":", ",")

                # Convert the line into a list.
                line = line.strip().split(",")
                hash_list = self.filter_by_lengths(string_listed=line)

                for hash_string in hash_list:
                    hash_status = self.identify_hash_type(hash_string=hash_string)
                    if hash_types.get(hash_status):
                        data[email]["hashes"].add(hash_string.replace("'", ''))
            
            return data

        elif file_suffix == 'SQL':
            hash_data = line.strip().split(",")
            if pattern_match:
                email = str(pattern_match.group())
                # Add emails into data dict even if they're a None
                if email not in data:
                    data[email] = {"hashes": set()}
                
                hash_list = self.filter_by_lengths(string_listed=hash_data)
        
                for hash_string in hash_list:
                    hash_status = self.identify_hash_type(hash_string=hash_string)
                    if hash_types.get(hash_status):
                        # hashes are being added here
                        data[email]["hashes"].add(hash_string.replace("'", ''))

            return data

        elif file_suffix == 'JSON':
            if pattern_match:
                email = str(pattern_match.group())
                
                if email not in data:
                    data[email] = {"hashes": ['NNone']}

                return data
        elif file_suffix == 'CSV':
            print('Still in development...')
            
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
        filename = self.generate_file_name()
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['email', 'hashes'])

            for email, hashes in data.items():
                hash_value = '-'.join(hashes['hashes'])
                writer.writerow([email, hash_value]) 

    def compare_keys_remove_duplicates(self):
        # Re-creating the dict only this time combine all hashes found per email
        final_dict = {}

        for self.data in self.data.values():
            for email, data in self.data.items():
                if email not in final_dict:
                    final_dict[email] = {'hashes': set()}  # Initialize an empty set for hashes
                final_dict[email]['hashes'].update(data['hashes'])  # Add hashes, avoiding duplicates

        return final_dict

    def check_hex_character(self, character):
        # Will check if a character is a hex or not
        try:
            int(character, 16)
            return True
        except ValueError:
            pass
    
    def determine_common_encoding(self, hex_value):
        encodings = {
            "ascii": (0x00, 0x7F),               # 7-bit ASCII
            "ISO-8859-1": (0x00, 0xFF), # 8-bit extended Latin-1
            "UTF-8": (0x00, 0x7F),       # UTF-8 overlaps ASCII for single-byte
            "UTF-16)": (0x0000, 0xFFFF),     # Basic Multilingual Plane
            "UTF-32": (0x0000, 0x10FFFF),         # Full Unicode range
            "Windows-1252": (0x00, 0xFF),         # Similar to ISO-8859-1
            "Shift_JIS": (0x81, 0x9F),            # Specific ranges for Japanese
            "EUC-JP": (0xA1, 0xFE),               # Japanese encodings
            "GB2312": (0xA1, 0xFE), # Chinese range
            "Big5": (0xA1, 0xFE),  # Traditional range
        }

        matches = []
        for encoding, (min_val, max_val) in encodings.items():
            if min_val <= hex_value <= max_val:
                matches.append(encoding)
        
        return matches if matches else ["Unknown encoding"]

    def reading_files(self):
        data = {}
        counter = 0
        try:
            # Reading dump multiple files
            if len(self.file_list) != 0:
                # Note: This can be cleaned up in encpasulated within a function
                for fileName in self.file_list:
                    encoder = self.identify_encoding(file=fileName)
                    suffix = self.identify_file_suffix(file=fileName)
                    counter += 1
                    print(f'Currently on {counter} out of {len(self.file_list)} files.')
                    with open(str(fileName), 'r', encoding=str(encoder)) as file:
                        for line in file:
                            self.parsing_lines(line=line, data=data, file_suffix=suffix)
                    
                    self.data[fileName] = data

                updated_dict_data = self.compare_keys_remove_duplicates()
        except TypeError:
            # Reading solo dump file
            if self.filename:
                data = {}
                # identify_encoding function is causing to open the file twice. For very large files this can take up time
                encoder = self.identify_encoding(file=self.filename)
                suffix = self.identify_file_suffix(file=self.filename)
                # ISO-8859-1 fixes the problem with this Vage.GG file
                # File "<frozen codecs>", line 322, in decode
                # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 1222: invalid continuation byte
                try:
                    with open(str(self.filename), 'r', encoding=str(encoder)) as file:
                        for line in file:
                            self.parsing_lines(line=line, data=data, file_suffix=suffix)
                except UnicodeDecodeError as error_text:
                    # Find hex within error text using regex
                    hex_pattern = r"\b0x[0-9a-fA-F]+\b"
                    matches = re.findall(hex_pattern, str(error_text))
                    hex_validation_staus = self.check_hex_character(character=matches[0])
                    if hex_validation_staus == True:
                        hex_value = int(matches[0], 0)
                        encoder = self.determine_common_encoding(hex_value=hex_value)
                        
                        with open(str(self.filename), 'r', encoding=str(encoder[0])) as file:
                            for line in file:
                                self.parsing_lines(line=line, data=data, file_suffix=suffix)
                   
                        self.data[self.filename] = data
                    else:
                        pass
                
                updated_dict_data = self.compare_keys_remove_duplicates()
            else:
                print('Problem occurred. Exiting.')
        except UnicodeDecodeError:
            print('There was a unicode error!')
    
        print(data)
        # print('Done')

        # self.write_data_set(updated_dict_data)

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

        print(f'Emails read succesfully: {len(email_list)}')
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
            # This will change any NaN = (Number not found (pandas)) into a None instead
            hashes_list = chunk['hashes'].apply(lambda x: None if pd.isna(x) else x)
            
            # (This should not be a fixed value)
            breach_id_instance = breachInfo.objects.get(name='HelloWorld')
            for email, hashes in zip(emails, hashes_list):
                if email in all_emails_set and email in email_dict:
                    email_instance = email_dict[email]
                    objects.append(breachName(
                        email_id=email_instance, 
                        email=email_instance.email, 
                        hashes=hashes,
                        breach_id=breach_id_instance
                    ))

        # This breaks when the file is to big.
        try: 
            breachName.objects.bulk_create(objects)
            print('Done adding emails and hashes...')
        except django.db.utils.IntegrityError as e:
            print('Duplicates were found. Exiting...')
            print(e)

    def verify_modelname(self):
        # Will check to see if the model name does in fact exist before sending the dataset into the model
        try:
            breachName = globals()[str(self.modelName)]
            return 'found'
        except KeyError:
            return 'not_found'

def main():
    parser = argparse.ArgumentParser(description="This script is to be used for creating datasets from data dumps.")
    parser.add_argument('-f', '--filename', help='Enter breach data filename, emails, passwords and lines will be extracted from this file.')
    parser.add_argument('-m', '--modelname', help='Enter the name of a pre-existing model that will be used for receiving data from a dataset.')
    parser.add_argument('-d', '--dataset', help='Enter dataset filename which will be used for sending information to django.')
    
    parser.add_argument('-n', '--newmodel', help='The name of the new model to be created.')
    parser.add_argument('-mP', '--modelPath', help='Path of where the model and admin path are located')
    parser.add_argument('-i', '--modelinfo', help='Description information for new model being created')
    parser.add_argument('-bd', '--breachdate', help='The date of when the breach occurred')
    parser.add_argument('-ad', '--addeddate', help='The date of when you created this model')
    parser.add_argument('-ec', '--emailcount', help='The total email count found within this breach')

    args = parser.parse_args()

    if args.dataset:
        database_operations = BulkEmailAdder(filename=args.dataset, modelName=args.modelname)
        value = database_operations.verify_modelname()
        if value == 'found':
            database_operations.main()
        elif value == 'not_found':
            print('The model name you entered was not found in the django database. Please create the model first.')
            sys.exit()

    elif args.filename:
        print('Parsing file(s) specified.')
        handle_suffix = SuffixHandler(filename=args.filename)
        handle_suffix.detect_wild_card()
    elif args.newmodel:
        print('Creating breach info first...')
        newModel = BreachDetails(modelName=args.newmodel, description=args.modelinfo, breachDate=args.breachdate, addedDate=args.addeddate, emailCount=args.emailcount)
        newModel.create_breach_info()
        
        print('Creating django model now...')
        modelPath = ModelCreator(modelName=args.newmodel, modelPath=args.modelPath)
        modelPath.verify_paths()

if __name__ == "__main__":
    main()
