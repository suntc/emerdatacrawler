'''
 * @Author: michael.tianchensun 
 * @Date: 2017-12-18 14:45:54 
'''

import sys, os
import requests
from datetime import datetime
import unicodedata
from bs4 import BeautifulSoup

## example http://cdfdata.fire.ca.gov/incidents/incidents_archived?archive_year=2016&pc=5&cp=15
url_paras = {
    'year': 2016,
    'pc' : 50,
    'cp' : 0,
}

store_path = 'C:\\Users\\suntc\\tchsun@ucdavis.edu\\cloudWorks\\emervis\\crawleroutput\calfire'

def form_url(url_paras):
    base_url = 'http://cdfdata.fire.ca.gov/incidents/incidents_archived?archive_year=%d&pc=%d&cp=%d'
    url = base_url % (url_paras['year'], url_paras['pc'], url_paras['cp'])
    return url

def simple_reports(year_range, page_range):
    ## python calfire.py 2014 2016 0
    res_reports = {}
    for year in range(year_range[0], year_range[1] + 1): ## through year
        res_reports.setdefault(year, [])
        for page in range(page_range[0], page_range[1] + 1): ## through page
            try:
                ## get html content
                url_paras['year'] = year
                url_paras['page'] = page
                url = form_url(url_paras)
                result = requests.get(url)
                if result.status_code != 200:
                    print('print bad request for year %d, page %d, continue...' % (year, page))
                ## form soup object
                soup = BeautifulSoup(result.content, 'lxml')
                ## get table of insterest
                report_tables = soup.find_all('table', {'class' : 'incident_table'})
                for r in report_tables: ## store into dict
                    '''
                    name, href
                    county
                    location
                    administrative unit, href
                    status notes
                    date stated
                    last update
                    phone numbers
                    '''
                    report = {}
                    trs = r.find_all('tr')
                    if len(trs) < 2: ## may be the first <table>
                        continue
                    for tr in trs:
                        tds = tr.find_all('td') ## should be only 2
                        if (len(tds) < 2): ## may be the first line of the table
                            continue
                        tagname = tds[0].text.strip(':').lower()
                        value = tds[1]
                        ## deal with some cases
                        if tagname == 'date started' or tagname == 'last update':
                            ## to datetime
                            timev = unicodedata.normalize("NFKD", value.text).strip(' ')
                            timev =  datetime.strptime(timev, '%B %d, %Y %I:%M %p')
                            value = str(timev)
                            pass
                        else: ## whether value contains link
                            value_a = value.find_all('a')
                            if len(value_a) > 0:
                                tagname_link = tagname + '_link'
                                value = value_a[0].text
                                link = value_a[0]['href']
                                value = unicodedata.normalize("NFKD", value).strip(' ')
                            else:
                                value = value.text
                                value = unicodedata.normalize("NFKD", value).strip(' ')
                        ## check whether value valid
                        tagname = unicodedata.normalize("NFKD", tagname).strip(' ')
                        report.setdefault(tagname, value)
                        if len(value_a) > 0:
                            report.setdefault(tagname_link, link)
                    print(report)
                    sys.stdin.read(1)
                ##  dict -- > json format
                ## write to file
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print('skip this page, continue...')
                sys.stdin.read(1)
                #continue

def main():
    year_range = [2016, 2016]
    page_range = [0, 100]
    if len(sys.argv) >= 3:
        year_range = [int(sys.argv[1]), int(sys.argv[2])] 
    if year_range[1] < year_range[0]:
        year_range = [year_range[1], year_range[0]]
    if len(sys.argv) >= 4:
        page_range[0] = int(sys.argv[3])
    if len(sys.argv) >= 5:
        page_range[1] = int(sys.argv[4])
    simple_reports(year_range, page_range)

if __name__ == '__main__':
    main()