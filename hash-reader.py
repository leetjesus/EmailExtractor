import re
import csv
def identify_hash_type(hash_string):
    """Identifies the type of a hash based on its length."""
    hash_length = len(hash_string)
    md5_hash_pattern = r'\b([a-f0-9]{32})\b'
    
    if hash_length == 32 or hash_length == 35:
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

# Change this
N = 1000
total_md5_hashes_found = 0
validate_email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
data = {}

with open('FILENAME HERE', 'r', encoding='utf-8') as file:
    for i in range(N):
        line = next(file).strip()
        y = line.split(",")
        pattern_match = re.search(validate_email_pattern, line)
        for hash_string in y:
            hash_type = identify_hash_type(hash_string)
            if pattern_match and hash_type == 'MD5':
                email = str(pattern_match.group())
                
                if email not in data:
                    data[email] = {"hashes": [], "line":None} 
                data[email]["hashes"].append(hash_string.replace("'", ''))
                data[email]["line"] = str(line)
                print('Email found: ' + str(pattern_match.group()))
                print('MD5 hash: ', str(pattern_match.group()), hash_string)
                print('-------------------------------------------------------------------') 
                total_md5_hashes_found += 1

print(f"Total MD5 hashes with associated emails found: {total_md5_hashes_found}")
    
for email, hashes in data.items():
    string = ''.join(hashes['hashes'])
    print(string[1:].replace(" ", '-'))

with open('test-hashes.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['email', 'hashes', 'line'])

    for email, hashes in data.items():
        hash_value = ''.join(hashes['hashes'])
        # NOTE: This string[1] index value is bound to change because of every file being different....
        writer.writerow([email, hash_value[1:].replace(" ", '-'), hashes['line']])
