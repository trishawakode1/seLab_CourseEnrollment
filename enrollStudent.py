# ============================================================
# UC-01: Enroll in Course
# E-Learning Portal — Software Engineering Assignment
# Black Box Testing: ECP + BVA on Course ID & Student Eligibility
# ============================================================

import re
from dataclasses import dataclass, field
from typing import Dict, List


# ============================================================
# ENTITY OBJECTS  (ECB — Entity layer)
# ============================================================

@dataclass
class Course:
    course_id:       str
    name:            str
    available:       bool
    seats_available: int


@dataclass
class Student:
    student_id:          str
    name:                str
    logged_in:           bool
    enrolled_course_ids: List[str] = field(default_factory=list)


@dataclass
class Enrollment:
    enrollment_id: str
    student_id:    str
    course_id:     str
    has_access:    bool = True


# ============================================================
# BOUNDARY OBJECT  (ECB — Enrollment Form UI)
# Course ID rules:  alphanumeric only, 1-10 characters.
# Student ID rules: alphanumeric only, non-empty.
# ============================================================

@dataclass
class EnrollmentRequest:
    student_id: str
    course_id:  str


class EnrollmentFormUI:
    _VALID_ID       = re.compile(r'^[A-Za-z0-9]+$')
    _MAX_COURSE_LEN = 10

    @classmethod
    def build_request(cls, student_id: str, course_id: str) -> EnrollmentRequest:
        if not student_id:
            raise ValueError("Invalid student ID")
        if not cls._VALID_ID.match(student_id):
            raise ValueError("Invalid student ID")
        if not course_id:
            raise ValueError("Invalid course ID")
        if not cls._VALID_ID.match(course_id):
            raise ValueError("Invalid course ID")
        if len(course_id) > cls._MAX_COURSE_LEN:
            raise ValueError("Invalid course ID")
        return EnrollmentRequest(student_id=student_id, course_id=course_id)


# ============================================================
# CONTROL OBJECT  (ECB — Enrollment Controller)
# ============================================================

class EnrollmentController:

    def __init__(self):
        self._students:       Dict[str, Student]  = {}
        self._courses:        Dict[str, Course]   = {}
        self._enrollments:    List[Enrollment]    = []
        self._next_enroll_id: int                 = 1

    def add_student(self, student: Student) -> None:
        self._students[student.student_id] = student

    def add_course(self, course: Course) -> None:
        self._courses[course.course_id] = course

    def get_enrolled_courses(self, student_id: str) -> List[str]:
        s = self._students.get(student_id)
        return list(s.enrolled_course_ids) if s else []

    def has_access(self, student_id: str, course_id: str) -> bool:
        return any(
            e.student_id == student_id and e.course_id == course_id
            for e in self._enrollments
        )

    def _check_availability(self, course: Course) -> bool:
        return course.available and course.seats_available > 0

    def _create_enrollment(self, student_id: str, course_id: str) -> Enrollment:
        eid = f"E{self._next_enroll_id}"
        self._next_enroll_id += 1
        e = Enrollment(enrollment_id=eid, student_id=student_id, course_id=course_id)
        self._enrollments.append(e)
        self._students[student_id].enrolled_course_ids.append(course_id)
        return e

    def enroll(self, request: EnrollmentRequest, acting_student_id: str) -> str:
        if acting_student_id not in self._students:
            raise LookupError("Student not found")
        if not self._students[acting_student_id].logged_in:
            raise PermissionError("Student must be logged in")
        if request.student_id not in self._students:
            raise LookupError("Student not found")
        if request.course_id not in self._courses:
            raise LookupError("Course not found")

        course = self._courses[request.course_id]

        if not self._check_availability(course):
            return "ERROR: Course is unavailable — redirecting to browse page"

        for e in self._enrollments:
            if e.student_id == request.student_id and e.course_id == request.course_id:
                raise ValueError("Student already enrolled in this course")

        course.seats_available -= 1
        enrollment = self._create_enrollment(request.student_id, request.course_id)
        student_name = self._students[request.student_id].name
        return (f"SUCCESS: Enrollment successful [ID={enrollment.enrollment_id}]"
                f" — {student_name} enrolled in {course.name}")


# ============================================================
# TEST DATA SEED
# ============================================================

def fresh_controller() -> EnrollmentController:
    ec = EnrollmentController()
    ec.add_student(Student("S001", "Trisha Wakode",   logged_in=True))
    ec.add_student(Student("S002", "Rahul Mehta",     logged_in=True))
    ec.add_student(Student("S004", "Logged Out User", logged_in=False))
    ec.add_student(Student("1001", "Numeric Student", logged_in=True))
    # S999 deliberately absent

    ec.add_course(Course("C101",  "Software Engineering", available=True,  seats_available=30))
    ec.add_course(Course("C102",  "Data Structures",      available=True,  seats_available=25))
    ec.add_course(Course("C103",  "Operating Systems",    available=True,  seats_available=20))
    ec.add_course(Course("C1",    "Intro Course",         available=True,  seats_available=10))
    ec.add_course(Course("C999",  "Unavailable Course",   available=False, seats_available=0))
    ec.add_course(Course("C104",  "Full Course",          available=True,  seats_available=0))
    # C000 deliberately absent
    return ec


# ============================================================
# TEST HARNESS
# ============================================================

def run_test(tc_id, tc_label, technique, scenario, inputs, expected,
             action, expect_exception=False):
    actual = ""
    passed = False
    try:
        actual = action()
        if not expect_exception:
            passed = expected in actual
        else:
            actual = f"[No exception thrown] Got: {actual}"
            passed = False
    except Exception as ex:
        actual = f"[Exception] {type(ex).__name__}: {ex}"
        if expect_exception:
            passed = expected in str(ex)

    return {
        "id": tc_id, "label": tc_label, "technique": technique,
        "scenario": scenario, "inputs": inputs,
        "expected": expected, "actual": actual, "passed": passed,
    }


def print_detail(r, index):
    status = "PASS" if r["passed"] else "FAIL"
    bar    = "=" * 72
    print(f"\n{bar}")
    print(f"  Test {index:>2} | {r['label']:<12} | Technique : {r['technique']}")
    print(f"  Scenario  : {r['scenario']}")
    print(f"  {'-'*68}")
    print(f"  Inputs    :")
    for k, v in r["inputs"].items():
        print(f"              {k:<24} = {v}")
    print(f"  {'-'*68}")
    print(f"  Expected  : {r['expected']}")
    print(f"  Actual    : {r['actual']}")
    print(f"  Result    : >>> {status} <<<")
    print(f"{bar}")


# ============================================================
# MAIN — 15 ECP + BVA test cases
# ============================================================

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         UC-01: Enroll in Course — Black Box Test Suite               ║
║         Techniques : Equivalence Class Partitioning (ECP)            ║
║                      Boundary Value Analysis (BVA)                   ║
║         Focus      : Course ID validity  |  Student Eligibility      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    results = []

    # ── PART A — ECP: Course ID ──────────────────────────────────────
    print("━" * 72)
    print("  PART A  —  ECP: Course ID Equivalence Classes")
    print("━" * 72)

    # TC-ECP01
    ec = fresh_controller()
    r = run_test(1, "TC-ECP01", "ECP — Valid partition",
        "Valid alphanumeric course ID that exists in the system",
        {"student_id": "S001", "logged_in": True,
         "course_id": "C101", "course_available": True, "seats": 30},
        "SUCCESS",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001"))
    results.append(r); print_detail(r, 1)

    # TC-ECP02
    ec = fresh_controller()
    ec.add_course(Course("CS202", "Computer Science", available=True, seats_available=15))
    r = run_test(2, "TC-ECP02", "ECP — Valid partition",
        "Longer valid alphanumeric course ID (multi-char prefix, exists)",
        {"student_id": "S001", "logged_in": True,
         "course_id": "CS202", "course_available": True, "seats": 15},
        "SUCCESS",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "CS202"), "S001"))
    results.append(r); print_detail(r, 2)

    # TC-ECP03
    r = run_test(3, "TC-ECP03", "ECP — Invalid partition",
        "Empty string passed as course ID",
        {"student_id": "S001", "logged_in": True, "course_id": '""  (empty)'},
        "Invalid course ID",
        lambda: EnrollmentFormUI.build_request("S001", ""),
        expect_exception=True)
    results.append(r); print_detail(r, 3)

    # TC-ECP04
    r = run_test(4, "TC-ECP04", "ECP — Invalid partition",
        "Course ID contains special characters (C@#1)",
        {"student_id": "S001", "logged_in": True, "course_id": '"C@#1"'},
        "Invalid course ID",
        lambda: EnrollmentFormUI.build_request("S001", "C@#1"),
        expect_exception=True)
    results.append(r); print_detail(r, 4)

    # TC-ECP05
    ec = fresh_controller()
    r = run_test(5, "TC-ECP05", "ECP — Invalid partition",
        "Numeric-only course ID (no letter prefix) — valid format, not in system",
        {"student_id": "S001", "logged_in": True, "course_id": '"999"'},
        "Course not found",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "999"), "S001"),
        expect_exception=True)
    results.append(r); print_detail(r, 5)

    # TC-ECP06
    ec = fresh_controller()
    r = run_test(6, "TC-ECP06", "ECP — Invalid partition",
        "Valid alphanumeric format but course ID does not exist in system",
        {"student_id": "S001", "logged_in": True,
         "course_id": "C000", "exists_in_system": False},
        "Course not found",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C000"), "S001"),
        expect_exception=True)
    results.append(r); print_detail(r, 6)

    # ── PART B — ECP: Student Eligibility ───────────────────────────
    print("\n" + "━" * 72)
    print("  PART B  —  ECP: Student Eligibility Equivalence Classes")
    print("━" * 72)

    # TC-ECP07
    ec = fresh_controller()
    r = run_test(7, "TC-ECP07", "ECP — Valid partition",
        "Student exists, logged in, not yet enrolled — all preconditions met",
        {"student_id": "S001", "logged_in": True,
         "course_id": "C101", "already_enrolled": False},
        "SUCCESS",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001"))
    results.append(r); print_detail(r, 7)

    # TC-ECP08
    ec = fresh_controller()
    r = run_test(8, "TC-ECP08", "ECP — Invalid partition",
        "Student exists but is NOT logged in (precondition violated)",
        {"student_id": "S004", "logged_in": False, "course_id": "C101"},
        "Student must be logged in",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S004", "C101"), "S004"),
        expect_exception=True)
    results.append(r); print_detail(r, 8)

    # TC-ECP09
    ec = fresh_controller()
    r = run_test(9, "TC-ECP09", "ECP — Invalid partition",
        "Student ID not registered in the system at all (S999)",
        {"student_id": "S999", "registered": False, "course_id": "C101"},
        "Student not found",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S999", "C101"), "S999"),
        expect_exception=True)
    results.append(r); print_detail(r, 9)

    # TC-ECP10
    ec = fresh_controller()
    def tc_ecp10():
        ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001")
        return ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001")
    r = run_test(10, "TC-ECP10", "ECP — Invalid partition",
        "Student already enrolled in course — duplicate enrollment attempt",
        {"student_id": "S001", "logged_in": True,
         "course_id": "C101", "already_enrolled": True},
        "already enrolled",
        tc_ecp10, expect_exception=True)
    results.append(r); print_detail(r, 10)

    # ── PART C — BVA: Course ID length & Seat availability ──────────
    print("\n" + "━" * 72)
    print("  PART C  —  BVA: Course ID Length & Seat Availability")
    print("━" * 72)

    # TC-BVA01
    ec = fresh_controller()
    r = run_test(11, "TC-BVA01", "BVA — min (len=1)",
        "Course ID = 1 character (min length) — format valid, not found in system",
        {"student_id": "S001", "logged_in": True,
         "course_id": '"C"', "id_length": 1},
        "Course not found",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C"), "S001"),
        expect_exception=True)
    results.append(r); print_detail(r, 11)

    # TC-BVA02
    ec = fresh_controller()
    r = run_test(12, "TC-BVA02", "BVA — min+1 (len=2)",
        "Course ID = 2 characters (min+1) — exists in system, enrollment succeeds",
        {"student_id": "S001", "logged_in": True,
         "course_id": '"C1"', "id_length": 2, "seats": 10},
        "SUCCESS",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C1"), "S001"))
    results.append(r); print_detail(r, 12)

    # TC-BVA03
    ec = fresh_controller()
    ec.add_course(Course("COURSE1234", "Advanced Topics", available=True, seats_available=5))
    r = run_test(13, "TC-BVA03", "BVA — max (len=10)",
        "Course ID = 10 characters (max valid length) — exists, enrollment succeeds",
        {"student_id": "S001", "logged_in": True,
         "course_id": '"COURSE1234"', "id_length": 10, "seats": 5},
        "SUCCESS",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "COURSE1234"), "S001"))
    results.append(r); print_detail(r, 13)

    # TC-BVA04
    ec = fresh_controller()
    ec.add_course(Course("C105", "Last Seat Course", available=True, seats_available=1))
    def tc_bva04():
        result    = ec.enroll(EnrollmentFormUI.build_request("S001", "C105"), "S001")
        remaining = ec._courses["C105"].seats_available
        return f"{result} | seats_remaining_after={remaining}"
    r = run_test(14, "TC-BVA04", "BVA — seat boundary (1)",
        "Exactly 1 seat remaining — enrollment succeeds, seat count drops to 0",
        {"student_id": "S001", "logged_in": True,
         "course_id": "C105", "seats_available": 1},
        "SUCCESS",
        tc_bva04)
    results.append(r); print_detail(r, 14)

    # TC-BVA05
    ec = fresh_controller()
    r = run_test(15, "TC-BVA05", "BVA — seat boundary (0)",
        "0 seats available (below boundary) — alternate flow, enrollment blocked",
        {"student_id": "S001", "logged_in": True,
         "course_id": "C104", "seats_available": 0},
        "Course is unavailable",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C104"), "S001"))
    results.append(r); print_detail(r, 15)

    # ── FINAL SUMMARY TABLE ─────────────────────────────────────────
    print("\n\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                       FINAL SUMMARY TABLE                           ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    W_N   =  3
    W_LBL = 12
    W_TEC = 24
    W_SCN = 44
    W_EXP = 32
    W_RES =  6
    total_w = W_N + W_LBL + W_TEC + W_SCN + W_EXP + W_RES + 14
    sep = "─" * total_w

    header = (f"{'#':<{W_N}}  {'TC ID':<{W_LBL}}  {'Technique':<{W_TEC}}  "
              f"{'Scenario':<{W_SCN}}  {'Expected output':<{W_EXP}}  {'Result':<{W_RES}}")
    print(f"\n{header}")
    print(sep)

    pass_count = fail_count = 0
    part_labels = {
        1:  "PART A  —  ECP: Course ID",
        7:  "PART B  —  ECP: Student Eligibility",
        11: "PART C  —  BVA: Course ID Length & Seats",
    }

    for r in results:
        if r["id"] in part_labels:
            print(f"\n  {part_labels[r['id']]}")
            print(sep)

        status = "PASS" if r["passed"] else "FAIL"
        if r["passed"]: pass_count += 1
        else:           fail_count += 1

        scn = r["scenario"][:W_SCN]
        exp = r["expected"][:W_EXP]
        tec = r["technique"][:W_TEC]
        print(f"{r['id']:<{W_N}}  {r['label']:<{W_LBL}}  {tec:<{W_TEC}}  "
              f"{scn:<{W_SCN}}  {exp:<{W_EXP}}  {status:<{W_RES}}")

    print(sep)
    print(f"\n  Total : {len(results)}   |   PASS : {pass_count}   |   FAIL : {fail_count}")
    if fail_count == 0:
        print("\n  All 15 test cases PASSED.")
    else:
        print(f"\n  {fail_count} test case(s) FAILED — see detailed output above.")
    print()


if __name__ == "__main__":
    main()