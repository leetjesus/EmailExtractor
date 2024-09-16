import time, subprocess, django, argparse, re, os, subprocess, sys

sys.path.append('/home/leetjesus/Desktop/breachpalacev1')
os.environ['DJANGO_SETTINGS_MODULE'] = 'breachpalace.settings'
django.setup()

# Import models
from backend_api.models import *
from databreaches.models import *

class AddEmails:
    def __init__(self, modelName):
        self.self = self
        self.breach_name = modelName
        
    def send_emails_to_db(self):
        with open('output.txt', 'r') as file:
            lines = file.readlines()

        og_emails = list(set(line.strip() for line in lines))

        try:
            # Giving each and every email in our extractedEmails.txt file a unique email_id
            latest_id = emailList.objects.latest('email_id').id
        except emailList.DoesNotExist:
            latest_id = 0

        # Fetch the data breach information (create instance)
        try:
            breach_information = breachInfo.objects.get(name=str(self.breach_name))
        except breachInfo.DoesNotExist:
            print(f'Error: {self.breach_name} not found.')

        # Check to see if any of our emails in extractedEmails.txt where found within our emailList table(model).
        existing_emails = set(emailList.objects.filter(email__in=og_emails).values_list('email', flat=True))
        
        # New emails that will be added.
        new_emails = []
        for email in og_emails:
            if email in existing_emails:
                pass
            else:
                # Create new email instance here and add to list.
                latest_id += 1
                new_emails.append(emailList(email=email, email_id=latest_id))

        if new_emails:
            emailList.objects.bulk_create(new_emails, ignore_conflicts=True)
            print(f'ADDED {len(new_emails)} to emailList table')

        # Now this will add all emails that were newly created and that already exist into the breach Model (table)
        all_emails = emailList.objects.filter(email__in=og_emails)
        breach_email_entries = []
        
        # same problem different format.... it's not detecting the file fast enough... it's not detecting BellBreach
        # SO this python script needs to refresh itself... otherwise it won't be able to detect the changes... because this is still going
        # On old import module data 
        breachName = globals()[f'{self.breach_name}Breach']
        
        for email_obj in all_emails:
            breach_email_entries.append(breachName(
            email_id=email_obj,
            email=email_obj,
            password='Null',
            breach_id=breach_information
        ))

        if breach_email_entries:
            # Add custom --modelname provided by the user
            breachName.objects.bulk_create(breach_email_entries, ignore_conflicts=True)
            print(f'Added {len(breach_email_entries)} emails to breach model.')

def main():
    parser = argparse.ArgumentParser(description="Admin path checker")
    parser.add_argument('-mN', '--modelname', required=True, help='Enter model name for data breach.')
    args = parser.parse_args()
    
    # # Adding emails to database
    database_operations = AddEmails(args.modelname.capitalize())
    database_operations.send_emails_to_db()

if __name__ == "__main__":
    main()
