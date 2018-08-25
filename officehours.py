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

with open('./example_officehours_constraints.csv', 'r') as f:
    print(file_to_constraints(f))


s = Solver()

tb = Const('tb', TimeBlock)

tb2 = timeblock(thursday, 9, 11)

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

s.add(endtime(tb) - starttime(tb) > 3)
s.add(starttime(tb) > 8)
s.add(TimeBlock.day(tb) == thursday)
#s.add(TimeBlock.day(tb2) == thursday)
#s.add(starttime(tb2) == 9)
#s.add(endtime(tb2) == 11)
s.add(Not(overlap_constraint_sameday(tb, tb2)))
print(s.check())
print(s.model())

students = {
    "alice": {
        "num_hours": 3,
        "blocked_times": [timeblock(monday, 8,9), timeblock(wednesday, 8, 9)]
    },
    "bob": {
        "num_hours": 4,
        "blocked_times": [timeblock(monday, 8,9), timeblock(tuesday, 10,12),
                          timeblock(wednesday, 14, 16)]
    },
    "charlie": {
        "num_hours": 4,
        "blocked_times": [timeblock(monday, 8,9), timeblock(tuesday, 10,12)]
    }
}

def make_constraints(students):
    s = Solver()

    max_slots = 4
    assignment_vars = defaultdict(list)
    all_svs = []

    # note: may have to choose smaller than hour
    # increments, in which case should still be integers
    FIRST_TIME = 8
    LAST_TIME = 18
    for key in students:
        for i in range(max_slots):
            sv = Const('{}_{}'.format(key, i), TimeBlock)
            all_svs.append(sv)
            # times must be > 0, end after start
            s.add(starttime(sv) >= FIRST_TIME)
            s.add(endtime(sv) > starttime(sv))
            s.add(endtime(sv) <= LAST_TIME)
            assignment_vars[key].append(sv)


        for sv in assignment_vars[key]:
            for blocked in students[key]["blocked_times"]:
                # no students' times can be 
                s.add(Not(overlap_constraint_sameday(sv, blocked)))

        assigned_count = count_assigned(assignment_vars[key])
        s.add(assigned_count >= 2)
        s.add(assigned_count <= 4)
        s.add(not_any_sameday(assignment_vars[key]))

    # desired goals globally: more coverage during busy times (say 11-4)
    # desired goals per student: 
    return s

s = make_constraints(students)
print(s.check())
print(s.model())
