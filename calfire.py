'''
 * @Author: michael.tianchensun 
 * @Date: 2017-12-18 14:45:54 
'''

import sys, os
import math
import requests
from datetime import datetime
import unicodedata
import logging
import json
from bs4 import BeautifulSoup

## example http://cdfdata.fire.ca.gov/incidents/incidents_archived?archive_year=2016&pc=5&cp=15
url_paras = {
    'year': 2016,
    'pc' : 50,
    'page' : 0,
}

config_file = 'calfire.config.json'
## store_path = 'C:\\Users\\suntc\\tchsun@ucdavis.edu\\cloudWorks\\emervis\\crawleroutput\calfire'

stats = {
    'success' : [],
    'fail': []
}
stats_str = "(year %d, page %d, count %d) %s"
stats_file = 'calfire.stats.json'

root = logging.getLogger()
root.setLevel(logging.INFO)

def form_url(url_paras):
    base_url = 'http://cdfdata.fire.ca.gov/incidents/incidents_archived?archive_year=%d&pc=%d&cp=%d'
    url = base_url % (url_paras['year'], url_paras['pc'], url_paras['page'])
    return url

def get_web_res(year, page):
    url_paras['year'] = year
    url_paras['page'] = page
    url = form_url(url_paras)
    result = requests.get(url)
    if result.status_code != 200:
        print('print bad request for year %d, page %d, continue...' % (year, page))
        raise Exception('bad request') 
    return result

def simple_reports_process(year, page, res_reports):
    ## get html content
    result = get_web_res(year, page)
    ## form soup object
    soup = BeautifulSoup(result.content, 'lxml')
    ## get table of insterest
    report_tables = soup.find_all('table', {'class' : 'incident_table'})
    for count, r in enumerate(report_tables): ## store into dict
        try:
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
            firename = ''
            trs = r.find_all('tr')
            if len(trs) < 2: ## may be the first <table>
                continue
            for tr in trs:
                tds = tr.find_all('td') ## should be only 2
                if (len(tds) < 2): ## may be the first line of the table
                    continue
                tagname = unicodedata.normalize("NFKD", tds[0].text).strip(' ')
                tagname = tagname.strip(':').lower()
                tagname = tagname.strip(' ')
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
                if tagname == 'name':
                    firename = value
                ## check whether value valid
                report.setdefault(tagname, value)
                if len(value_a) > 0:
                    report.setdefault(tagname_link, link)
            res_reports[year].append(report)
            ## update stats
            stats['success'].append(stats_str % (year, page, count, firename))
            #print("success ", stats_str % (year, page, count, firename))
    
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(e)
            print('skip this page, continue...')
            stats['fail'].append(stats_str % (year, page, count, firename))
            logging.warn("fail ", stats_str % (year, page, count, firename))
            sys.stdin.read(1)
            continue
    return res_reports

def simple_reports(year_range, page_range):
    ## python calfire.py 2014 2016 0
    res_reports = {}
    for year in range(year_range[0], year_range[1] + 1): ## through year
        res_reports.setdefault(year, [])
        logging.info('year ' + str(year))
        ## get maximum page number
        result = get_web_res(year, 0)
        soup = BeautifulSoup(result.content, 'lxml')
        ## use a for loop to find last number
        cur_node = soup.find_all('img', {'alt': 'Previous Page'})[0]
        max_pagenum = 0
        while True:
            cur_node = cur_node.next_sibling
            if cur_node is None:
                break
            if cur_node.name is None:
                continue
            if len(cur_node.text) > 0:
                max_pagenum = cur_node.text
        logging.info('max_pagenum is ' + str(max_pagenum))
        for page in range(page_range[0], min(page_range[1], int(max_pagenum)) + 1): ## through page
            logging.info('page ' + str(page))
            res_reports = simple_reports_process(year, page, res_reports)

        ## write to file
        ## load output folder
        with open(config_file) as confile:
            config_dict = json.load(confile)
            store_path = config_dict['store_path']
            print('store path', config_dict['store_path'])
            ## create file
            filename = str(year) + ' ' + str(datetime.now()) + '.json'
            with open(os.path.join(store_path, filename), 'w') as outfile:
                json.dump(res_reports[year], outfile)
                outfile.close()
            confile.close()

    with open(stats_file, 'w') as statsf:
        json.dump(stats, statsf)
        statsf.close()

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