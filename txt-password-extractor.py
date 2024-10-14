import re
import csv

# Define a regex that matches password-like sequences
password_pattern = r'(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^a-zA-Z0-9])([A-Za-z0-9!@#$%^&*()_+={}\[\]:;"\'<>,.?/~`-]{8,})'
valid_email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'

data = {}

with open('pokemoncreed.net.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        # Find the email in the line
        pattern_match = re.search(valid_email_pattern, line)
        if pattern_match:
            email = str(pattern_match.group())

            # Check if a password exists in the line
            password_match = re.search(password_pattern, line)
            if password_match:
                password = str(password_match.group(1))

                # Ensure we only append unique emails and passwords
                if email not in data:
                    data[email] = {"passwords": [], "line": None}

                # Avoid appending the same password multiple times
                if password not in data[email]['passwords']:
                    data[email]['passwords'].append(password)

                # Store the line for future reference
                data[email]["line"] = str(line)

with open('test-hashes.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['email', 'passwords', 'line'])

    for email, info in data.items():
        password_value = '-'.join(info['passwords'])
        duplicate_pattern_match = re.search(email, password_value)
        if duplicate_pattern_match:
            # print(duplicate_pattern_match.group(), ':', new_password)
            new_password = re.sub(duplicate_pattern_match.group(), '', password_value)
            writer.writerow([email, new_password, info['line']])
        else:
            # print(email, ':', '-'.join(info['passwords']))
            writer.writerow([email, password_value, info['line']])
