import sys
from bs4 import BeautifulSoup
import urllib2
import re
import datetime

import traceback

import logging
import os

class Hack:
    def __init__(self, name, url, location=None, date=None, topic=None):
        self.name = name
        self.url = url
        self.location = location
        self.date = date
        self.topic = topic


    def __repr__(self):

        return """<hack>
        <name>{0}</name>
        <url>{1}</url>
        <location>{2}</location>
        <date>{3}</date></hack>""".format(self.name, self.url, self.location, self.date)


class DateDecoder:

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def __init__(self, regex, date_part_order):
        self.regex = regex
        self.order = date_part_order

    def get_year_from_url(url):
        match = re.search("(19|20)d/d", url)
        return match.group(0)

    def parse_string(self, date_string, year = None):

        try:

            match = re.search(self.regex, date_string)
            parsed_date = match.group(0)

            parsed_date = re.split("\W+", parsed_date)

            # todo - prevent repetition
            year = None
            month = None
            day = None

            for count in range(0, 3):
                date_part = self.order[count]

                if date_part == "m":
                    month = parsed_date[count]
                elif date_part == "d":
                    day = parsed_date[count]
                elif date_part == "y":
                    year = parsed_date[count]
                else:
                    raise Exception("Unrecognized date part {0}".format(date_part))

            for i, month_name in enumerate(self.months):
                if str(month).startswith(month_name):
                    month = i + 1
                    break

            return datetime.date(int(year), int(month), int(day))

        except:
            print_exception()
            return None


def get_safe_string(content):

    # TODO - refactor this to see what's actually going on
    try:
        return str(content).encode('ascii', 'ignore').strip()
    except:
        return str(content.encode('ascii', 'ignore')).strip()


def print_exception (failed_component = None):
    if not failed_component == None:
        print "{0} failed".format(failed_component)

    print "Exception in user code:"
    print '-' * 60
    traceback.print_exc(file=sys.stdout)
    print '-' * 60


def main(argv=None):

    hacks = dict() # dictionary of hacks, indexed by URL

    # TODO - handle incomplete date cases and event-based cases
    short_date_regex = "(0[1-9]|1[012]|[1-9])[- /.](0[1-9]|[12][0-9]|3[01]|[1-9])[- /.]((19|20)\d\d|\d\d)" # mm/dd/yyyy
    short_date_regex_alt = "(19|20)\d\d[- /.](0[1-9]|1[012]|[1-9])[- /.](0[1-9]|[12][0-9]|3[01]|[1-9])" # mm/dd/yyyy
    long_date_regex = "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*\s\d(\d)?.?\s\d\d(\d\d)?" # Dec(ember) 19 1990

    date_regexes = [DateDecoder(short_date_regex_alt, "ymd"),
                    DateDecoder(short_date_regex, "mdy"),
                    DateDecoder(long_date_regex, "mdy")]


    with open('hack_data.xml', 'wb') as output:
        hacks_by_year_url = "file:///C:/My%20Web%20Sites/mit%20hacks/hacks.mit.edu/Hacks/by_year/index84cf.html"
        hacks_by_location_url = "file:///C:/My%20Web%20Sites/mit%20hacks/hacks.mit.edu/Hacks/by_location/index.html"
        hacks_by_topic_url = "file:///C:/My%20Web%20Sites/mit%20hacks/hacks.mit.edu/Hacks/by_topic/index.html"

        v = urllib2.urlopen(hacks_by_year_url)
        # Parse by year
        soup = BeautifulSoup(urllib2.urlopen(hacks_by_year_url).read())

        for row in soup.select('ul > li > a'):
            hack_href = row['href']
            hack_date = None
            hack_location = None
            hack_name = None


            # TODO - this is a temp hack for Tremblant
            if not str(hack_href).startswith("http://"):
                hack_href = os.path.normpath(os.path.join("file:///C:/My%20Web%20Sites/mit%20hacks/hacks.mit.edu/Hacks/by_year/", hack_href))


            try:
                soup_child = BeautifulSoup(urllib2.urlopen(hack_href).read())

                # TODO - temporary hack for local version downloaded at Tremblant
                if not str(soup_child.contents[0]).find("<title>Page has moved</title>") == -1:
                    print str.format("FAIL page not downloaded: {0}", hack_href)
                    continue

                hack_name = get_safe_string(row.contents[0])


                box = soup_child.find('table', class_="box")

                if (box != None):
                    # Matches first site format
                    hack_info_table = soup_child.find('table', class_="box").findAll('td')
                    hack_location = get_safe_string(hack_info_table[0].contents[0])
                    hack_date = get_safe_string(hack_info_table[1].contents[0])

                else:
                    # Matches second site format
                    match = re.search("(?<=Date:\<\/strong\>).*(?=\<br\>.*\n)", str(soup_child))
                    hack_date = match.group(0).strip()
                    match = re.search('(?<=Location:\<\/strong\>).*(?=\<br\>.*\n)', str(soup_child))
                    hack_location = match.group(0).strip()


                date = None
                for i, regex in enumerate(date_regexes):
                    date = regex.parse_string(hack_date)

                    if date != None:
                        break

                print "Parsed date: {0}".format(date)

                hack = Hack(name=hack_name, url=hack_href, location=hack_location, date=hack_date)
                hacks[hack.url] = hack

                output.write(BeautifulSoup('{0}'.format(hack)).prettify())
                print hack

            except:
                # TODO log exceptions to file
                # ignore exceptions - just print out errors that occurred for analysis later
                print_exception(hack_href)


        # Second pass - get better location information
        logging.debug("second pass - get better location information")

        soup = BeautifulSoup(urllib2.urlopen(hacks_by_location_url).read())

        for row in soup.select('ul > li > a'):
            location_href = row['href']

            logging.debug("current location_href: {0}", location_href)

            # TODO - this is a temp hack for Tremblant
            if not str(location_href).startswith("http://"):
                location_href = os.path.normpath(os.path.join("file:///C:/My%20Web%20Sites/mit%20hacks/hacks.mit.edu/Hacks/by_location/", location_href))
                logging.debug("new location_href: {0}", location_href)

            try:
                location_name = get_safe_string(row.contents[0])
                logging.debug("location name: {0}", location_name)

                match = re.search("((?<=\sIn\s)|(?<=\sin\s)|(?<=\son\s)|(?<=\sat\s)).*", location_name)
                location_name = match.group(0)

                soup_child = BeautifulSoup(urllib2.urlopen(location_href).read())

                # TODO - temporary hack for local version downloaded at Tremblant
                if not str(soup_child.contents[0]).find("<title>Page has moved</title>") == -1:
                    print str.format("FAIL page not downloaded: {0}", location_href)
                    continue

                # get sub location (h2, ul) pairs
                h2_soup = soup_child.find_all('h2') # sub locations
                ul_soup = soup_child.find_all('ul') # links to hacks

                # if no sub location exits, populate h2_soup with single location
                if len(h2_soup) == 0:
                    h2_soup = [BeautifulSoup("<h2>{0}</h2>".format(location_name))]

                logging.debug("sub locations: {0}", h2_soup)

                for i, h2 in enumerate(h2_soup):
                    ul = ul_soup[i]
                    for link in ul.find_all('a'):
                        hack_href = link.get('href')
                        hack_location = h2.contents[0]

                        if not str(hack_href).startswith("http://"):
                            hack_href = os.path.normpath(os.path.join("file:///C:/My%20Web%20Sites/mit%20hacks/hacks.mit.edu/Hacks/by_location/",  hack_href))

                        hacks[hack_href].location = hack_location

                        logging.debug("new hack: {0}", hacks[hack_href])




                # iterate through links for all sub locations, query hack_dict, add location data





            except:
                print print_exception()
                # TODO
                pass


        # Third pass - get hack topics
        soup = BeautifulSoup(urllib2.urlopen(hacks_by_topic_url).read())





if __name__ == "__main__":
    sys.exit(main())