import pandas as pd
import random


# Function to generate random usernames
def generate_username(full_name):
    username = full_name.lower().replace(" ", "") + str(random.randint(100, 999))
    return username


# Function to generate random passwords
def generate_password():
    password_length = random.randint(5, 7)
    password = ''.join(
        random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(password_length))
    return password


# Generate fictional customer data
customer_data = {
    'Full Name': ['John Doe', 'Jane Smith', 'Mike Johnson', 'Emily Davis', 'Chris Brown'],
    'Username': [generate_username('John Doe'), generate_username('Jane Smith'), generate_username('Mike Johnson'),
                 generate_username('Emily Davis'), generate_username('Chris Brown')],
    'Password': [generate_password() for _ in range(5)],
    'Age': [28, 35, 42, 30, 25],
    'Location': ['Lisbon', 'Porto', 'Coimbra', 'Faro', 'Braga'],
}

# Create a DataFrame
customer_df = pd.DataFrame(customer_data)

# Save DataFrame to CSV
customer_df.to_csv('customer_data.csv', index=False)