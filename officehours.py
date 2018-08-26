from z3 import *
from collections import defaultdict
import csv



Day, (monday, tuesday, wednesday, thursday, friday) = EnumSort(
    'Day', ('monday', 'tuesday', 'wednesday', 'thursday', 'friday'))
days_list = [monday, tuesday, wednesday, thursday, friday]

TimeBlock = Datatype('TimeBlock')
TimeBlock.declare('timeblock', ('day', Day), ('starttime', IntSort()), ('endtime', IntSort()))
TimeBlock.declare('none')
TimeBlock = TimeBlock.create()
timeblock = TimeBlock.timeblock
starttime = TimeBlock.starttime
endtime = TimeBlock.endtime
none = TimeBlock.none

def block_length(tb):
    return If(tb == none, 0, endtime(tb) - starttime(tb))

def count_assigned(tbs):
    return Sum([If(tb == none, 0, 1) for tb in tbs])

def file_to_constraints(csvfile):
    result_dictionary = {
        "impossible": [],
        "prefer_not": []
    }
    csvreader = csv.reader(csvfile, delimiter=',')
    next(csvreader, None) # skip header
    time_block = 0
    for csvline in csvreader:
        time_block += 1
        for i, day in enumerate(days_list, 1):
            if csvline[i].lower() == 'x':
                result_dictionary["impossible"].append( (day, time_block))
            if csvline[i].lower() == '2':
                result_dictionary["prefer_not"].append( (day, time_block))
    return result_dictionary


def fieldname_to_time(fname):
    day = days_list[int(fname[0])]
    hour, minute = fname[1:].split('.')
    time = (int(hour) - 9)*4 + int(minute)
    return (day, time)

assert(fieldname_to_time("39.1") == (thursday, 1))
assert(fieldname_to_time("310.1") == (thursday, 5))

def line_to_constraints(input_line):
    """
    accepts a line from csv.reader and outputs constraints dictionary
    """
    raise NotImplementedError



def includes_time_sameday(tb, day_and_time):
    day, time = day_and_time
    return And(TimeBlock.day(tb) == day,
               And(starttime(tb) <= time, endtime(tb) >= time))




def overlap_constraint(tb1, tb2):
    """
    Returns a boolean statement that is true if tb1 and tb2 overlap,
    without regard to day.
    """
    # start1 <= start2 <= end1 OR start2 <= start1 <= end2 should cover
    # all four cases
    overlap1 = And(starttime(tb1) <= starttime(tb2), starttime(tb2) <= endtime(tb1))
    overlap2 = And(starttime(tb2) <= starttime(tb1), starttime(tb1) <= endtime(tb2))
    return Or(overlap1, overlap2)

def overlap_constraint_sameday(tb1, tb2):
    """
    Returns a boolean statement that is true if tb1 and tb2 overlap,
    taking into account their day.
    """
    return And(overlap_constraint(tb1, tb2), TimeBlock.day(tb1) == TimeBlock.day(tb2))

def not_any_sameday(tbs):
    all_constraints = []
    for i in range(len(tbs)):
        for j in range(i+1, len(tbs)):
            all_constraints.append(
                Implies(
                    Not(Or(tbs[i] == none, tbs[j] == none)),
                    TimeBlock.day(tbs[i]) != TimeBlock.day(tbs[j])))
    return And(all_constraints)

with open('./example_officehours_constraints.csv', 'r') as f:
    example_constraints = file_to_constraints(f)

students = {
    "alice": {
        "constraints": example_constraints,
        "num_hours": 3
    },
    "bob": {
        "constraints": example_constraints,
        "num_hours": 3
    },
    "charlie": {
        "constraints": example_constraints,
        "num_hours": 4
    }
}

def make_constraints(students):
    s = Optimize()

    max_slots = 3
    assignment_vars = defaultdict(list)
    all_svs = []

    # note: may have to choose smaller than hour
    # increments, in which case should still be integers
    FIRST_TIME = 1
    LAST_TIME = 41
    for student_name in students:
        for i in range(max_slots):
            sv = Const('{}_{}'.format(student_name, i), TimeBlock)
            all_svs.append(sv)
            # times must be > 0, end after start
            s.add(starttime(sv) >= FIRST_TIME)
            s.add(endtime(sv) > starttime(sv))
            s.add(endtime(sv) <= LAST_TIME)
            assignment_vars[student_name].append(sv)


        for sv in assignment_vars[student_name]:
            for day_and_time in students[student_name]["constraints"]["impossible"]:
                s.add(Not(includes_time_sameday(sv, day_and_time)))
            for day_and_time in students[student_name]["constraints"]["prefer_not"]:
                s.add_soft(Not(includes_time_sameday(sv, day_and_time)))

        assigned_count = count_assigned(assignment_vars[student_name])
        s.add(assigned_count >= 2)
        s.add(not_any_sameday(assignment_vars[student_name]))

        block_lengths = [block_length(tb) for tb in assignment_vars[student_name]]
        s.add(Sum(block_lengths) == students[student_name]["num_hours"])

    return s

s = make_constraints(students)
print(s.check())
print(s.model())
