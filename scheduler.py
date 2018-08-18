from z3 import *
from collections import defaultdict, namedtuple

Section = namedtuple('Section', ['classroom', 'time'])

def compat(interval1, interval2):
    """
    Returns true if two time intervals are compatible, i.e. don't overlap.
    """
    first_overlap = (interval1[0] <= interval2[0] <= interval1[1]) or (interval1[0] <= interval2[1] <= interval1[1])
    second_overlap = (interval2[0] <= interval1[0] <= interval2[1]) or (interval2[0] <= interval1[1] <= interval2[1])
    # compatible if no overlap
    return (not (first_overlap or second_overlap))

def sections_compat(section1, section2):
    """
    Returns true if two sections are compatible, i.e. don't overlap,
    except for special case where two sections are back-to-back in the
    same classroom.
    """
    if section1.classroom == section2.classroom:
        if (section1.time[1] == section2.time[0] or
                section2.time[1] == section1.time[0]):
            return True
    return compat(section1.time, section2.time)


def make_constraints(students, sections):
    student_vars = defaultdict(list)
    flattened_vars = []

    #s = Solver()
    s = Optimize()

    # two possible section assignments per student
    # must be assigned to section i (1-indexed) , or 0 (no assignment)
    for key in students:
        for i in range(2):
            sv = Int('{}_{}'.format(key, i))
            s.add(sv >= 0)
            s.add(sv <= len(sections))
            flattened_vars.append(sv)
            student_vars[key].append(sv)

    # ensure one student assigned to each section
    all_sections_matched_list = []
    for required in range(1,len(sections)+1):
        any_one_section = [sv == required for sv in flattened_vars]
        all_sections_matched_list.append(Or(*any_one_section))
    s.add(And(*all_sections_matched_list))

    # constrain compatibility for each student
    for key in student_vars:
        student_schedule = students[key]["classes"]
        current_student_variables = student_vars[key]

        for section_id in range(1,len(sections)+1):
            i = section_id - 1
            for class_time in student_schedule:
                if not compat(class_time, sections[i].time):
                    for sv in current_student_variables:
                        s.add(sv != section_id)

    # ensure no student is assigned to overlapping sections
    # by rights this part should allow an overlap if the sections
    # are in the same classroom and next to each other
    incompatible_pairs = []
    for section_id_1 in range(1,len(sections)+1):
        i = section_id_1 - 1
        for section_id_2 in range(section_id_1, len(sections)+1):
            j = section_id_2 - 1
            if not sections_compat(sections[i], sections[j]): 
                incompatible_pairs.append( (section_id_1, section_id_2))


    for key in student_vars:
        current_student_variables = student_vars[key]
        # right now assume at most two sections per student
        if len(current_student_variables) == 2:
            sv1 = current_student_variables[0]
            sv2 = current_student_variables[1]
            for a, b in incompatible_pairs:
                s.add(Not( Or(
                    And(sv1 == a, sv2 == b),
                    And(sv1 == b, sv2 == a)
                )))


    # soft constraints
    for key in student_vars:
        student_schedule = students[key]["preferences"]
        current_student_variables = student_vars[key]

        for section_id in range(1,len(sections)+1):
            i = section_id - 1
            for class_time in student_schedule:
                if not compat(class_time, sections[i].time):
                    for sv in current_student_variables:
                        s.add_soft(sv != section_id)


    # what else might we need????
    return s, student_vars

