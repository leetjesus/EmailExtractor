import time, subprocess, django, argparse, re, os, subprocess, sys
from chardet.universaldetector import UniversalDetector
import pathlib, csv
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'breachpalace.settings')
# django.setup()

# Import models
# from backend_api.models import *
# from databreaches.models import *

class ModelCreator:
    def __init__(self, modelName, modelPath, adminPath):
        self.modelName = modelName
        self.modelPath = modelPath
        self.adminPath = adminPath

    def create_model(self):
        model_syntax = f"""
class {self.modelName}Breach(models.Model):
    email_id = models.ForeignKey(emailList, on_delete=models.CASCADE)
    email = models.EmailField()
    password = models.TextField()
    breach_id = models.ForeignKey(breachInfo, on_delete=models.CASCADE)

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
        ('breach_id',   {{'fields': ['email_id']}}),
        ('Name',        {{'fields': ['email']}}),
        ('Description', {{'fields': ['password']}}),
        ('Breach Date', {{'fields': ['breach_id']}})
    ]
"""
        with open(self.adminPath, 'a') as file:
            file.write(admin_syntax)
            file.flush() # compel buffer and write to file immediately
            os.fsync(file.fileno())  # Ensure file write is completed

    def create_breach_info(self):
        try:
            latest_id = breachInfo.objects.latest('breach_id').id + 1
        except breachInfo.DoesNotExist:
            latest_id = 0 
        
        breachInfo.objects.create(
            breach_id=latest_id, 
            name=self.modelName, 
            description='Hello worldTesting', 
            BreachDate='2013-10-04', 
            AddedDate='2013-12-04', 
            emailCount='2900'
        )

    def make_migrations(self):
        # using subprocess because call_command wont identify file changes fast enough
        time.sleep(1)
        print("Making migrations...")
        result = subprocess.run(['python', 'manage.py', 'makemigrations', 'databreaches'], capture_output=True, text=True)
        print("Applying migrations...")
        result = subprocess.run(['python', 'manage.py', 'migrate', 'databreaches'], capture_output=True, text=True)

    def verify_paths(self):
        isModel = os.path.isfile(self.modelPath)
        isAdmin = os.path.isfile(self.adminPath)

        print(f"Model path exists: {isModel}")
        print(f"Admin path exists: {isAdmin}")

        if isAdmin and isModel:
           self.create_model()
           self.create_admin_model()
           self.create_breach_info()
           self.make_migrations()

class EmailExtractor:
    def __init__(self, filename):
        self.filename = filename

    def email_extractor(self):
        validate_email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        valid_filenames = []
        
        print('Validating filenames....')
       
       # Checking if file's exist first
        for filename in self.filename:
            check_file = os.path.isfile(filename)
            if check_file:
                valid_filenames.append(filename)
        
        print(valid_filenames)
        user_validation = input('Are the found files correct? Y/N:')
          
        line_count = 0

        if user_validation.upper() == 'Y' or 'YES':
            # Determine the file uni code type
            file_info = {}
            detector = UniversalDetector()
            for filename in valid_filenames:
                detector.reset()
                print('Detetcing unicode...')
                for line in open(filename, 'rb'):
                    detector.feed(line)
                    if detector.done: break
                detector.close()
                file_info[filename] = detector.result['encoding']

            for file, uni_type in file_info.items():
                # Detect if the file extension contains a csv or if its a txt file
                file_exten_check = pathlib.Path(file).suffix
                if file_exten_check == '.csv':
                    # CSV READING
                    with open(file, 'r', encoding=uni_type) as breach_file:
                        csvreader = csv.reader(breach_file)
                        output = open('BULKEXTRACT.txt', 'a')
                        for line in csvreader:
                            for i in line:
                                pattern_match = re.search(validate_email_pattern, i)
                                if pattern_match:
                                    line_count += 1
                                    output.write(str(i) + '\n')
                        output.close()
                        print(f'Completed {file}: Email count: {line_count}')

                elif file_exten_check == '.txt':
                    # TXT READING
                    with open(file, 'r', encoding=uni_type) as breach_file:
                        output = open('BULKEXTRACT.txt', 'a')
                        Lines = breach_file.readlines()
                        for line in Lines:
                            line_count += 1
                            pattern_match = re.search(validate_email_pattern, line)
                            if pattern_match:
                                output.write(str(pattern_match.group()) + '\n')
                        output.close()
                        print(f'Completed {file}: Email count: {line_count}')
        else:
            print("Enter the filenames in correctly.")
        
    def remove_duplicate_emails(self):
        lines = open('BULKEXTRACT.txt', 'r').readlines()
        lines_set = set(lines)  # removing duplicates using set()
        
        line_count = 0
        
        with open('output.txt', 'w') as output:
            for line in lines_set:
                line_count += 1
                output.write(line)

        print(f'Total email count without duplicates: {line_count}')

def main():

    def list_of_strings(arg):
        return arg.split(',')

    parser = argparse.ArgumentParser(description='Checking to see status')
    parser.add_argument('-f', '--filename', action='store_true', help='Enter a filename for the breache(s) files.')
    parser.add_argument('-m', '--model', action='store_true', help='Enable model mode')
    parser.add_argument('-e', '--email', action='store_true', help='Enable sending output.txt to django db(models).')
    
    parser.add_argument('-fP', '--filepath', type=list_of_strings, help='Filename for the breach data you’ll be using.')
    parser.add_argument('-aP', '--adminpath', help='File path for the admin.py panel in Django app.')
    parser.add_argument('-mN', '--modelname', help='Enter model name for data breach.')
    parser.add_argument('-mP', '--modelpath', help='File path for models.py in Django app.')
        
    args = parser.parse_args()
    
    if args.filename and args.model and args.email:
        model_creator = ModelCreator(args.modelname.capitalize(), args.modelpath, args.adminpath)
        model_creator.verify_paths()
        
        Extractorobj = EmailExtractor(args.filename)
        Extractorobj.email_extractor()
        Extractorobj.remove_duplicate_emails()
        
        subprocess.run(['python', 'email_adder.py', '-mN', f'{args.modelname}', '-e', 'true'])

    elif args.filename and args.model:
        model_creator = ModelCreator(args.modelname.capitalize(), args.modelpath, args.adminpath)
        model_creator.verify_paths()

        Extractorobj = EmailExtractor(args.filename)
        Extractorobj.email_extractor()
        Extractorobj.remove_duplicate_emails()
    
    elif args.filename and args.email:
        print('Models needed please try again...')
    
    elif args.filename:
        Extractorobj = EmailExtractor(args.filepath)
        Extractorobj.email_extractor()
        Extractorobj.remove_duplicate_emails()
    
    elif args.model:
        model_creator = ModelCreator(args.modelname.capitalize(), args.modelpath, args.adminpath)
        model_creator.verify_paths()
    
    elif args.email:
        subprocess.run(['python', 'email_adder.py', '-mN', f'{args.modelname}', '-e', 'true'])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\nExiting...')
