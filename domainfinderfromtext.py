import streamlit as st
import re
from urllib.parse import urlparse
import requests
import random
from bs4 import BeautifulSoup
import datetime
import os

# Define a list of User-Agent strings
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
]

# Define a function to randomly select a User-Agent
def get_random_user_agent():
    return random.choice(user_agents)

# Define a function to extract and sort unique domains and main domains from text using regular expressions
def extract_and_sort_domains(text):
    # Regular expression pattern to match domains with various TLDs, subdomains, and URL schemes
    domain_pattern = r"(https?://)?([a-zA-Z0-9.-]+(\.[a-zA-Z]{2,}))|www\.[a-zA-Z0.9.-]+\.[a-zA-Z]{2,}"
    
    # Find all domain matches in the input text
    domains = re.findall(domain_pattern, text)
    
    # Extract, add "https://" if not present, and store the unique domains in a set
    unique_domains = set()
    for domain in domains:
        if domain[0]:
            unique_domains.add(domain[0] + domain[1])
        else:
            unique_domains.add('https://' + domain[1])
    
    # Convert the set of unique domains back to a sorted list
    sorted_domains = sorted(list(unique_domains))
    
    # Extract and sort the unique main domains
    main_domains = sorted(set(urlparse(domain).netloc for domain in sorted_domains))
    
    return sorted_domains, main_domains

# Define a function to fetch the title of a web page with a random User-Agent and handle getaddrinfo failed errors
def get_page_title(url):
    try:
        headers = {'User-Agent': get_random_user_agent()}  # Randomly select a User-Agent
        response = requests.get(url, headers=headers, allow_redirects=True, verify=False)  # Add verify=False to ignore SSL certificate verification
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.title
        if title_tag:
            return title_tag.string.strip(), response.url
        else:
            return "Title not available", response.url
    except requests.exceptions.RequestException as e:
        # Handle getaddrinfo failed error
        if "getaddrinfo failed" in str(e):
            return "Failed to establish a connection to the domain", url
        return "Title not available", str(e)

# Streamlit app title
st.title("Domain Extractor, Sorter, and Title Checker App")

# Input text area for user input
input_text = st.text_area("Enter text:")

# Input text box for the file path
html_file_path = st.text_input("Enter HTML file path:", value="C:/Users/style/Downloads/found_domains.html")

# Get the current date and time in the specified format
current_datetime = datetime.datetime.now().strftime("%d %B %Y %A %I:%M %p")

# Initialize the serial number
serial_number = 1

# Check if the HTML file exists, and if not, create it with a header
if not os.path.exists(html_file_path):
    with open(html_file_path, 'w', encoding='utf-8') as file:
        file.write("<html>\n<head><title>Found Domains and Titles</title></head>\n<body>\n")
        file.write(f'<p style="background-color: pink; padding: 5px;">Extraction Date: {current_datetime}</p>\n')
else:
    # If the HTML file exists, read it to find the highest serial number and existing domains
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
        # Find the highest serial number
        highest_serial = max([int(match.group(1)) for match in re.finditer(r"Serial Number: (\d+)", html_content)], default=1)
        serial_number = highest_serial + 1
        # Extract existing domains to check for duplicates later
        existing_domains = set(re.findall(r"<a href='(https?://[^']+)'.*?</a>", html_content))

# Add a button to extract and display domain information
if st.button("Extract Domains"):
    # Extract and sort unique domains and main domains from the input text
    sorted_domains, main_domains = extract_and_sort_domains(input_text)

    # Remove duplicates from sorted_domains by checking against existing_domains
    sorted_domains = [domain for domain in sorted_domains if domain not in existing_domains]

    # Display the total number of unique domains
    st.write(f"Total Valid Domains Found: {len(sorted_domains)}")

    # Display domain titles
    st.header("Domain Titles:")

    # Create or open the existing HTML file in append mode with UTF-8 encoding
    with open(html_file_path, 'a', encoding='utf-8') as file:
        for domain in sorted_domains:
            title, redirect_url = get_page_title(domain)

            # Check if the title is "Failed to establish a connection to the domain"
            if title != "Failed to establish a connection to the domain":
                # Check if the title is "Title not available"
                if title != "Title not available":
                    extracted_date = datetime.datetime.now().strftime("%d %B %Y %A %I:%M %p")
                    row_color = random.choice(["lightgray", "lightpink", "lightblue"])
                    
                    # Append the new data to the existing HTML file with the serial number
                    file.write(f"<p style='background-color: {row_color};'>Serial Number: {serial_number} <a href='{domain}' target='_blank'>{domain}</a>: {title} ({extracted_date})</p>\n")
                    
                    # Increment the serial number
                    serial_number += 1

    # Provide a download link for the updated HTML file
    st.markdown(f'<a href="file://{html_file_path}" download="found_domains.html">Click to download HTML file</a>', unsafe_allow_html=True)

# Display the download button after the code completes its extraction
if not input_text:
    st.write("Please enter some text to extract domains and titles.")
