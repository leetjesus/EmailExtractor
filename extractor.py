import time, subprocess, django, argparse, re, os, subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'breachpalace.settings')
django.setup()

# Import models
from backend_api.models import *
from databreaches.models import *

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

        with open(self.filename, 'r') as breach_file:
            output = open('extractedEmails.txt', 'a')

            Lines = breach_file.readlines()
            line_count = 0

            for line in Lines:
                line_count += 1
                pattern_match = re.search(validate_email_pattern, line)
                if pattern_match:
                    print(f"Line {line_count}: {pattern_match.group()}")
                    output.write(str(pattern_match.group()) + '\n')
            
            output.close()
        
    def remove_duplicate_emails(self):
        lines = open('extractedEmails.txt', 'r').readlines()
        lines_set = set(lines)  # removing duplicates using set()

        with open('output.txt', 'w') as output:
            for line in lines_set:
                output.write(line)

def main():
    parser = argparse.ArgumentParser(description="Admin path checker")
    parser.add_argument('-f', '--filename', required=True, help='Filename for the breach data you’ll be using.')
    parser.add_argument('-a', '--adminpath', required=True, help='File path for the admin.py panel in Django app.')
    parser.add_argument('-mN', '--modelname', required=True, help='Enter model name for data breach.')
    parser.add_argument('-m', '--modelpath', required=True, help='File path for models.py in Django app.')
    args = parser.parse_args()
    
    # Instantiate EmailExtractor with email_extractor() and remove_duplicate_emails()
    # Extractorobj = EmailExtractor(args.filename)
    # Extractorobj.email_extractor()
    # Extractorobj.remove_duplicate_emails()
    
    model_creator = ModelCreator(args.modelname.capitalize(), args.modelpath, args.adminpath)
    model_creator.verify_paths()
    
if __name__ == "__main__":
    main()
