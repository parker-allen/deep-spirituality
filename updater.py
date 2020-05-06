import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

def get_scriptures(url, user_agent, len_old_urls):
    arr1 = np.array([])
    arr2 = np.array([])
    arr4 = np.array([])

    request = urllib.request.Request(url, headers={'User-Agent': user_agent})
    response = urllib.request.urlopen(request)
    html = response.read()

    soup = BeautifulSoup(html, 'html.parser')

    # finds all scriptures and references
    for tag in soup.findAll("blockquote"):
        try:
            if ":" in tag.next_element.next_sibling.text:
                # check to make sure that there exists a valid scripture reference
                ref, translation = separate_ref_translation(
                    tag.next_element.next_sibling.text.replace('– ',
                                                               '').strip())

                arr1 = np.append(arr1, tag.next.text.strip())  # scripture
                arr2 = np.append(arr2, ref.strip())  # reference
                arr4 = np.append(arr4, translation)  # translation
                continue
        except AttributeError:
            pass
        try:
            if ":" in tag.next.contents[-1].text:
                # check to make sure that there exists a valid scripture reference
                ref, translation = separate_ref_translation(
                    tag.next.contents[-1].text)

                arr1 = np.append(arr1, tag.next.contents[0])  # scripture
                arr2 = np.append(arr2, ref.strip())  # reference
                arr4 = np.append(arr4, translation)  # translation
        except AttributeError:
            pass

    date = soup.findAll('li', {'class': 'meta-date'})[0].text
    article = soup.findAll('h1')[0].text.strip()

    for i in range(len(arr1)):
        row = ["", date.strip('\''), article, url, arr2[i] + ' ' + arr4[i], arr1[i]]
        index = len_old_urls + i
        sheet.insert_row(row, index + 1)
        sheet.update_cell(index+1, 2, date)

    return len(arr1), article


def separate_ref_translation(ref):
    translation = ''
    for i in range(len(ref), -1, -1):
        if ref[i - 1].isalpha():
            translation = ref[i - 1] + translation
            ref = ref[:-1]
        elif ref[i - 1] == ' ':
            break
    return ref, translation


def get_all_urls(user_agent):
    num_pages = 17
    arr1 = []
    for i in range(num_pages):
        url = 'https://www.deepspirituality.net/devotionals/page/' + str(i + 1)

        request = urllib.request.Request(url,
                                         headers={'User-Agent': user_agent})
        response = urllib.request.urlopen(request)
        html = response.read()

        soup = BeautifulSoup(html, 'html.parser')

        for tag in soup.findAll("h2", {"class": "entry-title"}):
            arr1.append(tag.a['href'])

    return arr1


usr_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
# urls = get_all_urls(usr_agent)

main_df = pd.DataFrame(columns=['ref', 'translation', 'Scripture', 'Article', 'Link', 'reference', 'Article Date'])

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
sheet = client.open("Scriptures of the Day").sheet1
df = pd.DataFrame(sheet.get_all_records())

print('getting all urls, this may take a minute...')
urls = get_all_urls(usr_agent)
old_urls = sheet.col_values(4)[1:]
print('finished getting urls')

for url in urls:
    if url not in old_urls:
        while True:
            try:
                num, title = get_scriptures(url, usr_agent, len(old_urls)+1)
            except gspread.exceptions.APIError as e:
                print('need to sleep for 10 seconds...')
                time.sleep(10)
                continue
            break
        if num > 0:
            print( 'added', num, 'scripture(s) from', title)