# losttime/views/_output_templates.py

import datetime
import dominate
from dominate.tags import *

class EventHtmlWriter(object):
    def __init__(self, event, classes=None, results=None):
        self.event = event
        self.eventclasses = classes
        self.personresults = results

    def eventResultIndv(self):
        """
        create an html file with individual results for this event.
        """
        # in the future, switch based on template here
        return _writeEventResultIndv(self.event, self.eventclasses, self.personresults)



def _writeEventResultIndv(event, classes, results):
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
            h1('Results for {0}'.format(event.name))
            try:
                eventdate = datetime.date(*[int(x) for x in event.date.split('-')])
                p('An orienteering event held at {0} on {1:%d %B %Y}'.format(event.venue, eventdate))
            except:
                pass
            p('Competition Classes:')
        with div(cls='row'):
            for ec in classes:
                div((a(ec.name, href='#{0}'.format(ec.shortname))), cls='col-md-3')
        for ec in classes:
            with div(cls='row').add(div(cls='col-md-8')):
                classresults = [r for r in results if r.classid == ec.id]
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
    return doc


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
