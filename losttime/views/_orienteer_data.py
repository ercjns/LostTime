# _orienteer_data.py
#
# Provides a set of Python classes which roughly align with parts of the
# International Orienteering Federation (IOF) XML spec at
# http://orienteering.org/datastandard/IOF.xsd
#
# Eric Jones
# www.ercjns.com
# 2016

from bs4 import BeautifulSoup as BS

class Event(object):
    def __init__(self, name, date, venue):
        self.name = name
        self.date = date
        self.venue = venue
        return

    def __str__(self):
        return '{0} at {1}'.format(self.name, self.venue)


class EventClass(object):
    def __init__(self, event, name, shortname, CR):
        self.name = name
        self.shortname = shortname
        self.scoremethod = None
        self.event = event
        self.soupCR = CR

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.shortname)


class EventPersonResult(object):
    def __init__(self, name, bib, si, clubshort, coursestatus, resultstatus, time):
        self.name = name
        self.bib = bib
        self.sicard = si
        self.clubshortname = clubshort
        self.coursestatus = coursestatus #OK, MSP, DNF (Did the competitor complete the course?)
        self.resultstatus = resultstatus #OK, NC, DSQ (Should the competitor show up in results?)
        self.time = time
        self.score = None
        self.position = None

        self.event = None
        self.eventclass = None
        self.eventcourse = None

def _resultStatusToCode(status):
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

class OrienteerXmlReader(object):
    def __init__(self, file):
        self.file = file
        with open(self.file, 'r') as infile:
            # TODO: Why does BS break when the xml encoding says windows-1252 rather than utf-8?
            infile.readline().replace('windows-1252', 'utf-8')
            self.soup = BS(infile, 'xml')
            if not self.soup.ResultList:
                self.validiofxml = False
                #TODO: this should pass back a specific error - File is not a <ResultList>.
                return
        self.iofv = int(self.soup.ResultList['iofVersion'][0])
        # self.iofv = 3
        # TODO: need more validation here before declaring it valid and proceeding...
        self.validiofxml = True
        return

    # TODO: all methods which read the soup should cache/memoize the value with the object the first time it is read.
    def _getEventName(self):
        if self.iofv == 3:
            try: name = self.soup.ResultList.Event.Name.string
            except: name = None
        return name

    def _getEventDate(self):
        if self.iofv == 3:
            # TODO: parse this into a DateTime.Date
            try: date = self.soup.ResultList.Event.StartTime.string
            except: date = None
        return date

    def _getEventVenue(self):
        # Venue is a child of RACE rather than EVENT. There are one or more RACEs which make an EVENT.
        # each competitior should start each RACE once. RACE is often omitted.
        return None

    def _getEventClassName(self, CR):
        try: name = CR.Class.Name.string
        except: name = None
        return name

    def _getEventClassShortName(self, CR):
        try: shortname = CR.Class.ShortName.string
        except: shortname = None
        return shortname

    def _getEventClasses(self):
        eventClasses = []
        if self.iofv == 3:
            classes = self.soup.find_all("ClassResult")
            for eclass in classes:
                eventclass = EventClass(self._getEventName(), self._getEventClassName(eclass), self._getEventClassShortName(eclass), eclass)
                eventClasses.append(eventclass)
        return eventClasses

    def _getPersonResultName(self, S):
        if S.name == 'PersonResult' or S.name == 'PersonEntry':
            if self.iofv == 2:
                try:
                    gn = S.Person.PersonName.Given.string
                except:
                    gn = None
                try:
                    fn = S.Person.PersonName.Family.string
                except:
                    fn = None
            elif self.iofv == 3:
                try:
                    gn = S.Person.Name.Given.string
                except:
                    gn = None
                try:
                    fn = S.Person.Name.Family.string
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

    def _getPersonResultBib(self, S):
        if S.name == 'PersonResult':
            if self.iofv == 2:
                bib = None
            elif self.iofv == 3:
                try:
                    bib = S.Result.BibNumber.string
                except:
                    bib = None
            else:
                raise ValueError
        else: raise ValueError
        return bib

    def _getPersonResultSicard(self, S):
        if S.name == 'PersonEntry':
            if self.iofv == 3:
                try:
                    sicard = S.ControlCard.string
                except:
                    sicard = None
            else:
                raise ValueError
        elif S.name == 'PersonResult':
            if self.iofv == 2:
                sicard = None
            elif self.iofv == 3:
                try:
                    sicard = S.Result.ControlCard.string
                except:
                    sicard = None
            else:
                raise ValueError
        else: raise ValueError
        return sicard

    def _getPersonResultClubShort(self, S):
        if S.name == 'PersonResult' or S.name == 'PersonEntry':
            if self.iofv == 2:
                try:
                    club = S.Person.CountryId.string
                except:
                    club = None
            elif self.iofv == 3:
                try:
                    club = S.Organisation.ShortName.string
                except:
                    club = None
        else: raise ValueError
        return club

    def _getPersonResultCourseStatus(self, S):
        if S.name == 'PersonResult':
            if self.iofv == 3:
                try:
                    status = S.Result.Status.string
                    if status in ['NotCompeting', 'Disqualified', 'OverTime']:
                        status = 'Unknown'
                except:
                    raise NameError
            else:
                raise ValueError
        else: raise ValueError
        return _resultStatusToCode(status)

    def _getPersonResultResultStatus(self, S):
        if S.name == 'PersonResult':
            if self.iofv == 3:
                try:
                    status = S.Result.Status.string
                    if status in ['MissingPunch', 'DidNotFinish']:
                        status = 'OK'
                except:
                    raise NameError
            else:
                raise ValueError
        else: raise ValueError
        return _resultStatusToCode(status)

    def _getPersonResultTime(self, S):
        if S.name == 'PersonResult':
            if self.iofv == 3:
                try:
                    time = int(S.Result.Time.string)
                except:
                    time = None
            else:
                raise ValueError
        else: raise ValueError
        return time

    def getEventMeta(self):
        # Return the Name, Date, Venue, and Class information as read from the XML file.
        eventMeta = {}
        eventMeta['name'] = self._getEventName()
        eventMeta['date'] = self._getEventDate()
        eventMeta['venue'] = self._getEventVenue()
        eventMeta['classes'] = self._getEventClasses()
        return eventMeta

    def getClassPersonResults(self, CR):
        # Return a list of python PersonResults for the given EventClass SOUP.
        # Should this be a method on the event class?

        results = []
        personresults = CR.find_all("PersonResult")
        for pr in personresults:
            name = self._getPersonResultName(pr)
            bib = self._getPersonResultBib(pr)
            si = self._getPersonResultSicard(pr)
            clubshort = self._getPersonResultClubShort(pr)
            coursestatus = self._getPersonResultCourseStatus(pr)
            resultstatus = self._getPersonResultResultStatus(pr)
            time = self._getPersonResultTime(pr)
            newpr = EventPersonResult(name, bib, si, clubshort, coursestatus, resultstatus, time)
            results.append(newpr)
        return results
