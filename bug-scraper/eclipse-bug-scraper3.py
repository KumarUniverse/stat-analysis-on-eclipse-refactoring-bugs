#!/usr/bin/python

from bs4 import BeautifulSoup
from lxml import html
from typing import Match
import requests
import re


def parse_str(s: str) -> str:
    return " ".join(s.replace("\n"," ").split())

def is_date(date_str: str) -> Match:
    return re.search(r"(\d{4})[-](\d{2})[-](\d{2})", date_str)

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
page = requests.get(bug_list_url) #,headers)
soup = BeautifulSoup(page.content, "html.parser")

csv_file = open("eclipse-jdt-refactoring-bugs-extended.csv", "w+")
csv_file.write("ID,Product,Comp,Assignee,Status,Resolution,Summary,Hardware,")
csv_file.write("Importance,CC_List,Date_Reported,Date_Modified,History\n")

table = soup.find("table")
bug_rows = table.findAll("tr")
bug_count = len(bug_rows)

print("Bug scraping started")
# Ignore the column headers row and get all the other rows.
for i in range(1,bug_count):
    if (i % 100 == 0):
        print(f"{i} out of {bug_count-1} bugs added")
    bug_row = bug_rows[i]
    additional_bug_info = []
    for bug_info in bug_row.findAll("td"):
        if (bug_info.has_attr("class") and
            bug_info["class"][0] == "first-child"):
            atag = bug_info.find("a")
            bug_url = "https://bugs.eclipse.org/bugs/" + atag["href"]
            page = requests.get(bug_url)

            # Check if the bug description or title contains
            # the word "refactor". If it doesn't, skip the bug.
            soup2 = BeautifulSoup(page.content, "html.parser")
            ctrl_f = soup2.find(string=re.compile("refactor"))
            if not ctrl_f:
                break

            tree = html.fromstring(page.content)
            hardware_used = parse_str(
                tree.xpath('//td[@class="field_value"]/text()')[0])
            bug_importance = parse_str(
                tree.xpath('//td[@id="bz_show_bug_column_1"]' \
                    '/table//tr[11]/td/text()')[0])
            cc_list = parse_str(
                tree.xpath('//td[@id="bz_show_bug_column_2"]' \
                    '/table//tr[3]/td/text()')[0])
            date_reported = parse_str(
                tree.xpath('//td[@id="bz_show_bug_column_2"]' \
                    '/table//tr[1]/td/text()')[0])[:-3]
            date_modified = parse_str(
                tree.xpath('//td[@id="bz_show_bug_column_2"]' \
                    '/table//tr[2]/td/text()')[0])[:-2]
            additional_bug_info.append(hardware_used)
            additional_bug_info.append(bug_importance)
            additional_bug_info.append(cc_list)
            additional_bug_info.append(date_reported)
            additional_bug_info.append(date_modified)

            # Get the bug's history URL and read its history.
            bug_history_url = "https://bugs.eclipse.org/bugs/" + parse_str(
                tree.xpath('//td[@id="bz_show_bug_column_2"]' \
                    '/table//tr[2]/td/a/@href')[0])
            page = requests.get(bug_history_url)
            soup2 = BeautifulSoup(page.content, "html.parser")
            history_table_elems = soup2.findAll("td")

            # Store the history as str array ({}) separated by semicolons (;).
            status_dates = "{"

            # Store the first date, if available:
            if len(history_table_elems) > 1:
                first_date = history_table_elems[1].text.strip()
                if is_date(first_date):
                    status_dates += "First_date:" + first_date + ";"

            # Add the statuses, resolution, and their dates.
            prev_date = "0000-00-00"
            for i in range(3,len(history_table_elems)):
                table_elem = history_table_elems[i].text.strip()
                if is_date(table_elem):
                    prev_date = table_elem
                if table_elem == "Status":
                    new_status = history_table_elems[i+2].text.strip()
                    status_dates += "Status:" + new_status + ";"
                    status_dates += "Status_date:" + prev_date + ";"
                if table_elem == "Resolution":
                    resolution = history_table_elems[i+2].text.strip()
                    status_dates += "Resolution:" + resolution + ";"
                    status_dates += "Resolution_date:" + prev_date + ";"

            status_dates += "}"
            additional_bug_info.append(status_dates)

            csv_file.write(bug_info.text.strip() + ",")
        elif (bug_info.has_attr("class") and
            bug_info["class"][0] == "bz_changeddate_column" and
            additional_bug_info):
            for i in range(len(additional_bug_info)-1):
                csv_file.write(str(additional_bug_info[i]).strip() + ",")
            csv_file.write(str(additional_bug_info[-1]).strip() + "\n")
            additional_bug_info.clear()
        else:
            csv_file.write(bug_info.text.replace(",","").strip() + ",")
print("All bugs have been scraped")

csv_file.close()
