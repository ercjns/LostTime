# losttime/views/_output_templates.py

import datetime
import csv
import dominate
from dominate.tags import *

class EventHtmlWriter(object):
    def __init__(self, event, format='generic', classes=None, results=None, teamclasses=None, teamresults=None):
        self.event = event
        self.format = format
        self.eventclasses = classes
        self.personresults = results
        self.teamclasses = teamclasses
        self.teamresults = teamresults

    def eventResultIndv(self):
        """
        create an html file with individual results for this event.
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
        if self.format == 'generic':
            return self.__writeEventResultTeam()
        if self.format == 'coc':
            return self.__writeEventResultTeam_coc()
        else:
            raise KeyError("Unrecognized output format {0}".format(self.format))


    def __writeEventResultIndv(self):
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
                        if ec.scoremethod in ['time', 'worldcup', '1000pts']:
                            classresults = _sortByPosition(classresults)
                            th('Pos.')
                        th('Name')
                        if ec.scoremethod in ['alpha']:
                            classresults = _sortByName(classresults)
                        th('Club')
                        th('Time')
                        if ec.scoremethod in ['1000pts', 'worldcup']:
                            th('Score')
                    for pr in classresults:
                        with t.add(tr()):
                            if ec.scoremethod in ['time', 'worldcup', '1000pts']:
                                td(pr.position) if pr.position > 0 else td()
                            td(pr.name)
                            td(pr.club_shortname) if pr.club_shortname else td()
                            if pr.coursestatus in ['ok']:
                                td(pr.timetommmss())
                            elif pr.resultstatus in ['ok']:
                                td('{1} {0}'.format(pr.timetommmss(), pr.coursestatus))
                            else:
                                td('{1} {2} {0}'.format(pr.timetommmss(), pr.coursestatus, pr.resultstatus))
                            if (ec.scoremethod in ['worldcup', '1000pts']):
                                td('{0:d}'.format(int(pr.score))) if pr.score is not None else td()
        return doc # __writeEventResultIndv

    def __writeEventResultIndv_coc(self):
        doc = div(cls="LostTimeContent")
        with doc:
            with div(cls="lg-mrg-bottom"):
                self.eventclasses.sort(key=lambda x: x.shortname)
                for ec in self.eventclasses:
                    h3(a(ec.name, href='#{0}'.format(ec.shortname)))
            for ec in self.eventclasses:
                with div(cls="classResults lg-mrg-bottom"):
                    classresults = [r for r in self.personresults if r.classid == ec.id]
                    h3(ec.name, id=ec.shortname)
                    t = table(cls="table table-striped", id='ResultsTable-{0}'.format(ec.shortname)).add(tbody())
                    with t.add(tr(id="column-titles")):
                        if ec.scoremethod in ['time', 'worldcup', '1000pts']:
                            classresults = _sortByPosition(classresults)
                            th('Pos.')
                        th('Name')
                        th('Club')
                        th('Time')
                        if ec.scoremethod in ['1000pts', 'worldcup']:
                            th('Score')
                    for pr in classresults:
                        with t.add(tr()):
                            if ec.scoremethod in ['time', 'worldcup', '1000pts']:
                                td(pr.position) if pr.position > 0 else td()
                            td(pr.name)
                            td(pr.club_shortname) if pr.club_shortname else td()
                            if pr.coursestatus in ['ok']:
                                td(pr.timetommmss())
                            elif pr.resultstatus in ['ok']:
                                td('{1} {0}'.format(pr.timetommmss(), pr.coursestatus))
                            else:
                                td('{1} {2} {0}'.format(pr.timetommmss(), pr.coursestatus, pr.resultstatus))
                            if (ec.scoremethod in ['worldcup', '1000pts']):
                                td('{0:d}'.format(int(pr.score))) if pr.score is not None else td()
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

    def __writeEventResultTeam_coc(self):
        doc = div(cls="LostTimeContent")
        with doc:
            with div(cls="lg-mrg-bottom"):
                for tc in self.teamclasses:
                    self.teamclasses.sort(key=lambda x: x.shortname)
                    h3(a(tc.name, href='#{0}'.format(tc.shortname)))
            for tc in self.teamclasses:
                with div(cls="classResults lg-mrg-bottom"):
                    classresults = [r for r in self.teamresults if r.teamclassid == tc.id]
                    h3(tc.name, id=tc.shortname)
                    t = table(cls='table table-striped', id='TeamResultsTable-{0}'.format(tc.shortname)).add(tbody())
                    with t.add(tr(id='column-titles')):
                        classresults = _sortByPosition(classresults)
                        th('Pos.')
                        th('Name')
                        th('Score')
                    for r in classresults:
                        try:
                            memberids = [int(x) for x in r.resultids.split(',')]
                        except:
                            memberids = []
                        members = [x for x in self.personresults if x.id in memberids]
                        members = _sortByPosition(members)
                        with t.add(tr(cls="team-result")):
                            td(r.position) if r.position > 0 else td()
                            td(r.teamname_short)
                            td('{0:d}'.format(int(r.score))) if r.score is not None else td()
                        for m in members:
                            with t.add(tr(cls="team-member")):
                                td()
                                td()
                                td('{0:d}'.format(int(m.score))) if m.score is not None else td()
                                td(m.name)
                                if m.coursestatus in ['ok']:
                                    td(m.timetommmss())
                                elif m.resultstatus in ['ok']:
                                    td('{1} {0}'.format(m.timetommmss(), m.coursestatus))
                                else:
                                    td('{1} {2} {0}'.format(m.timetommmss(), m.coursestatus, m.resultstatus))
        return doc # __writeEventResultTeam_coc


class EntryWriter(object):
    def __init__(self, infiles, format, eventtype='standard', bibstart=1001):
        self.files = infiles
        self.format = format
        self.eventtype = eventtype
        self.bibnum = _nextbib(bibstart)

    def writeEntries(self):
        if self.format == 'OE':
            return self.__writeOEentries()
        else:
            raise KeyError("Unrecognized output format for entries")

    def __writeOEentries(self):
        template = ';{0};;{1};;{2};{3};;{4};;{5};;;;0;;;;;;{6};;;;;{7};;;;;;;;;;;;;;;;;;;;;;;{8};0;X;;;;;;\n'
        doc = ''
        prefix = 'OESco0001;' if self.eventtype == 'score' else 'OE0001;'
        header = prefix + 'Stno;XStno;Chipno;Database Id;Surname;First name;YB;S;Block;nc;Start;Finish;Time;Classifier;Credit -;Penalty +;Comment;Club no.;Cl.name;City;Nat;Location;Region;Cl. no.;Short;Long;Entry cl. No;Entry class (short);Entry class (long);Rank;Ranking points;Num1;Num2;Num3;Text1;Text2;Text3;Addr. surname;Addr. first name;Street;Line2;Zip;Addr. city;Phone;Mobile;Fax;EMail;Rented;Start fee;Paid;Team;Course no.;Course;km;m;Course controls\n'
        doc += header
        for f in self.files:
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
