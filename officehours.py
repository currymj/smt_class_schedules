from z3 import *
from collections import defaultdict
import csv
from pprint import pprint
from timeit import default_timer as timer

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
    "returns the length of a time block (defaulting to 0 for none)"
    return If(tb == none, 0, endtime(tb) - starttime(tb))

def count_assigned(tbs):
    "returns the number of variables in a list not assigned none"
    return Sum([If(tb == none, 0, 1) for tb in tbs])

def fieldname_to_time(fname):
    """
    Takes a fieldname from the constraint csv and turns it into
    a (day, time) tuple.
    """
    day = days_list[int(fname[0])]
    hour, minute = fname[1:].split('.')
    time = (int(hour) - 9)*4 + int(minute)
    return (day, time)

assert(fieldname_to_time("39.1") == (thursday, 1))
assert(fieldname_to_time("310.1") == (thursday, 5))

def line_to_constraints(input_line):
    """
    accepts a line from csv.reader and outputs constraints dictionary """
    constraints = {
        "impossible": [],
        "prefer_not": [],
        "num_hours": int(input_line[1])
    }

    line = input_line[2:] # drop name
    for i in range(0, len(line)-1, 2):
        time = fieldname_to_time(line[i])
        status = line[i+1]
        if status.lower() == 'x':
            constraints["impossible"].append(time)
        elif status.lower() != '1':
            constraints["prefer_not"].append(time)
    return constraints


def file_to_constraints(csvfile):
    csvreader = csv.reader(csvfile, delimiter=',')
    result_dictionary = {}
    for line in csvreader:
        result_dictionary[line[0]] = line_to_constraints(line)
    return result_dictionary

def includes_time_sameday(tb, day_and_time):
    day, time = day_and_time
    return And(TimeBlock.day(tb) == day,
               And(starttime(tb) <= time, endtime(tb) >= time))

def not_any_sameday(tbs):
    all_constraints = []
    for i in range(len(tbs)):
        for j in range(i+1, len(tbs)):
            all_constraints.append(
                Implies(
                    Not(Or(tbs[i] == none, tbs[j] == none)),
                    TimeBlock.day(tbs[i]) != TimeBlock.day(tbs[j])))
    return And(all_constraints)

with open('./hours_file.csv', 'r') as f:
    students = file_to_constraints(f)

#pprint(students)

def make_constraints(students):
    s = Optimize()

    max_slots = 3
    assignment_vars = defaultdict(list)
    all_svs = []

    # note: may have to choose smaller than hour
    # increments, in which case should still be integers
    FIRST_TIME = 1
    LAST_TIME = 40
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
            for day_and_time in students[student_name]["impossible"]:
                s.add(Not(includes_time_sameday(sv, day_and_time)))
            for day_and_time in students[student_name]["prefer_not"]:
                s.add_soft(Not(includes_time_sameday(sv, day_and_time)))

        assigned_count = count_assigned(assignment_vars[student_name])
        s.add(assigned_count >= 2)
        s.add(not_any_sameday(assignment_vars[student_name]))

        block_lengths = [block_length(tb) for tb in assignment_vars[student_name]]
        s.add(Sum(block_lengths) == students[student_name]["num_hours"])

    return s

s = make_constraints(students)
start = timer()
print(s.check())
end = timer()
print('Time taken to check sat: {}'.format(end-start))
print(s.model())
