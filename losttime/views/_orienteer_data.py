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
from bs4 import BeautifulSoup as BS


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
        with open(self.file, 'r') as xmlfile:
            xmlfile.readline().replace('windows-1252', 'utf-8')
            self.xmlsoup = BS(xmlfile, 'xml')
            if not self.xmlsoup.ResultList:
                return False
        self.xmlv = int(self.xmlsoup.ResultList['iofVersion'][0])
        if self.xmlv not in [2, 3]:
            return False
        return True

    def _validateCSV(self):
        with open(self.file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            self.csvcols = self._getCSVcols(next(reader))
            if set(['name', 'class', 'time']) <= set(self.csvcols.keys()):
                if not self.ScoreO:
                    return True
                elif 'points' in self.csvcols.keys():
                    return True
        return False

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

    def getEventClassPersonResults(self, Oec):
        #return list of EPR objects
        if self.filetype == 'xml':
            return self._getEventClassPersonResultsXML(Oec)
        elif self.filetype == 'csv':
            return self._getEventClassPersonResultsCSV(Oec)
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
            classes = self.xmlsoup.find_all("ClassResult")
            for eclass in classes:
                eventclass = EventClass(
                    self.__XMLgetEventName(), 
                    self.__XMLgetEventClassName(eclass), 
                    self.__XMLgetEventClassShortName(eclass), 
                    )
                eventClasses.append(eventclass)
        return eventClasses
    def _getEventClassPersonResultsXML(self, Oecr):
        results = []
        #GIVEN an EVENT, I need to re-qurey the self.xmlsoup, there is no soup passed in as before. this is a change!
        personresults = self.xmlsoup.find(string=Oecr.name).find_parent("Class").find_next_siblings("PersonResult")
        for prsoup in personresults:
            pr = EventPersonResult(
                self.__XMLgetPersonResultName(prsoup),
                self.__XMLgetPersonResultBib(prsoup),
                self.__XMLgetPersonResultSicard(prsoup),
                self.__XMLgetPersonResultClubShort(prsoup),
                self.__XMLgetPersonResultCourseStatus(prsoup),
                self.__XMLgetPersonResultResultStatus(prsoup),
                self.__XMLgetPersonResultTime(prsoup),
            )
            results.append(pr)
        return results


##########
# XML Parse Functions
##########
    def __XMLgetEventName(self):
        if self.xmlv == 3:
            try: name = self.xmlsoup.ResultList.Event.Name.string
            except: name = None
        return name
    def __XMLgetEventDate(self):
        if self.xmlv == 3:
            try: date = self.xmlsoup.ResultList.Event.StartTime.string
            except: date = None
        return date
    def __XMLgetEventVenue(self):
        return None
    def __XMLgetEventClassName(self, ecrsoup):
        try: name = ecrsoup.Class.Name.string
        except: name = None
        return name
    def __XMLgetEventClassShortName(self, ecrsoup):
        try: shortname = ecrsoup.Class.ShortName.string
        except: shortname = None
        return shortname

    def __XMLgetPersonResultName(self, prsoup):
        if prsoup.name == 'PersonResult' or prsoup.name == 'PersonEntry':
            if self.xmlv == 2:
                try:
                    gn = prsoup.Person.PersonName.Given.string
                except:
                    gn = None
                try:
                    fn = prsoup.Person.PersonName.Family.string
                except:
                    fn = None
            elif self.xmlv == 3:
                try:
                    gn = prsoup.Person.Name.Given.string
                except:
                    gn = None
                try:
                    fn = prsoup.Person.Name.Family.string
                except:
                    fn = None
            else:
                raise ValueError
        else: raise ValueError
        if (gn != None) and (fn != None):
            name = gn + ' ' + fn
        elif (gn != None):
            name = gn
        elif (fn != None):
            name = fn
        else:
            name = None
        return name

    def __XMLgetPersonResultBib(self, prsoup):
        if prsoup.name == 'PersonResult':
            if self.xmlv == 2:
                bib = None
            elif self.xmlv == 3:
                try:
                    bib = prsoup.Result.BibNumber.string
                except:
                    bib = None
            else:
                raise ValueError
        else: raise ValueError
        return bib

    def __XMLgetPersonResultSicard(self, prsoup):
        if prsoup.name == 'PersonEntry':
            if self.xmlv == 3:
                try:
                    sicard = prsoup.ControlCard.string
                except:
                    sicard = None
            else:
                raise ValueError
        elif prsoup.name == 'PersonResult':
            if self.xmlv == 2:
                sicard = None
            elif self.xmlv == 3:
                try:
                    sicard = prsoup.Result.ControlCard.string
                except:
                    sicard = None
            else:
                raise ValueError
        else: raise ValueError
        return sicard

    def __XMLgetPersonResultClubShort(self, prsoup):
        if prsoup.name == 'PersonResult' or prsoup.name == 'PersonEntry':
            if self.xmlv == 2:
                try:
                    club = prsoup.Person.CountryId.string
                except:
                    club = None
            elif self.xmlv == 3:
                try:
                    club = prsoup.Organisation.ShortName.string
                except:
                    club = None
        else: raise ValueError
        return club

    def __XMLgetPersonResultCourseStatus(self, prsoup):
        if prsoup.name == 'PersonResult':
            if self.xmlv == 3:
                try:
                    status = prsoup.Result.Status.string
                    if status in ['NotCompeting', 'Disqualified', 'OverTime']:
                        status = 'Unknown'
                except:
                    raise NameError
            else:
                raise ValueError
        else: raise ValueError
        return self._resultStatusToCode(status)

    def __XMLgetPersonResultResultStatus(self, prsoup):
        if prsoup.name == 'PersonResult':
            if self.xmlv == 3:
                try:
                    status = prsoup.Result.Status.string
                    if status in ['MissingPunch', 'DidNotFinish']:
                        status = 'OK'
                except:
                    raise NameError
            else:
                raise ValueError
        else: raise ValueError
        return self._resultStatusToCode(status)

    def __XMLgetPersonResultTime(self, prsoup):
        if prsoup.name == 'PersonResult':
            if self.xmlv == 3:
                try:
                    time = int(prsoup.Result.Time.string)
                except:
                    time = None
            else:
                raise ValueError
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
        name = unicode(line[self.csvcols['name']].strip('\"\'\/\\ '), 'utf-8')
        return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
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
