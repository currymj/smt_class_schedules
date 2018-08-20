from z3 import *
from collections import defaultdict

Day, (monday, tuesday, wednesday, thursday, friday) = EnumSort('Day',
                                                               ('monday', 'tuesday', 'wednesday', 'thursday', 'friday'))

TimeBlock = Datatype('TimeBlock')
TimeBlock.declare('timeblock', ('day', Day), ('starttime', IntSort()), ('endtime', IntSort()))
TimeBlock = TimeBlock.create()
timeblock = TimeBlock.timeblock
starttime = TimeBlock.starttime
endtime = TimeBlock.endtime

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

s.add(endtime(tb) - starttime(tb) > 3)
s.add(starttime(tb) > 8)
s.add(TimeBlock.day(tb) == thursday)
#s.add(TimeBlock.day(tb2) == thursday)
#s.add(starttime(tb2) == 9)
#s.add(endtime(tb2) == 11)
s.add(Not(overlap_constraint_sameday(tb, tb2)))
print(s.check())
print(s.model())

students = {"charlie": {
    "num_hours": 4,
    "blocked_times": [timeblock(monday, 8,9), timeblock(tuesday, 10,12)]
}}

def make_constraints(students):
    s = Solver()

    max_slots = 4
    assignment_vars = defaultdict(list)
    all_svs = []
    for key in students:
        for i in range(max_slots):
            sv = Const('{}_{}'.format(key, i), TimeBlock)
            all_svs.append(sv)
            s.add(starttime(sv) > 0)
            s.add(endtime(sv) > starttime(sv))
            assignment_vars[key].append(sv)

        for sv in assignment_vars[key]:
            for blocked in students[key]["blocked_times"]:
                s.add(Not(overlap_constraint_sameday(sv, blocked)))

        assignment_times = [endtime(tb) - starttime(tb) for tb in assignment_vars[key]]
        s.add(Sum(assignment_times) == students[key]["num_hours"])
    return s

s = make_constraints(students)
print(s.check())
print(s.model())
