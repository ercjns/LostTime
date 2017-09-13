# losttime/views/_output_templates.py

import datetime
import pytz
import csv, fileinput, sys
import dominate
from dominate.tags import *

class EventHtmlWriter(object):
    def __init__(self, event, format='generic', classes=None, results=None, teamclasses=None, teamresults=None, clubcodes=None):
        self.event = event
        self.format = format
        self.eventclasses = classes
        self.personresults = results
        self.teamclasses = teamclasses
        self.teamresults = teamresults
        self.clubcodes = clubcodes

    def eventResultIndv(self):
        """
        create an html file with individual, or individual+team results for this event.
        """
        if self.format == 'generic':
            return self.__writeEventResultIndv()
        elif self.format == 'coc':
            return self.__writeEventResultIndv_coc()
        else:
            raise KeyError("Unrecognized output format {0}".format(self.format))

    def eventResultTeam(self):
        """
        create an html file with team results for this event
        """
        if len(self.teamclasses) == 0:
            return False
        if self.format == 'generic':
            return self.__writeEventResultTeam()
        elif self.format == 'coc':
            return False #team results included on indv result page
        else:
            raise KeyError("Unrecognized output format {0}".format(self.format))


    def __writeEventResultIndv(self):
        doc = dominate.document(title='Event Results')
        with doc.head:
            link(rel='stylesheet',
                 href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css',
                 integrity='sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7',
                 crossorigin='anonymous')
            link(rel='stylesheet',
                 href='https://maxcdn.bootstrapcdn.com/font-awesome/4.6.1/css/font-awesome.min.css')
            meta(name='viewport', content='width=device-width, initial-scale=1.0')
        with doc:
            page = div(cls='container-fluid')
        with page:
            with div(cls='row').add(div(cls='col-xs-12')):
                h1('Results for {0}'.format(self.event.name))
                try:
                    eventdate = datetime.date(*[int(x) for x in event.date.split('-')])
                    p('An orienteering event held at {0} on {1:%d %B %Y}'.format(self.event.venue, eventdate))
                except:
                    pass
                p('Competition Classes:')
            with div(cls='row'):
                for ec in self.eventclasses:
                    self.eventclasses.sort(key=lambda x: x.shortname)
                    div((a(ec.name, href='#{0}'.format(ec.shortname))), cls='col-md-3')
            for ec in self.eventclasses:
                with div(cls='row').add(div(cls='col-md-8')):
                    classresults = [r for r in self.personresults if r.classid == ec.id]
                    h3(ec.name, id=ec.shortname)
                    t = table(cls='table table-striped table-condensed', id='ResultsTable-{0}'.format(ec.shortname))
                    with t.add(tr(id='column-titles')):
                        if ec.scoremethod in ['time', 'worldcup', '1000pts', 'score', 'score1000']:
                            classresults = _sortByPosition(classresults)
                            th('Pos.')
                        th('Name')
                        if ec.scoremethod in ['alpha']:
                            classresults = _sortByName(classresults)
                        th('Club')
                        if ec.scoremethod in ['score', 'score1000']:
                            th('Points')
                            th('Penalty')
                            th('Total')
                        th('Time')
                        if ec.scoremethod in ['1000pts', 'worldcup', 'score1000']:
                            th('Score')
                    for pr in classresults:
                        with t.add(tr()):
                            if ec.scoremethod in ['time', 'worldcup', '1000pts', 'score', 'score1000']:
                                td(pr.position) if pr.position > 0 else td()
                            td(pr.name)
                            td(pr.club_shortname) if pr.club_shortname else td()
                            if ec.scoremethod in ['score', 'score1000']:
                                td(pr.ScoreO_points)
                                td(pr.ScoreO_penalty)
                                td(pr.ScoreO_net)
                            if pr.coursestatus in ['ok']:
                                td(pr.timetommmss())
                            elif pr.resultstatus in ['ok']:
                                td('{1} {0}'.format(pr.timetommmss(), pr.coursestatus))
                            else:
                                td('{1} {2} {0}'.format(pr.timetommmss(), pr.coursestatus, pr.resultstatus))
                            if (ec.scoremethod in ['worldcup', '1000pts', 'score1000']):
                                td('{0:d}'.format(int(pr.score))) if pr.score is not None else td()
        return doc # __writeEventResultIndv

    def __writeEventResultIndv_coc(self):
        doc = div(cls="LostTimeContent", id="lt-top")
        with doc:

            self.eventclasses.sort(key=lambda x: x.shortname)
            WIOL = [x for x in self.eventclasses if x.shortname.startswith('W')]
            if len(WIOL) > 0:
                # Split Out Public and WIOL individual classes in menu
                with div(cls="lg-mrg-bottom"):
                    h2("Winter Series (Public)")
                    for ec in self.eventclasses:
                        if ec not in WIOL:
                            h4(a(ec.name, href='#{0}'.format(ec.shortname)))
                with div(cls="lg-mrg-bottom"):
                    h2("WIOL School League - Individuals")
                    for ec in WIOL:
                        h4(a(ec.name, href='#{0}'.format(ec.shortname)))
            else:
                with div(cls="lg-mrg-bottom"):
                    h2("Event Classes")
                    for ec in self.eventclasses:
                        h4(a(ec.name, href='#{0}'.format(ec.shortname)))

            if len(self.teamclasses) > 0:
                with div(cls="lg-mrg-bottom"):
                    h2("WIOL School League - Teams")
                    for tc in self.teamclasses:
                        self.teamclasses.sort(key=lambda x: x.shortname)
                        h4(a(tc.name, href='#{0}'.format(tc.shortname)))

            for ec in self.eventclasses:
                with div(cls="classResults lg-mrg-bottom"):
                    classresults = [r for r in self.personresults if r.classid == ec.id]
                    h3(ec.name, id=ec.shortname)
                    t = table(cls="table table-striped", id='ResultsTable-{0}'.format(ec.shortname)).add(tbody())
                    with t.add(tr(id="column-titles")):
                        if ec.scoremethod in ['time', 'worldcup', '1000pts', 'score', 'score1000']:
                            classresults = _sortByPosition(classresults)
                            th('Pos.')
                        th('Name')
                        th('Club')
                        if ec.scoremethod in ['score', 'score1000']:
                            th('Points')
                            th('Penalty')
                            th('Total')
                        th('Time')
                        if ec.scoremethod in ['1000pts', 'worldcup', 'score1000']:
                            th('Score')
                    for pr in classresults:
                        with t.add(tr()):
                            if ec.scoremethod in ['time', 'worldcup', '1000pts', 'score', 'score1000']:
                                td(pr.position) if pr.position > 0 else td()
                            td(pr.name)
                            td(pr.club_shortname) if pr.club_shortname else td()
                            if ec.scoremethod in ['score', 'score1000']:
                                td(pr.ScoreO_points)
                                td(pr.ScoreO_penalty)
                                td(pr.ScoreO_net)
                            if pr.coursestatus in ['ok']:
                                td(pr.timetommmss())
                            elif pr.resultstatus in ['ok']:
                                td('{0} {1}'.format(pr.coursestatus, pr.timetommmss()))
                            elif pr.resultstatus in ['dns']:
                                td('{0}'.format(pr.resultstatus))
                            else:
                                td('{0} {1}*'.format(pr.resultstatus, pr.timetommmss()))
                            if (ec.scoremethod in ['worldcup', '1000pts', 'score1000']):
                                td('{0:d}'.format(int(pr.score))) if pr.score is not None else td()
                p(a("Menu", href="#lt-top"), cls="lg-mrg-bottom text-center")
            if len(self.teamclasses) > 0:
                for tc in self.teamclasses:
                    with div(cls="classResults lg-mrg-bottom"):
                        classresults = [r for r in self.teamresults if r.teamclassid == tc.id]
                        h3(tc.name, id=tc.shortname)
                        t = table(cls='table table-striped', id='TeamResultsTable-{0}'.format(tc.shortname)).add(tbody())
                        with t.add(tr(id='column-titles')):
                            classresults = _sortByPosition(classresults)
                            th('Place')
                            th('Points')
                            th('School / Name')
                            th('Finish')
                        for r in classresults:
                            with t.add(tr(cls="team-result-full")):
                                td(r.position) if r.position > 0 else td()
                                td('{0:d}'.format(int(r.score))) if r.score is not None else td()
                                try:
                                    td('{0} ({1})'.format(self.clubcodes[r.teamname_short][0].name, r.teamname_short))
                                except:
                                    td(r.teamname_short)
                                finpct = r.numfinishes if r.numfinishes == 0 else int((float(r.numfinishes)/r.numstarts)*100)
                                td('{0}% ({1} of {2})'.format(finpct, r.numfinishes, r.numstarts))
                            try:
                                memberids = [int(x) for x in r.resultids.split(',')]
                            except:
                                memberids = []
                            members = [x for x in self.personresults if x.id in memberids]
                            members = _sortByPosition(members)
                            for m in members:
                                with t.add(tr(cls="team-result-member")):
                                    td()
                                    td('{0:d}'.format(int(m.score))) if m.score is not None else td()
                                    td('{0} ({1})'.format(m.name, m.club_shortname))
                                    if m.coursestatus in ['ok']:
                                        td(m.timetommmss())
                                    elif m.resultstatus in ['ok']:
                                        td('{1} {0}'.format(m.timetommmss(), m.coursestatus))
                                    else:
                                        td('{1} {2} {0}'.format(m.timetommmss(), m.coursestatus, m.resultstatus))
                    p(a("Menu", href="#lt-top"), cls="lg-mrg-bottom text-center")
            h3("Result Status Codes")
            with dl(cls="dl-horizontal"):
                dt("msp: missing punch")
                dd("a control was skipped or taken out of order")
                dt("dnf: did not finish")
                dd("a control or set of controls at the end of the course were skipped")
                dt("nc: not competing")
                dd("the competitor is not eligible for standings, such as when running a second course")
                dt("dq: disqualified")
                dd("breaking competition rules, such as conferring with another competitor or entering an out of bounds area")
                dt("ovt: overtime")
                dd("returning after the course closure time")
                dt("dns: did not start")
                dd("the competitor did not start")
                dt("<time>*")
                dd("the star indicates course completion status was not reported and may be valid, msp, or dnf")
        return doc # __writeEventResultIndv_coc


    def __writeEventResultTeam(self):
        doc = dominate.document(title='Event Results')
        with doc.head:
            link(rel='stylesheet',
                 href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css',
                 integrity='sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7',
                 crossorigin='anonymous')
            link(rel='stylsheet',
                 href='https://maxcdn.bootstrapcdn.com/font-awesome/4.6.1/css/font-awesome.min.css')
            meta(name='viewport', content='width=device-width, initial-scale=1.0')
        with doc:
            page = div(cls='container-fluid')
        with page:
            with div(cls='row').add(div(cls='col-xs-12')):
                h1('Team Results for {0}'.format(self.event.name))
                try:
                    eventdate = datetime.date(*[int(x) for x in self.event.date.split('-')])
                    p('An orienteering event held at {0} on {1:%d %B %Y}'.format(self.event.venue, eventdate))
                except:
                    pass
                p('Team Competition Classes:')
            with div(cls='row'):
                for tc in self.teamclasses:
                    self.teamclasses.sort(key=lambda x: x.shortname)
                    div((a(tc.name, href='#{0}'.format(tc.shortname))), cls='col-md-3')
            for tc in self.teamclasses:
                with div(cls='row').add(div(cls='col-md-8')):
                    classresults = [r for r in self.teamresults if r.teamclassid == tc.id]
                    h3(tc.name, id=tc.shortname)
                    t = table(cls='table table-striped table-condensed', id='TeamResultsTable-{0}'.format(tc.shortname))
                    with t.add(tr(id='column-titles')):
                        classresults = _sortByPosition(classresults)
                        th('Pos.')
                        th('Name')
                        th('Score')
                    for r in classresults:
                        with t.add(tr()):
                            td(r.position) if r.position > 0 else td()
                            td(r.teamname_short)
                            td('{0:d}'.format(int(r.score))) if r.score is not None else td()
        return doc # __writeEventResultTeam


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
                                td(r['club'])
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
    def __init__(self, infiles, format, eventtype='standard', bibstart=1001):
        self.files = infiles
        self.format = format
        self.eventtype = eventtype
        self.bibnum = _nextbib(bibstart)

    def writeEntries(self):
        if self.format == 'OE':
            return self.__writeOEentries()
        elif self.format == 'CheckIn':
            return self.__writeCheckInEntries()
        else:
            raise KeyError("Unrecognized output format for entries: {}".format(self.format))

    def __writeOEentries(self):
        template = ';{0};;{1};;{2};{3};;{4};;{5};;;;0;;;;;;{6};;;;;{7};;;;;;;;;;;;;;;;;;;;;;;{8};0;X;;;;;;\n'
        doc = ''
        prefix = 'OESco0001;' if self.eventtype == 'score' else 'OE0001;'
        header = prefix + 'Stno;XStno;Chipno;Database Id;Surname;First name;YB;S;Block;nc;Start;Finish;Time;Classifier;Credit -;Penalty +;Comment;Club no.;Cl.name;City;Nat;Location;Region;Cl. no.;Short;Long;Entry cl. No;Entry class (short);Entry class (long);Rank;Ranking points;Num1;Num2;Num3;Text1;Text2;Text3;Addr. surname;Addr. first name;Street;Line2;Zip;Addr. city;Phone;Mobile;Fax;EMail;Rented;Start fee;Paid;Team;Course no.;Course;km;m;Course controls\n'
        doc += header
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
                    first = line[datacols['first']].strip('\"\'\/\\ ')
                    last = line[datacols['last']].strip('\"\'\/\\ ')
                    club = line[datacols['club']].strip('\"\'\/\\ ')
                    cat = line[datacols['cat']].strip('\"\'\/\\ ')
                    sex = line[datacols['sex']].strip('\"\'\/\\ ')
                    punch = line[datacols['punch']].strip('\"\'\/\\ ')
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
                    regline = template.format(stno, punch, last, first, sex, nc, club, cat, rented)
                    doc += regline
        return doc

    def __writeCheckInEntries(self):
        rentalDocA = '<h2>Pre-Registered List: RENTAL e-punches (List A)</h2>\n'
        rentalDocB = '<h2>Pre-Registered List: RENTAL e-punches (List B)</h2>\n'
        rentalDoc = '<h4>REGISTRATION VOLUNTEERS</h4><p>Check off ALL participants in the first column as they arrive. Collect money from those who owe it and mark it out.</br>Write in e-punch numbers (clearly!) and bring this page to finish ASAP while using the other copy of this list.</p>\n'
        rentalDoc += '<h4>FINISH VOLUNTEERS</h4><p>For any handwritten e-punch numbers without check marks, find the name in the e-punch software, enter the number, and add a check to this form. Return this list registration.</p>\n<hr />\n'
        ownersDoc = '<h2>Pre-Registered List: OWNED e-punches</h2>\n'
        ownersDoc += '<h4>REGISTRATION VOLUNTEERS</h4><p>Check off ALL participants in the first column as they arrive. Collect money from those who owe it and mark it out when paid.</p>\n<hr />\n'
        
        tablehead = '<table>\n<thead><tr><th class="check">&#x2714;</th><th>First</th><th>Last</th><th>Owes</th><th>Course</th><th>E-Punch</th><th>Club</th><th>Phone</th><th>Emergency Phone</th><th>Car</th></tr></thead>\n'

        rentalDoc += tablehead
        ownersDoc += tablehead
        OWN_TEMPLATE = '<tr><td class="check">{}</td><td>{}</td><td>{}</td><td class="owes">{}</td><td>{}</td><td class="punch">{}</td><td>{}</td><td class="phone">{}</td><td class="phone">{}</td><td class="license">{}</td></tr>\n'
        RENT_TEMPLATE = '<tr><td class="check">{}</td><td>{}</td><td>{}</td><td class="owes">{}</td><td>{}</td><td class="rentpunch"></td><td>{}</td><td class="phone">{}</td><td class="phone">{}</td><td class="license">{}</td></tr>\n'

        for f in self.files:

            for line in fileinput.input(files=(f), inplace=True):
                line = line.replace('\0', '')
                sys.stdout.write(line)

            with open(f, 'r') as currentfile:
                regreader = csv.reader(currentfile, delimiter=',')
                datacols = self.__identify_columns(next(regreader))
                
                for line in regreader:
                    first = line[datacols['first']].strip('\"\'\/\\ ').replace('_', ' ')
                    last = line[datacols['last']].strip('\"\'\/\\ ').replace('_', ' ')
                    club = line[datacols['club']].strip('\"\'\/\\ ')
                    cat = line[datacols['cat']].strip('\"\'\/\\ ')
                    sex = line[datacols['sex']].strip('\"\'\/\\ ')
                    punch = line[datacols['punch']].strip('\"\'\/\\ ')
                    paid = line[datacols['paid']].strip('\"\'\/\\ ')
                    owed = line[datacols['owed']].strip('\"\'\/\\ ')
                    phone = line[datacols['phone1']].strip('\"\'\/\\ ').replace('\\', ' ').replace('/', ' ').replace('-', '.')
                    phone2 = line[datacols['phone2']].strip('\"\'\/\\ ').replace('\\', ' ').replace('/', ' ').replace('-', '.')
                    license = line[datacols['license']].strip('\"\'\/\\ ')

                    rental = True if len(punch) == 0 else False
                    paid = True if len(owed) == 0 else False
                    

                    if (first == '') and (last == '') and (club == '') and (cat == ''):
                        continue
                    if not paid:
                        owed = '${}'.format(owed)
                        box = owed
                    else:
                        box = ''

                    if rental:
                        newline = RENT_TEMPLATE.format(box, first, last, owed, cat, club, phone, phone2, license)
                        rentalDoc += newline
                    else:
                        newline = OWN_TEMPLATE.format(box, first, last, owed, cat, punch, club, phone, phone2, license)
                        ownersDoc += newline
        rentalDocA += rentalDoc + '</table>\n'
        rentalDocB += rentalDoc + '</table>\n'
        ownersDoc += '</table>\n'
        pacificTZ = pytz.timezone('US/Pacific')
        utc = pytz.timezone('UTC')
        now = utc.localize(datetime.datetime.utcnow())
        localtime = now.astimezone(pacificTZ)
        timestamp = '<p id="createdate">{}</p>'.format(localtime.strftime('%H:%M %A %d %b %Y %Z%z'))
        header = '<!DOCTYPE html><html>\n<head>\n' + timestamp + '</head>\n'
        pagebreak = '\n<p style="page-break-before: always" ></p>\n'
        doc = header + ownersDoc + pagebreak + rentalDocA + pagebreak + rentalDocB + '</body></html>\n'
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
