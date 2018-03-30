# losttime/views/_output_templates.py

import datetime
import pytz
import csv, fileinput, sys
import dominate
import abc
from dominate.tags import *
from flask import flash


class EventHtmlWriter(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, event, format='generic', classes=None, results=None, teamclasses=None, teamresults=None, clubcodes=None):
        self.event = event
        self.format = format
        self.eventclasses = classes
        self.personresults = results
        self.teamclasses = teamclasses
        self.teamresults = teamresults
        self.clubcodes = clubcodes

    @abc.abstractmethod
    def eventResultIndv(self):
        """

        :return:
        """
        pass
    #     """
    #     create an html file with individual, or individual+team results for this event.
    #     """
    #     if self.format == 'generic':
    #         return self.__writeEventResultIndv()
    #     elif self.format == 'coc':
    #         return self.__writeEventResultIndv_coc()
    #     else:
    #         raise KeyError("Unrecognized output format {0}".format(self.format))

    @abc.abstractmethod
    def eventResultTeam(self):
        """
        create an html file with team results for this event
        """
        pass
        # if len(self.teamclasses) == 0:
        #     return False
        # if self.format == 'generic':
        #     return self.__writeEventResultTeam()
        # elif self.format == 'coc':
        #     return False #team results included on indv result page
        # else:
        #     raise KeyError("Unrecognized output format {0}".format(self.format))



class SeriesHtmlWriter(object):
    def __init__(self, series, format='generic', seriesclasses=None, results=None, clubcodes=None):
        self.series = series
        self.format = format
        self.seriesclasses = seriesclasses
        self.results = results
        self.clubcodes = clubcodes

    def seriesResult(self):
        """
        create an html file with series results for this event.
        """
        if self.format == 'generic':
            return self.__writeSeriesResult()
        elif self.format == 'coc':
            return self.__writeSeriesResult_coc()
        else:
            raise KeyError("Unrecognized output format {0}".format(self.format))

    def __writeSeriesResult(self):
        # TODO: generic series output
        return self.__writeSeriesResult_coc()

    def __writeSeriesResult_coc(self):
        doc = div(cls="LostTimeContent")
        with doc:
            style(".season1{ color: Red;} .season2{ color: Crimson;} .season3{ color: FireBrick;} .season-pts{ text-decoration: underline;}")
            with div(cls="lg-mrg-bottom"):
                h2("Season Standings")
                self.seriesclasses.sort(key=lambda x: x.shortname)
                for sc in self.seriesclasses:
                    h4(a(sc.name, href='#{0}'.format(sc.shortname)))
            for sc in self.seriesclasses:
                with div(cls="classResults lg-mrg-bottom", id=sc.shortname):
                    h3(sc.name)
                    t = table(cls="table table-striped")
                    with t.add(tr(id='column-titles')):
                        th('Place')
                        th('Name') if sc.classtype == 'indv' else th('Team')
                        if sc.classtype == 'indv':
                            th('School') if sc.shortname.startswith('W') else th('Club')
                        for i in range(1, len(self.series.eventids.split(','))+1):
                            th('#{0}'.format(i))
                        th('Season')
                    for r in self.results[sc.shortname]:
                        bestscores = r['scores'][:self.series.scoreeventscount]
                        scores = []
                        for eid in [int(x) for x in self.series.eventids.split(',')]:
                            try:
                                scores.append((int(r['results'][eid].score), int(r['results'][eid].position)))
                            except:
                                scores.append(('--', False))
                        with t.add(tr()):
                            td(r['position'])
                            if sc.classtype == 'indv':
                                # td("{0} ({1})".format(r['name'], r['club']))
                                td(r['name'])
                                td(r['club']) if r['club'] != None else td()
                            elif sc.classtype == 'team':
                                td("{0} ({1})".format(self.clubcodes[r['name']][0].name, r['name']))

                            for s in scores:
                                # td(s)
                                score_decorators = ''
                                d = td(s[0])
                                if s[0] in bestscores:
                                    score_decorators = 'season-pts'
                                    bestscores.remove(s[0])
                                if s[1] == 1:
                                    score_decorators += " season1"
                                elif s[1] == 2:
                                    score_decorators += " season2"
                                elif s[1] == 3:
                                    score_decorators += " season3"
                                if score_decorators != '':
                                    with d:
                                        attr(cls = score_decorators)

                            td(int(r['score']))
        return doc


class EntryWriter(object):
    def __init__(self, infiles, format, eventtype='standard', punchtype='epunch', bibstart=1001):
        self.files = infiles
        self.format = format
        if self.format == 'CheckInNationalMeet':
            self.national_meet = True
        else:
            self.national_meet = False
        self.eventtype = eventtype
        self.epunch = True if punchtype == 'epunch' else False
        self.bibnum = _nextbib(bibstart)

    def writeEntries(self):
        if self.format == 'OE':
            return self.__writeOEentries()
        elif self.format == 'CheckIn' or self.format == 'CheckInNationalMeet':
            return self.__writeCheckInEntries()
        else:
            raise KeyError("Unrecognized output format for entries: {}".format(self.format))

    def __writeOEentries(self):
        template = ';{0};;{1};;{2};{3};{4};{5};;{6};;;;0;;;;;;{7};;;;;{8};;;;;;;;;;;;;;;;;;;;;;;{9};0;X;;;;;;\n'
        doc = ''
        prefix = 'OESco0001;' if self.eventtype == 'score' else 'OE0001;'
        header = prefix + 'Stno;XStno;Chipno;Database Id;Surname;First name;YB;S;Block;nc;Start;Finish;Time;Classifier;Credit -;Penalty +;Comment;Club no.;Cl.name;City;Nat;Location;Region;Cl. no.;Short;Long;Entry cl. No;Entry class (short);Entry class (long);Rank;Ranking points;Num1;Num2;Num3;Text1;Text2;Text3;Addr. surname;Addr. first name;Street;Line2;Zip;Addr. city;Phone;Mobile;Fax;EMail;Rented;Start fee;Paid;Team;Course no.;Course;km;m;Course controls\n'
        doc += header
        bibs = []
        bibs_dupes_exist = False
        for f in self.files:

            for line in fileinput.input(files=(f), inplace=True):
                # for line in rawfile:
                line = line.replace('\0', '')
                sys.stdout.write(line)

            with open(f, 'r') as currentfile:
                regreader = csv.reader(currentfile, delimiter=',')
                datacols = self.__identify_columns(next(regreader))

                known_renting = True if 'rented' in datacols.keys() else False
                known_bib = True if 'stno' in datacols.keys() else False
                known_nc = True if 'nc' in datacols.keys() else False

                for line in regreader:
                    first = line[datacols['first']].strip('\"\'\/\\ ') if 'first' in datacols.keys() else ''
                    last = line[datacols['last']].strip('\"\'\/\\ ') if 'last' in datacols.keys() else ''
                    yb = line[datacols['yb']].strip('\"\'\/\\ ') if 'yb' in datacols.keys() else ''
                    club = line[datacols['club']].strip('\"\'\/\\ ') if 'club' in datacols.keys() else ''
                    cat = line[datacols['cat']].strip('\"\'\/\\ ') if 'cat' in datacols.keys() else ''
                    sex = line[datacols['sex']].strip('\"\'\/\\ ') if 'sex' in datacols.keys() else ''
                    punch = line[datacols['punch']].strip('\"\'\/\\ ') if 'punch' in datacols.keys() else ''
                    if (first == '') and (last == '') and (club == '') and (cat == ''):
                        continue
                    if known_renting:
                        rented = line[datacols['rented']].strip('\"\'\/\\ ')
                    else:
                        rented = 'X' if len(punch) == 0 else ''
                    if known_bib:
                        stno = line[datacols['stno']].strip('\"\'\/\\ ')
                        if len(stno) == 0:
                            stno = next(self.bibnum)
                    else:
                        stno = next(self.bibnum)
                    if known_nc:
                        nc = line[datacols['nc']].strip('\"\'\/\\ ')
                    else:
                        nc = '0'
                    if stno in bibs:
                        bibs_dupes_exist = True
                    bibs.append(stno)
                    regline = template.format(stno, punch, last, first, yb, sex, nc, club, cat, rented)
                    doc += regline
        if bibs_dupes_exist:
            flash("Detected entries with non-unique start/bib numbers.", 'danger')
        return doc

    def __writeCheckInEntries(self):
        if self.epunch:
            rentalDocA = '<h2>Pre-Registered List: RENTAL e-punches (List A)</h2>\n'
            rentalDocB = '<h2>Pre-Registered List: RENTAL e-punches (List B)</h2>\n'
            rentalDoc = '<h4>REGISTRATION VOLUNTEERS</h4><p>Check off ALL participants in the first column as they arrive. Collect money from those who owe it and mark it out.</br>Write in e-punch numbers (clearly!) and bring this page to finish ASAP while using the other copy of this list.</p>\n'
            rentalDoc += '<h4>FINISH VOLUNTEERS</h4><p>For any handwritten e-punch numbers without check marks, find the name in the e-punch software, enter the number, and add a check to this form. Return this list registration.</p>\n<hr />\n'

            ownersDoc = '<h2>Pre-Registered List: OWNED e-punches</h2>\n'
            ownersDoc += '<h4>REGISTRATION VOLUNTEERS</h4><p>Check off ALL participants in the first column as they arrive. Collect money from those who owe it and mark it out when paid.</p>\n<hr />\n'

            if self.national_meet:
                tablehead = '<table>\n<thead><tr><th class="check">&#x2714;</th><th>First</th><th>Last</th><th>Owes</th><th>Course</th><th>E-Punch</th><th>Club</th><th>YB</th><th>Gen.</th><th>Phone</th><th>Emergency Phone</th><th>Car</th></tr></thead>\n'
            else:
                tablehead = '<table>\n<thead><tr><th class="check">&#x2714;</th><th>First</th><th>Last</th><th>Owes</th><th>Course</th><th>E-Punch</th><th>Club</th><th>Phone</th><th>Emergency Phone</th><th>Car</th></tr></thead>\n'

            rentalDoc += tablehead
            ownersDoc += tablehead

            if self.national_meet:
                OWN_TEMPLATE = '<tr><td class="check">{}</td><td>{}</td><td>{}</td><td class="owes">{}</td><td class="verify">{}</td><td class="punch">{}</td><td class="verify">{}</td><td class="YB verify"></td><td class="gender verify"></td><td class="phone">{}</td><td class="phone">{}</td><td class="license">{}</td></tr>\n'
                RENT_TEMPLATE = '<tr><td class="check">{}</td><td>{}</td><td>{}</td><td class="owes">{}</td><td class="verify">{}</td><td class="rentpunch"></td><td class="verify">{}</td><td class="YB verify"></td><td class="gender verify"></td><td class="phone">{}</td><td class="phone">{}</td><td class="license">{}</td></tr>\n'
            else:
                OWN_TEMPLATE = '<tr><td class="check">{}</td><td>{}</td><td>{}</td><td class="owes">{}</td><td>{}</td><td class="punch">{}</td><td>{}</td><td class="phone">{}</td><td class="phone">{}</td><td class="license">{}</td></tr>\n'
                RENT_TEMPLATE = '<tr><td class="check">{}</td><td>{}</td><td>{}</td><td class="owes">{}</td><td>{}</td><td class="rentpunch"></td><td>{}</td><td class="phone">{}</td><td class="phone">{}</td><td class="license">{}</td></tr>\n'

        else:
            manualDoc = '<h2>Pre-Registered List: MANUAL PUNCH event</h2>\n'
            manualDoc += '<h4>REGISTRATION VOLUNTEERS</h4><p>Check off ALL participants in the first column as they arrive. Collect money from those who owe it and mark it out when paid.</p>\n<hr />\n'
            manualDoc += '<table>\n<thead><tr><th class="check">&#x2714;</th><th>First</th><th>Last</th><th>Owes</th><th>Course</th><th>Club</th><th>Phone</th><th>Emergency Phone</th><th>Car</th></tr></thead>\n'
        
            MANUAL_TEMPLATE = '<tr><td class="check">{}</td><td>{}</td><td>{}</td><td class="owes">{}</td><td>{}</td><td>{}</td><td class="phone">{}</td><td class="phone">{}</td><td class="license">{}</td></tr>\n'

        for f in self.files:

            for line in fileinput.input(files=(f), inplace=True):
                line = line.replace('\0', '')
                sys.stdout.write(line)

            with open(f, 'r') as currentfile:
                regreader = csv.reader(currentfile, delimiter=',')
                datacols = self.__identify_columns(next(regreader))
                
                for line in regreader:
                    first = line[datacols['first']].strip('\"\'\/\\ ').replace('_', ' ') if 'first' in datacols.keys() else ''
                    last = line[datacols['last']].strip('\"\'\/\\ ').replace('_', ' ') if 'last' in datacols.keys() else ''
                    club = line[datacols['club']].strip('\"\'\/\\ ') if 'club' in datacols.keys() else ''
                    cat = line[datacols['cat']].strip('\"\'\/\\ ') if 'cat' in datacols.keys() else ''
                    sex = line[datacols['sex']].strip('\"\'\/\\ ') if 'sex' in datacols.keys() else ''
                    punch = line[datacols['punch']].strip('\"\'\/\\ ') if ('punch' in datacols.keys() and self.epunch) else ''
                    paid = line[datacols['paid']].strip('\"\'\/\\ ') if 'paid' in datacols.keys() else '?'
                    owed = line[datacols['owed']].strip('\"\'\/\\ ') if 'owed' in datacols.keys() else ''
                    phone = line[datacols['phone1']].strip('\"\'\/\\ ').replace('\\', ' ').replace('/', ' ').replace('-', '.') if 'phone1' in datacols.keys() else ''
                    phone2 = line[datacols['phone2']].strip('\"\'\/\\ ').replace('\\', ' ').replace('/', ' ').replace('-', '.') if 'phone2' in datacols.keys() else ''
                    license = line[datacols['license']].strip('\"\'\/\\ ') if 'license' in datacols.keys() else ''

                    rental = True if len(punch) == 0 else False
                    paid = True if len(owed) == 0 else False
                    

                    if (first == '') and (last == '') and (club == '') and (cat == ''):
                        continue
                    if not paid:
                        owed = '${}'.format(owed)
                        box = owed
                    else:
                        box = ''

                    if rental and self.epunch:
                        newline = RENT_TEMPLATE.format(box, first, last, owed, cat, club, phone, phone2, license)
                        rentalDoc += newline
                    elif self.epunch:
                        newline = OWN_TEMPLATE.format(box, first, last, owed, cat, punch, club, phone, phone2, license)
                        ownersDoc += newline
                    else:
                        newline = MANUAL_TEMPLATE.format(box, first, last, owed, cat, club, phone, phone2, license)
                        manualDoc += newline
        
        if self.epunch:
            rentalDocA += rentalDoc + '</table>\n'
            rentalDocB += rentalDoc + '</table>\n'
            ownersDoc += '</table>\n'
        else:
            manualDoc += '</table>\n'

        pacificTZ = pytz.timezone('US/Pacific')
        utc = pytz.timezone('UTC')
        now = utc.localize(datetime.datetime.utcnow())
        localtime = now.astimezone(pacificTZ)
        timestamp = '<p id="createdate">{}</p>'.format(localtime.strftime('%H:%M %A %d %b %Y %Z%z'))

        header = '<!DOCTYPE html><html>\n<head>\n' + timestamp + '</head>\n'
        pagebreak = '\n<p style="page-break-before: always" ></p>\n'

        if self.epunch:
            doc = header + ownersDoc + pagebreak + rentalDocA + pagebreak + rentalDocB + '</body></html>\n'
        else:
            doc = header + manualDoc + '</body></html>\n'
        return doc


    def __identify_columns(self, headerline):
        """return dict of indexes for output columns"""
        datacols = {}
        for idx, val in enumerate(headerline):
            val = val.lower()
            if 'bib' in val:
                datacols['stno'] = idx
                continue
            elif 'first' in val:
                datacols['first'] = idx
                continue
            elif 'last' in val:
                datacols['last'] = idx
                continue
            elif 'club' in val or 'school' in val:
                datacols['club'] = idx
                continue
            elif 'class' in val or 'course' in val:
                datacols['cat'] = idx
                continue
            elif 'sex' in val or ('gen' in val and 'emergency' not in val):
                datacols['sex'] = idx
                continue
            elif 'punch' in val or 'card' in val:
                datacols['punch'] = idx
                continue
            elif 'rent' in val:
                datacols['rented'] = idx
                continue
            elif 'nc' in val and 'emergency' not in val:
                datacols['nc'] = idx
                continue
            elif 'paid' in val:
                datacols['paid'] = idx
                continue
            elif 'owed' in val:
                datacols['owed'] = idx
                continue
            elif 'phone' in val and 'emergency' not in val:
                datacols['phone1'] = idx
                continue
            elif 'emergencyphone' in val:
                datacols['phone2'] = idx
                continue
            elif 'license' in val:
                datacols['license'] = idx
                continue
            elif 'yb' in val:
                datacols['yb'] = idx
                continue
            else:
                continue
        return datacols


def _sortByPosition(results):
    """
    Sort by position, with position -1 at the end.
    """
    invalid = []
    valid = []
    for result in results:
        if (result.position == -1) or (result.position is None):
            invalid.append(result)
        else:
            valid.append(result)
    valid.sort(key=lambda x: x.position)
    return valid + invalid


def _sortByName(results):
    results = sorted(results, key=lambda x: x.name)
    return results


def _nextbib(initial=1001):
    i = initial
    while True:
        yield i
        i += 1
