import re
import csv
import sys
import os
import django
from django.core.exceptions import ObjectDoesNotExist

# Setup Django
sys.path.append('/home/leetjesus/Desktop/breachpalacev1')
os.environ['DJANGO_SETTINGS_MODULE'] = 'breachpalace.settings'
django.setup()

from backend_api.models import *
from databreaches.models import *

objects = []
breachName = globals()[f'PokemoncreedBreach']

og_emails = []

# Open and read the CSV file - only emails for now
with open('test-hashes.csv', 'r') as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        og_emails.append(row['email'])

# Fetching latest email ID
try:
    latest_id = emailList.objects.latest('email_id').email_id
except emailList.DoesNotExist:
    latest_id = 0

# Check if emails already exist
existing_emails = set(emailList.objects.filter(email__in=og_emails).values_list('email', flat=True))

new_emails = []

# Adding new emails
for email in og_emails:
    if email not in existing_emails:
        latest_id += 1
        new_emails.append(emailList(email=email, email_id=latest_id))

# Bulk create new emails
if new_emails:
   emailList.objects.bulk_create(new_emails, ignore_conflicts=True)
   print(f'ADDED {len(new_emails)} to emailList table')

# Fetch all emails, both new and existing
all_emails_new_and_existing = emailList.objects.filter(email__in=og_emails)

# Match emails and create breach entries
with open('test-hashes.csv', 'r') as file:
    reader = csv.DictReader(file)
    for item1 in reader:
        for item2 in all_emails_new_and_existing:
            if item1['email'] == item2.email:
                try:
                    breach_id_instance = breachInfo.objects.get(name='Pokemoncreed')
                    email_instance = emailList.objects.get(email_id=item2.email_id)
                    # Create the breach entry using the emailList instance
                    objects.append(breachName(
                        email_id=email_instance,  # Must be the emailList instance, not just the ID
                        email=email_instance.email,
                        hashes=item1['passwords'],  # Ensure CSV has a column named 'passwords'
                        line=item1['line'],          # Ensure CSV has a column named 'line'
                        breach_id=breach_id_instance
                    ))
                except emailList.DoesNotExist:
                     pass

try:
    breachName.objects.bulk_create(objects, ignore_conflicts=True)
except django.db.utils.IntegrityError as e:
    print(e)
