#!/usr/bin/python
# This program collects the bug IDs of all the refactoring bugs
# whose product is JDT and component is UI from Eclipse's Bugzilla website.
# It then sorts the bug IDs and outputs them to a txt file.

from bs4 import BeautifulSoup
import requests
import re


def parse_str(s: str) -> str:
    return " ".join(s.replace("\n"," ").split())

# headers are used to make scraper look like a browser to the website
# headers = {
#     'Access-Control-Allow-Origin': '*',
#     'Access-Control-Allow-Methods': 'GET',
#     'Access-Control-Allow-Headers': 'Content-Type',
#     'Access-Control-Max-Age': '3600',
#     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) ' \
#         'Gecko/20100101 Firefox/52.0'
# }

bug_list_url = "https://bugs.eclipse.org/bugs/buglist.cgi?"\
    "component=UI&limit=0&order=bug_status%2Cpriority%2Cbug_severity"\
    "&product=JDT&query_format=advanced"

refactoring_bug_id_list = set()

page = requests.get(bug_list_url) #,headers)
soup = BeautifulSoup(page.content, "html.parser")

table = soup.find("table")
bug_rows = table.findAll("tr")
bug_count = len(bug_rows)

print("Bug ID scraping started")
# Ignore the column headers row and get all the other rows.
for i in range(1,bug_count):
    if (i % 100 == 0):
        print(f"{i} out of {bug_count-1} bugs added")
    bug_row = bug_rows[i]

    bug_id = bug_row.find("td")
    atag = bug_id.find("a")
    bug_url = "https://bugs.eclipse.org/bugs/" + atag["href"]
    page = requests.get(bug_url)

    # Check if the bug description or title contains
    # the word "refactor", ignoring case. If it doesn't, skip the bug.
    soup2 = BeautifulSoup(page.content, "html.parser")
    ctrl_f = soup2.find(string=re.compile("refactor", re.IGNORECASE))
    if ctrl_f:
        #print(parse_str(bug_id.text))
        refactoring_bug_id_list.add(parse_str(bug_id.text))

refactoring_bug_data_file = open("refactoring_bug_data.csv","r")
for line in refactoring_bug_data_file.readlines()[1:10]:
    bug_id = line.split(",")[1]
    refactoring_bug_id_list.add(int(bug_id))

refactoring_bug_id_list = list(refactoring_bug_id_list)
refactoring_bug_id_list.sort()

bug_id_file = open("refactoring_bug_id_list.txt", "w+")
for bug_id in refactoring_bug_id_list:
    #print(bug_id)
    bug_id_file.write(bug_id + "\n")

print("All bug IDs have been added to the refactoring_bug_id_list.txt file.")
refactoring_bug_data_file.close()
bug_id_file.close()
