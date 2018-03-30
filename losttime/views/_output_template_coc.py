# losttime/views/_output_template_coc.py

from _output_templates import EventHtmlWriter
from _output_templates import _sortByPosition
import datetime
import pytz
import csv, fileinput, sys
import dominate
from dominate.tags import *
from flask import flash


class EventHtmlWriter_COC(EventHtmlWriter):
    def __init__(self, event, classes=None, results=None, teamclasses=None, teamresults=None, clubcodes=None):
        super(EventHtmlWriter_COC, self).__init__(event, 'coc', classes, results, teamclasses, teamresults, clubcodes)

    def eventResultIndv(self):
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
                        if ec in WIOL:
                            th('School')
                        else:
                            th('Club')
                        if ec.scoremethod in ['score', 'score1000']:
                            th('Points')
                            th('Penalty')
                            th('Total')
                        th('Time', cls="text-right")
                        if ec.scoremethod in ['1000pts', 'worldcup', 'score1000']:
                            th('Score', cls="text-right")
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
                                td(pr.timetommmss(), cls="text-right")
                            elif pr.resultstatus in ['ok']:
                                td('{0} {1}'.format(pr.coursestatus, pr.timetommmss()), cls="text-right")
                            elif pr.resultstatus in ['dns']:
                                td('{0}'.format(pr.resultstatus), cls="text-right")
                            else:
                                td('{0} {1}*'.format(pr.resultstatus, pr.timetommmss()), cls="text-right")
                            if (ec.scoremethod in ['worldcup', '1000pts', 'score1000']):
                                td('{0:d}'.format(int(pr.score)), cls="text-right") if pr.score is not None else td()
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