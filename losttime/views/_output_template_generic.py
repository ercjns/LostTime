# losttime/views/_output_template_generic.py

from _output_templates import EventHtmlWriter
from _output_templates import _sortByPosition
import datetime
import pytz
import csv, fileinput, sys
import dominate
from dominate.tags import *
from flask import flash


class EventHtmlWriter_Generic(EventHtmlWriter):
    def __init__(self, event, classes=None, results=None, teamclasses=None, teamresults=None, clubcodes=None):
        super(EventHtmlWriter_Generic, self).__init__(event, classes, results, teamclasses, teamresults, clubcodes)

    def eventResultIndv(self):
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

    def eventResultTeam(self):
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
                    t = table(cls='table table-striped table-condensed',
                              id='TeamResultsTable-{0}'.format(tc.shortname))
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
        return doc  # __writeEventResultTeam


