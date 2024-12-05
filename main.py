import time, subprocess, django, argparse, re, os, subprocess, sys, time
from chardet.universaldetector import UniversalDetector
from datetime import date
import pathlib, csv, glob
import pandas as pd
from memory_profiler import profile

# Hard coded for now... possibly use environmentle variable
sys.path.append('/home/leetjesus/Desktop/breachpalacev1')
os.environ['DJANGO_SETTINGS_MODULE'] = 'breachpalace.settings'

# Setup Django
django.setup()

from backend_api.models import *
from databreaches.models import *

class BreachDetails:
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

    def identify_encoding(self, file):
        # Handle multiple files here
        # Left off here
        detector = UniversalDetector()
        detector.reset()
        
        for line in open(file, 'rb'):
            detector.feed(line)
            if detector.done: break
        
        detector.close()
        
        return detector.result['encoding']

    def hash_validation(self, hash_string):
        # Validating hashes and removing any false flags
        md5_hash_pattern = r'\b[a-f0-9]{32}\b'
        if len(hash_string) > 35:
            match = re.findall(md5_hash_pattern, hash_string)
            if len(match) > 0:
                match = '-'.join(match) 
                return match
            else:
                return None
        else:
            return hash_string
            
    def parsing_lines(self, line, data, file_suffix):
        hash_types = {
            'MD5':      'found',
            'SHA-1':    'found',
            'SHA-256':  'found',
            'SHA-512':  'found'
        }
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        # file_suffix = self.identify_file_suffix()
        pattern_match = re.search(email_pattern, line)

        # Working with TXT dump files
        if file_suffix == 'TXT':
            if pattern_match:
                email = str(pattern_match.group())
                
                if email not in data:
                    data[email] = {"hashes": ['NNone']}

                return data

        # Working with SQL files
        elif file_suffix == 'SQL':
            hash_data = line.strip().split(",")
            for hash_string in hash_data:
                hash_type = self.identify_hash_type(hash_string)
                if pattern_match and hash_types.get(hash_type) == 'found':
                    # Validatie the hash before adding into a file
                    hash_string = self.hash_validation(hash_string=hash_string)
                
                    email = str(pattern_match.group())
            
                    if email not in data:
                        data[email] = {"hashes": set()} 

                    # hashes are being added here
                    try:
                        data[email]["hashes"].add(hash_string.replace("'", ''))
                    except AttributeError as e:
                        # If a None is returned from hash_validation then don't add anything into the csv file
                        pass

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
            writer.writerow(['email', 'hashes'])

            for email, hashes in data.items():
                hash_value = ''.join(hashes['hashes'])
                writer.writerow([email, hash_value[1:].replace(" ", '-')]) 

    def compare_keys_remove_duplicates(self):
        # Re-creating the dict only this time combine all hashes found per email
        final_dict = {}

        for self.data in self.data.values():
            for email, data in self.data.items():
                if email not in final_dict:
                    final_dict[email] = {'hashes': set()}  # Initialize an empty set for hashes
                final_dict[email]['hashes'].update(data['hashes'])  # Add hashes, avoiding duplicates

        return final_dict

    def reading_files(self):
        data = {}
        count = 0
        try:
            # Writing to multiple files
            if len(self.file_list) != 0:
                # This can be cleaned up in encpasulated within a function
                for fileName in self.file_list:
                    encoder = self.identify_encoding(file=fileName)
                    suffix = self.identify_file_suffix(file=fileName)
                    with open(str(fileName), 'r', encoding=str(encoder)) as file:
                        for line in file:
                            self.parsing_lines(line=line, data=data, file_suffix=suffix)
                    
                    self.data[fileName] = data
                updated_dict_data = self.compare_keys_remove_duplicates()
        except TypeError:
            # Writing solo files
            if self.filename:
                encoder = self.identify_encoding(file=self.filename)
                suffix = self.identify_file_suffix(file=self.filename)
                with open(str(self.filename), 'r', encoding=str(encoder)) as file:
                    for line in file:
                        self.parsing_lines(line=line, data=data, file_suffix=suffix)
                    
                self.data[self.filename] = data
                updated_dict_data = self.compare_keys_remove_duplicates()
            else:
                print('Nothing was found')
        self.write_data_set(updated_dict_data)

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
            # The breachID instance will need to be changed accroding to the model name being used.. Fixed value for now
            # Fix this value
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

# @profile used for reading mem usage
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
        file_opertations = DataSetCrator(filename=args.filename)
        # This logic here needs to change a bit...
        file_opertations.multiple_files_check()
        file_opertations.reading_files()
    elif args.newmodel:
        print('Creating breach info first...')
        newModel = BreachDetails(modelName=args.newmodel, description=args.modelinfo, breachDate=args.breachdate, addedDate=args.addeddate, emailCount=args.emailcount)
        newModel.create_breach_info()
        
        print('Creating django model now...')
        modelPath = ModelCreator(modelName=args.newmodel, modelPath=args.modelPath)
        modelPath.verify_paths()

if __name__ == "__main__":
    # main()
    handle_suffix = SuffixHandler(filename='*.sql')
    handle_suffix.detect_wild_card()
