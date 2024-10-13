import pandas as pd
import time, subprocess, django, argparse, re, os, subprocess, sys
import pathlib, csv, glob

sys.path.append('/home/leetjesus/Desktop/breachpalacev1')
os.environ['DJANGO_SETTINGS_MODULE'] = 'breachpalace.settings'

# Setup Django
django.setup()

from backend_api.models import *
from databreaches.models import *

objects = []
# Change this to the model your adding data too
breachName = globals()[f'EmailhashtestBreach']

og_emails = []

with open('test-hashes.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        og_emails.append(row['email'])


# Grabbing the latest email id for generating new emails
try:
    latest_id = emailList.objects.latest('email_id').id
except emailList.DoesNotExist:
    latest_id = 0


# Check to see if the og_emails exist within the table emailList
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

with open('test-hashes.csv', 'r') as file:
    reader = csv.DictReader(file)
    for item1 in reader:
        for item2 in all_emails_new_and_exisisting:
            if re.search(item1['email'], item2.email):
                print(f"Match found: '{item1['email']}' in '{item2.email}'")
                email_id = emailList.objects.get(pk=item2.email_id)
                objects.append(breachName(
                    email_id=email_id,
                    email=item1['email'],
                    hashes=row['hashes'],
                    line=row['line'],
                ))

# Pass up any duplicat emails found
try:
    breachName.objects.bulk_create(objects)
except django.db.utils.IntegrityError as e:
    print(e)
