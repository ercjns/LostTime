# A Library to handle assigning WIOL start times

import datetime as dt
from nptime import nptime
import csv
from random import shuffle

class Start(object):
    def __init__(self, start_time, school=None, individual=None):
        self._OCCUPIED = False
        self._REQUEST = False
        self.start_time = start_time #nptime object
        self.school = school #string
        self.individual = individual #string
        if self.school:
            self._OCCUPIED = True
        if self.individual:
            self._REQUEST = True
        return

    def assign_start(self, school, individual=None):
        if school == None:
            return
        if self._OCCUPIED == True:
            raise
        self._OCCUPIED = True
        self.school = school
        self.individual = individual
        if self.individual:
            self._REQUEST == True
        return

    def unassign_start(self):
        self._OCCUPIED = False
        self._REQUEST = False
        self.school = None
        self.individual = None
        return

class Course(object):
    def __init__(self, code, name=None, short=None, first=None, interval=None, last=None):
        self.code = code # string
        self.name = name # string
        self.name_short = short # string
        self.first = first # nptime
        self.interval = interval # timedelta
        self.last = last # nptime
        self.starts = [] # list of Start objects
        self.sandbox = [] # list of strings (school names)
        self._generate_starts()
        return

    def _generate_starts(self):
        if ((self.first == None)
           or (self.interval == None)
           or (self.last == None)):
            # WARN but return as if nothing happened
            return
        time = self.first
        while time <= self.last:
            self.starts.append(Start(time))
            time = time + self.interval
        self._order_starts()
        return

    def _order_starts(self, reverse=False):
        self.starts.sort(key=lambda start:start.start_time, reverse=reverse)

    def getEarliestAvailableStart(self):
        self._order_starts()
        for s in self.starts:
            if not s._OCCUPIED:
                return s
            continue
        return None

    def spreadTeams(self, spacing=1, reverse=False):
        # modifies self.sandbox IN PLACE. Does not Assign Starts.
        # spacing: how many must be different between same team. 
        # reverse: False goes early to late, moving people up.
        self.sandbox = [x for x in self.sandbox if x != None]
        if reverse:
            self.sandbox.reverse()

        # while loop because len(self.sandbox) can expand.
        i = 0 
        while i < len(self.sandbox):
            # create the the slice to compare against
            first = i - spacing if (i-spacing)>=0 else 0
            last = i
            slice_to_check_for_dupes = self.sandbox[first:last]

            if self.sandbox[i] in slice_to_check_for_dupes:
                # can't have this item at this index
                # find the first item that is valid for this index
                rest_of_list = self.sandbox[i+1:]
                inserted = False
                for j, item in enumerate(rest_of_list):
                    if item not in slice_to_check_for_dupes:
                        popped = self.sandbox.pop(i+j+1)
                        self.sandbox.insert(i, item)
                        # print("Inserting {}".format(item))
                        inserted = True
                        break
                if not inserted:
                    self.sandbox.insert(i, None)
                    # print("No items to insert, inserted None")

            else:
                # valid start time at this index.
                # print("This item OK {} {}".format(self.sandbox[i], i))
                pass
            # move on to next index in the sandbox
            i += 1

        if reverse:
            self.sandbox.reverse()
        return

    def getAssignedStarts(self):
        self._order_starts()
        return [x for x in self.starts if x._OCCUPIED == True]

    def getStartAtTime(self, time):
        for s in self.starts:
            if s.start_time == time:
                return s
                break
        return None

    def getStartsForSchool(self, school):
        self._order_starts()
        return [x for x in self.starts if x.school == school]

class Registration(object):
    def __init__(self, school, course, number):
        self.school = school # string
        self.course = course # course object
        self.number = int(number) # how many on this course
        return

class Event(object):
    def __init__(self):
        self.courses = [] # Course objects
        self.registrations = [] # Registration objects
        self.schools = None # list of strings (populated by create_registrations)

    def add_courses(self, file):
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                code = row['ID']
                name = row['NAME']
                short = row['SHORT']
                first = _hms_to_nptime(row['FIRST'])
                interval = _hms_to_timedelta(row['INTERVAL'])
                last = _hms_to_nptime(row['LAST'])
                c = Course(code, name, short, first, interval, last)
                self.courses.append(c)
            self.courses.sort(key=lambda course:course.code)
        return

    def get_course_by_shortname(self, shortname):
        for course in self.courses:
            if course.name_short == shortname:
                return course
                break
        return None

    def create_registrations(self, file):
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                school = row['SCHOOL']
                if school.lower() == 'total':
                    continue
                for course in self.courses:
                    try:
                        number = int(row[course.name_short])
                    except:
                        number = 0
                    if number > 0:
                        r = Registration(school, course, number)
                        self.registrations.append(r)
        self.schools = list(set(r.school for r in self.registrations))
        return

    def getSchoolRegistrations(self, school):
        return [x for x in self.registrations if x.school == school]

    def assign_starts(self):
        shuffle(self.schools)
        for s in self.schools:
            registrations = self.getSchoolRegistrations(s)
            for r in registrations:
                for i in range(r.number):
                    r.course.sandbox.append(r.school)
        for c in self.courses:
            spacing = 1 if c.name_short == 'ELEM' else 2
            c.spreadTeams(spacing)
            c.spreadTeams(spacing, reverse=True)
            # pair up this new order with the empty starts
            toAssign = zip(c.sandbox, c.starts)
            # assign the actual start times
            for school, start in toAssign:
                start.assign_start(school)
        return

    def get_starts_by_time(self, time):
        # helps to support export
        starts = {}
        for c in self.courses:
            s = c.getStartAtTime(time)
            if s:
                starts[c.name] = s.school
        return starts

    def export_start_list(self, outpath='MasterStartList.csv'):
        starttimes = set()
        for c in self.courses:
            for s in c.starts:
                starttimes.add(s.start_time)
        starttimes = list(starttimes)
        starttimes.sort() #rows

        fieldnames = ['Time'] + [x.name for x in self.courses]

        with open(outpath, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in starttimes:
                data = self.get_starts_by_time(t)
                data['Time'] = t
                writer.writerow(data)

        #TODO add some stats here to indicate how well assignment went...
        return

def _hms_to_nptime(hms):
    h,m,s = hms.split(':')
    return nptime(hour=int(h), minute=int(m), second=int(s))

def _hms_to_timedelta(hms):
    h,m,s = hms.split(':')
    return dt.timedelta(hours=int(h), minutes=int(m), seconds=int(s))

if __name__ == '__main__':
    e = Event()
    e.add_courses('courses_test.csv')
    e.create_registrations('registrations_test.csv')
    e.assign_starts()
    e.export_start_list()