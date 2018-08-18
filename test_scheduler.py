from scheduler import make_constraints, Section

def test_one():
    students = {
        "alice": {
            "classes":[[13.5, 14.5], [9.5,10.75]],
            "preferences": []
        },
        "bob": {"classes": [[9.5, 11.0]], "preferences": []},
        "charlie": {"classes": [], "preferences": []}
    }

    sections = [Section('1111', [8.0, 9.0]), Section('2222', [9.0, 10.0]), Section('3333', [11.0, 12.0]), Section('4444', [13.0, 14.0])]

    s, _ = make_constraints(students, sections)
    assert(str(s.check()) == 'sat')

def test_overlap_sections():
    students = {"charlie": {"classes": [], "preferences": []}}
    sections = [Section("1111", [9.0,10.0]), Section("2222", [9.0,10.0])]
    s, _ = make_constraints(students, sections)
    assert(str(s.check()) == 'unsat')

def test_backtoback_different():
    students = {"charlie": {"classes": [], "preferences": []}}
    sections = [Section("1111", [9.0,10.0]), Section("2222", [10.0,11.0])]
    s, _ = make_constraints(students, sections)
    assert(str(s.check()) == 'unsat')


def test_backtoback_same():
    students = {"charlie": {"classes": [], "preferences": []}}
    sections = [Section("1111", [9.0,10.0]), Section("1111", [10.0,11.0])]
    s, _ = make_constraints(students, sections)
    assert(str(s.check()) == 'sat')

def test_preference_satisfied():
    students = {"charlie":
                {"classes": [], "preferences": [[9.0, 10.0]]},
                "bob": {"classes": [], "preferences": [[12.0, 14.0]]}}
    sections = [Section("1111", [9.0,10.0]), Section("1111", [13.0, 14.0])]
    s, student_vars = make_constraints(students, sections)

    assert(str(s.check()) == 'sat')
    m = s.model()

    charlie_vars = student_vars['charlie']
    bob_vars = student_vars['bob']

    assert((m.eval(charlie_vars[0]) == 2) or (m.eval(charlie_vars[1]) == 2))
    assert((m.eval(bob_vars[0]) == 1) or (m.eval(bob_vars[1]) == 1))

def test_preference_ignored_if_necessary():
    students = {"charlie":
                {"classes": [], "preferences": [[9.0, 10.0]]}}
    sections = [Section("1111", [9.0,10.0])]
    s, _ = make_constraints(students, sections)
    assert(str(s.check()) == 'sat')




