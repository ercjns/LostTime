# _orienteer_data.py
#
# Provides a set of Python classes which roughly align with parts of the
# International Orienteering Federation (IOF) XML spec at
# http://orienteering.org/datastandard/IOF.xsd
#
# Provides a Reader Object which can read properly structured XML and CSV
# files and build the python classes with the input data.
#
# Eric Jones
# www.ercjns.com
# 2016

import csv, unicodedata
from math import floor
from defusedxml.ElementTree import parse
from datetime import datetime

class Event(object):
    def __init__(self, name, date, venue):
        self.name = name
        self.date = date
        self.venue = venue
        return

    def __str__(self):
        return 'Event {0} at {1}'.format(self.name, self.venue)


class EventClass(object):
    def __init__(self, event, name, shortname):
        self.event = event
        self.name = name
        self.shortname = shortname
        self.scoremethod = None

    def __str__(self):
        return 'EventClass {0} ({1})'.format(self.name, self.shortname)


class EventPersonResult(object):
    def __init__(self, name, bib, si, clubshort, coursestatus, resultstatus, time, score_points=None, score_penalty=None):
        self.name = name
        self.bib = bib
        self.sicard = si
        self.clubshortname = clubshort
        self.coursestatus = coursestatus #OK, MSP, DNF (Did the competitor complete the course?)
        self.resultstatus = resultstatus #OK, NC, DSQ (Should the competitor show up in results?)
        self.time = time
        self.score = None
        self.position = None

        self.ScoreO_points = score_points
        self.ScoreO_penalty = score_penalty

        self.event = None
        self.eventclass = None
        self.eventcourse = None

    def __str__(self):
        return 'EventPersonResult {0} ({1})'.format(self.name, self.clubshortname)

class OrienteerResultReader(object):
    def __init__(self, file, ScoreO=False):
        self.file = file
        self.ScoreO = ScoreO
        self.filetype = file.rsplit('.', 1)[1].lower()
        if self.filetype == 'xml':
            self.isValid = self._validateXML()
        elif self.filetype == 'csv':
            self.isValid = self._validateCSV()
        else:
            self.isValid = False
        return

    def _validateXML(self):
        self.xmlns = {'iof3': 'http://www.orienteering.org/datastandard/3.0', 
              'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        with open(self.file, 'r', encoding="utf-8") as xmlfile:
            xmlfile.readline().replace('windows-1252', 'utf-8')
            self.xmltree = parse(xmlfile)
            self.xmlroot = self.xmltree.getroot()
            EXPECTED_ROOT = '{' + self.xmlns['iof3'] + '}'+ 'ResultList'
            if self.xmlroot.tag != EXPECTED_ROOT:
                return False

        self.xmlv = floor(float(self.xmlroot.attrib['iofVersion']))
        if self.xmlv not in [3]:
            return False
        return True

    def _validateCSV(self):
        with open(self.file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            firstline = next(reader)
            if firstline[0] == 'OESco0012':
                self.csvcols = self.__getOEScoCSVcols(firstline)
            else:
                self.csvcols = self._getCSVcols(firstline)
            if (set(['name', 'class', 'time']) <= set(self.csvcols.keys()) or
                set(['first', 'last', 'class', 'time']) <= set(self.csvcols.keys())):
                if not self.ScoreO:
                    return True
                elif 'points' in self.csvcols.keys() and 'penalty' in self.csvcols.keys():
                    return True
        return False

    def __getOEScoCSVcols(self, headerline):
        '''
        Important columns from an OEScore csv, based on how COC has OE configured
        '''
        datacols = {}
        for idx, val in enumerate(headerline):
            val = val.lower()
            if val == 'first name':
                datacols['first'] = idx
                continue
            elif val == 'surname':
                datacols['last'] = idx
                continue
            elif val == 'short':
                datacols['class'] = idx
                continue
            elif val == 'long':
                datacols['classlong'] = idx
                continue
            elif val == 'time':
                datacols['time'] = idx
                continue
            elif val == 'city':
                datacols['club'] = idx
                continue
            elif val == 'points':
                datacols['points'] = idx
                continue
            elif val == 'score penalty':
                datacols['penalty'] = idx
                continue
            else:
                continue
        return datacols

    def _getCSVcols(self, headerline):
        datacols = {}
        for idx, val in enumerate(headerline):
            val = val.lower()
            if 'name' in val:
                datacols['name'] = idx
                continue
            elif 'class' in val and 'classlong' not in val:
                datacols['class'] = idx
                continue
            elif 'time' in val:
                datacols['time'] = idx
                continue
            elif 'club' in val:
                datacols['club'] = idx
                continue
            elif 'classlong' in val:
                datacols['classlong'] = idx
                continue
            elif 'points' in val:
                datacols['points'] = idx
            elif 'penalty' in val:
                datacols['penalty'] = idx
            else:
                continue
        return datacols

    def _resultStatusToCode(self, status):
        if status.lower() == 'ok':
            return 'ok'
        if status.lower() == 'missingpunch':
            return 'msp'
        elif status.lower() == 'didnotfinish':
            return 'dnf'
        elif status.lower() == 'notcompeting':
            return 'nc'
        elif status.lower() == 'disqualified':
            return 'dq'
        elif status.lower() == 'didnotstart':
            return 'dns'
        elif status.lower() == 'overtime':
            return 'ovt'
        else:
            return 'unknown'

    def getEventMeta(self):
        #return Event object
        if self.filetype == 'xml':
            return self._getEventXML()
        elif self.filetype == 'csv':
            return self._getEventCSV()
        return None

    def getEventClasses(self):
        #return list of EventClass objects
        if self.filetype == 'xml':
            return self._getEventClassesXML()
        elif self.filetype == 'csv':
            return self._getEventClassesCSV()
        return None

    def getEventClassPersonResults(self, eventClass):
        #return list of EPR objects
        if self.filetype == 'xml':
            return self._getEventClassPersonResultsXML(eventClass)
        elif self.filetype == 'csv':
            return self._getEventClassPersonResultsCSV(eventClass)
        return None


##########
# XML Helper Functions
##########
    def _getEventXML(self):
        return Event(
            self.__XMLgetEventName(),
            self.__XMLgetEventDate(),
            self.__XMLgetEventVenue()
        )
    def _getEventClassesXML(self):
        eventClasses = []
        if self.xmlv == 3:
            classes = self.xmltree.findall('iof3:ClassResult', self.xmlns)
            for eclass in classes:
                eventclass = EventClass(
                    self.__XMLgetEventName(), 
                    self.__XMLgetEventClassName(eclass), 
                    self.__XMLgetEventClassShortName(eclass), 
                    )
                eventClasses.append(eventclass)
        return eventClasses
    def _getEventClassPersonResultsXML(self, eventClass):
        results = []
        xpath = "iof3:ClassResult/"
        xpath += "iof3:Class[iof3:Name='{}']/".format(eventClass.name)
        xpath += "../iof3:PersonResult"
        personresults = self.xmltree.findall(xpath, self.xmlns)
        for prElement in personresults:
            pr = EventPersonResult(
                self.__XMLgetPersonResultName(prElement),
                self.__XMLgetPersonResultBib(prElement),
                self.__XMLgetPersonResultSicard(prElement),
                self.__XMLgetPersonResultClubShort(prElement),
                self.__XMLgetPersonResultCourseStatus(prElement),
                self.__XMLgetPersonResultResultStatus(prElement),
                self.__XMLgetPersonResultTime(prElement),
            )
            results.append(pr)
        return results


##########
# XML Parse Functions
##########
    def __XMLgetEventName(self):
        if self.xmlv == 3:
            try: 
                els = self.xmltree.findall('iof3:Event/iof3:Name', self.xmlns)
                if len(els) == 1:
                    name = els[0].text
                else:
                    name = None
            except: name = None
        return name
    def __XMLgetEventDate(self):
        if self.xmlv == 3:
            try: 
                els = self.xmltree.findall('iof3:Event/iof3:StartTime', self.xmlns)
                if len(els) == 1:
                    date = els[0].text
                else:
                    els = self.xmltree.findall('iof3:ClassResult/iof3:PersonResult/iof3:Result/iof3:StartTime', self.xmlns)
                    date = els[0].text #just grab the first one.
            except: date = None
        if date != None:
            date = datetime.strptime(date.split('T')[0], '%Y-%m-%d')
        return date
    def __XMLgetEventVenue(self):
        return None
    def __XMLgetEventClassName(self, ecrtree):
        try: name = ecrtree.find('iof3:Class/iof3:Name', self.xmlns).text
        except: name = None
        return name
    def __XMLgetEventClassShortName(self, ecrtree):
        try: shortname = ecrtree.find('iof3:Class/iof3:ShortName', self.xmlns).text
        except: shortname = None
        return shortname

    def __XMLgetPersonResultName(self, prtree):
        if self.xmlv == 3:
            try: 
                gn = prtree.find('iof3:Person/iof3:Name/iof3:Given', self.xmlns).text
            except:
                gn = None
            try:
                fn = prtree.find('iof3:Person/iof3:Name/iof3:Family', self.xmlns).text
            except:
                fn = None
        else:
            raise ValueError
        if (gn != None) and (fn != None):
            name = gn + ' ' + fn
        elif (gn != None):
            name = gn
        elif (fn != None):
            name = fn
        else:
            name = None
        return name

    def __XMLgetPersonResultBib(self, prtree):
        if self.xmlv == 3:
            try:
                bib = prtree.find('iof3:Result/iof3:BibNumber', self.xmlns).text
            except:
                bib = None
        else: raise ValueError
        return bib

    def __XMLgetPersonResultSicard(self, prtree):
        # if prsoup.name == 'PersonEntry':
        #     if self.xmlv == 3:
        #         try:
        #             sicard = prsoup.ControlCard.string
        #         except:
        #             sicard = None
        #     else:
        #         raise ValueError
        if self.xmlv == 3:
            try:
                sicard = prtree.find('iof3:Result/iof3:ControlCard', self.xmlns).text
            except:
                sicard = None
        else: raise ValueError
        return sicard

    def __XMLgetPersonResultClubShort(self, prtree):
        if self.xmlv == 3:
            try:
                club = prtree.find('iof3:Organisation/iof3:ShortName', self.xmlns).text
            except:
                club = None
        else: raise ValueError
        return club

    def __XMLgetPersonResultCourseStatus(self, prtree):
        if self.xmlv == 3:
            try:
                status = prtree.find('iof3:Result/iof3:Status', self.xmlns).text
                if status in ['NotCompeting', 'Disqualified', 'OverTime']:
                    status = 'Unknown'
            except:
                raise NameError
        else: raise ValueError
        return self._resultStatusToCode(status)

    def __XMLgetPersonResultResultStatus(self, prtree):

        if self.xmlv == 3:
            try:
                status = prtree.find('iof3:Result/iof3:Status', self.xmlns).text
                if status in ['MissingPunch', 'DidNotFinish']:
                    status = 'OK'
            except:
                raise NameError
        else: raise ValueError
        return self._resultStatusToCode(status)

    def __XMLgetPersonResultTime(self, prtree):
        if self.xmlv == 3:
            try:
                time = int(prtree.find('iof3:Result/iof3:Time', self.xmlns).text)
            except:
                time = None
        else: raise ValueError
        return time

##########
# CSV Helper Functions
##########
    def _getEventCSV(self):
        return Event(
            None,
            None,
            None,
        )
    def _getEventClassesCSV(self):
        eventClasses = []
        known_codes = []
        with open(self.file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader) # skip header line
            for line in reader:
                class_short = self.__CSVgetEventClassShortName(line)
                class_full = self.__CSVgetEventClassName(line)
                if class_short in known_codes:
                    continue
                eventclass = EventClass(
                    None,
                    class_full,
                    class_short,
                    )
                eventClasses.append(eventclass)
                known_codes.append(class_short)
        return eventClasses
    def _getEventClassPersonResultsCSV(self, Oecr):
        results = []
        # May need to do something to get back to first line?
        # Is there a better way than looping the entire file every time?
        with open(self.file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader) # skip header line
            for line in reader:
                if self.__CSVgetEventClassShortName(line) != Oecr.shortname:
                    continue
                name = self.__CSVgetPersonResultName(line)
                club = self.__CSVgetPersonResultClubShort(line)
                time, coursestatus, resultstatus = self.__CSVgetPersonResultTime(line)
                if self.ScoreO:
                    score_points = self.__CSVgetPersonResultScorePoints(line)
                    score_penalty = self.__CSVgetPersonResultScorePenalty(line)
                else:
                    score_points = None
                    score_penalty = None
                pr = EventPersonResult(
                    name,
                    None, # Bib
                    None, # SiCard
                    club,
                    coursestatus,
                    resultstatus,
                    time,
                    score_points,
                    score_penalty
                )
                results.append(pr)
        return results


##########
# CSV Parsing Functions
##########

    def __CSVgetEventClassShortName(self, line):
        return line[self.csvcols['class']].strip('\"\'\/\\ ')
    def __CSVgetEventClassName(self, line):
        try:
            return line[self.csvcols['classlong']].strip('\"\'\/\\ ')
        except:
            return self.__CSVgetEventClassShortName(line)
    def __CSVgetPersonResultName(self, line):
        if 'name' in self.csvcols.keys():
            name = line[self.csvcols['name']].strip('\"\'\/\\ ')
            return name
            # return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
        elif 'first' in self.csvcols.keys() and 'last' in self.csvcols.keys():
            first = line[self.csvcols['first']].strip('\"\'\/\\ ')
            last = line[self.csvcols['last']].strip('\"\'\/\\ ')
            return first + ' ' + last
            # return unicodedata.normalize('NFKD', first + ' ' + last).encode('ascii', 'ignore')
        else:
            return ''
        return

    def __CSVgetPersonResultClubShort(self, line):
        try:
            return line[self.csvcols['club']].strip('\"\'\/\\ ')
        except:
            return None
    def __CSVgetPersonResultTime(self, line):
        timestr = line[self.csvcols['time']].strip('\"\'\/\\ ').lower()
        timestr = timestr.split(':')
        if len(timestr) == 3:
            # HH:MM:SS
            hours = int(timestr[0])
            mins = int(timestr[1])
            secs = int(timestr[2])
            if hours >= 8 and secs == 0:
                #likely excel being dumb "45:24:00"
                secs = mins
                mins = hours
                hours = 0
            time = hours*3600 + mins*60 + secs
            return time, 'ok', 'ok'
        elif len(timestr) == 2:
            # MMM:SS
            mins = int(timestr[0])
            secs = int(timestr[1])
            time = mins*60 + secs
            return time, 'ok', 'ok'
        else:
            timestr = str(timestr[0])
            if timestr in ['dnf', 'mp', 'msp']:
                return None, timestr, 'ok'
            elif timestr in ['dns', 'dsq', 'nc']:
                return None, None, timestr
            else:
                raise ValueError("Unknown time value {0}".format(timestr))
    def __CSVgetPersonResultScorePoints(self, line):
        points = line[self.csvcols['points']].strip('\"\'\/\\ ')
        try:
            return int(points)
        except:
            raise ValueError("unknown Score O point value {0}".format(points))
    def __CSVgetPersonResultScorePenalty(self, line):
        try:
            return abs(int(line[self.csvcols['penalty']].strip('\"\'\/\\ ')))
        except:
            return 0
