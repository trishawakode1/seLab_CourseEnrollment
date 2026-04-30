# ============================================================
# UC-01: Enroll in Course
# E-Learning Portal — Software Engineering Assignment
# Consistent with Use Case Spec, Sequence Diagram & ECB Objects
# ============================================================

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ============================================================
# ENTITY OBJECTS  (ECB — Entity layer)
# ============================================================

@dataclass
class Course:
    course_id: str
    name: str
    available: bool
    seats_available: int


@dataclass
class Student:
    student_id: str
    name: str
    logged_in: bool
    enrolled_course_ids: List[str] = field(default_factory=list)


@dataclass
class Enrollment:
    enrollment_id: str
    student_id: str
    course_id: str
    has_access: bool = True   # postcondition: access to notes & lectures


# ============================================================
# BOUNDARY OBJECT  (ECB — Enrollment Form UI)
# Validates raw input before handing off to the controller
# ============================================================

@dataclass
class EnrollmentRequest:
    student_id: str
    course_id: str


class EnrollmentFormUI:
    """Boundary object — validates input and builds an EnrollmentRequest."""

    _VALID_ID = re.compile(r'^[A-Za-z0-9]+$')

    @classmethod
    def build_request(cls, student_id: str, course_id: str) -> EnrollmentRequest:
        if not student_id:
            raise ValueError("Invalid student ID")
        if not course_id:
            raise ValueError("Invalid course ID")
        if not cls._VALID_ID.match(student_id):
            raise ValueError("Invalid student ID")
        if not cls._VALID_ID.match(course_id):
            raise ValueError("Invalid course ID")
        return EnrollmentRequest(student_id=student_id, course_id=course_id)


# ============================================================
# CONTROL OBJECT  (ECB — Enrollment Controller)
# Orchestrates the sequence diagram flow:
#   Student -> FormUI -> Controller -> Course (checkAvailability)
#                                   -> Enrollment (createEnrollment)
# ============================================================

class EnrollmentController:
    """
    Control object — mirrors the sequence diagram:

      Student        FormUI         Controller      Course / Enrollment
        |--selectCourse->|               |                |
        |                |--requestCourse(C_ID)-->|       |
        |                |               |--checkAvail--->|
        |                |               |<--(result)-----|
        |                |<--successSig--|                |
        |<-displayMsg----|               |--createEnroll->|
    """

    def __init__(self):
        self._students:    Dict[str, Student]    = {}
        self._courses:     Dict[str, Course]     = {}
        self._enrollments: List[Enrollment]      = []
        self._next_enroll_id: int                = 1

    # ── seed helpers ──────────────────────────────────────────
    def add_student(self, student: Student) -> None:
        self._students[student.student_id] = student

    def add_course(self, course: Course) -> None:
        self._courses[course.course_id] = course

    # ── postcondition helpers (used by tests) ─────────────────
    def get_enrolled_courses(self, student_id: str) -> List[str]:
        student = self._students.get(student_id)
        return list(student.enrolled_course_ids) if student else []

    def has_access(self, student_id: str, course_id: str) -> bool:
        for e in self._enrollments:
            if e.student_id == student_id and e.course_id == course_id:
                return e.has_access
        return False

    # ── sequence diagram step: checkAvailability(C_ID) ────────
    def _check_availability(self, course: Course) -> bool:
        return course.available and course.seats_available > 0

    # ── sequence diagram step: createEnrollment ───────────────
    def _create_enrollment(self, student_id: str, course_id: str) -> Enrollment:
        eid = f"E{self._next_enroll_id}"
        self._next_enroll_id += 1
        enrollment = Enrollment(enrollment_id=eid,
                                student_id=student_id,
                                course_id=course_id)
        self._enrollments.append(enrollment)
        # Postcondition 1: student's dashboard updated
        self._students[student_id].enrolled_course_ids.append(course_id)
        return enrollment

    # ── main enroll flow ──────────────────────────────────────
    def enroll(self, request: EnrollmentRequest, acting_student_id: str) -> str:
        # Validate acting student exists first
        if acting_student_id not in self._students:
            raise LookupError("Student not found")

        # Precondition: student must be logged in
        if not self._students[acting_student_id].logged_in:
            raise PermissionError("Student must be logged in")

        # Validate target student exists
        if request.student_id not in self._students:
            raise LookupError("Student not found")

        # Validate course exists
        if request.course_id not in self._courses:
            raise LookupError("Course not found")

        course = self._courses[request.course_id]

        # Alternate flow: checkAvailability(C_ID)
        if not self._check_availability(course):
            return "ERROR: Course is unavailable — redirecting to browse page"

        # Check for duplicate enrollment
        for e in self._enrollments:
            if e.student_id == request.student_id and e.course_id == request.course_id:
                raise ValueError("Student already enrolled in this course")

        # createEnrollment (final step in sequence diagram)
        course.seats_available -= 1
        enrollment = self._create_enrollment(request.student_id, request.course_id)

        student_name = self._students[request.student_id].name
        # Postcondition: success signal -> display successful enrollment message
        return (f"SUCCESS: Enrollment successful [ID={enrollment.enrollment_id}]"
                f" — {student_name} enrolled in {course.name}")


# ============================================================
# TEST HARNESS
# ============================================================

def fresh_controller() -> EnrollmentController:
    """Returns a new controller seeded with standard test data."""
    ec = EnrollmentController()
    ec.add_student(Student("S001", "Trisha Wakode",   logged_in=True))
    ec.add_student(Student("S002", "Rahul Mehta",     logged_in=True))
    ec.add_student(Student("1001", "Numeric Student", logged_in=True))
    # S999 deliberately absent — non-existent student test

    ec.add_course(Course("C101", "Software Engineering", available=True,  seats_available=30))
    ec.add_course(Course("C102", "Data Structures",      available=True,  seats_available=25))
    ec.add_course(Course("C103", "Operating Systems",    available=True,  seats_available=20))
    ec.add_course(Course("C999", "Unavailable Course",   available=False, seats_available=0))
    # C000 deliberately absent — non-existent course test
    return ec


def run_test(tc_id: int, scenario: str, input_desc: str, expected: str,
             action, expect_exception: bool = False) -> dict:
    actual = ""
    passed = False
    try:
        actual = action()
        if not expect_exception:
            passed = expected in actual
        else:
            actual = f"No exception thrown (got: {actual})"
            passed = False
    except Exception as ex:
        actual = f"EXCEPTION: {ex}"
        if expect_exception:
            passed = expected in str(ex)

    return {
        "id":       tc_id,
        "scenario": scenario,
        "input":    input_desc,
        "expected": expected,
        "actual":   actual,
        "passed":   passed,
    }


# ============================================================
# TEST CASES
# ============================================================

def main():
    print("=================================================")
    print("  UC-01: Enroll in Course — Black Box Test Suite ")
    print("=================================================\n")

    results = []

    # TC01 — Normal flow: valid student, available course
    ec = fresh_controller()
    results.append(run_test(
        1, "Normal flow — valid student, available course",
        "studentID=S001, logged_in=True, courseID=C101, available=True",
        "SUCCESS",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001")
    ))

    # TC02 — Precondition: student not logged in
    ec = fresh_controller()
    ec.add_student(Student("S004", "Logged Out User", logged_in=False))
    results.append(run_test(
        2, "Precondition — student not logged in",
        "studentID=S004, logged_in=False, courseID=C101",
        "Student must be logged in",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S004", "C101"), "S004"),
        expect_exception=True
    ))

    # TC03 — Alternate flow: course unavailable
    ec = fresh_controller()
    results.append(run_test(
        3, "Alternate flow — course unavailable",
        "studentID=S001, logged_in=True, courseID=C999, available=False",
        "Course is unavailable",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C999"), "S001")
    ))

    # TC04 — Duplicate enrollment
    ec = fresh_controller()
    def tc04():
        ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001")
        return ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001")
    results.append(run_test(
        4, "Duplicate enrollment — same course",
        "studentID=S001, logged_in=True, courseID=C101, already_enrolled=True",
        "already enrolled",
        tc04, expect_exception=True
    ))

    # TC05 — Empty student ID
    ec = fresh_controller()
    results.append(run_test(
        5, "Boundary — empty student ID",
        'studentID="", logged_in=True, courseID=C101',
        "Invalid student ID",
        lambda: EnrollmentFormUI.build_request("", "C101"),
        expect_exception=True
    ))

    # TC06 — Empty course ID
    ec = fresh_controller()
    results.append(run_test(
        6, "Boundary — empty course ID",
        'studentID=S001, logged_in=True, courseID=""',
        "Invalid course ID",
        lambda: EnrollmentFormUI.build_request("S001", ""),
        expect_exception=True
    ))

    # TC07 — Non-existent course ID
    ec = fresh_controller()
    results.append(run_test(
        7, "Boundary — non-existent course ID",
        "studentID=S001, logged_in=True, courseID=C000",
        "Course not found",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C000"), "S001"),
        expect_exception=True
    ))

    # TC08 — Non-existent student
    ec = fresh_controller()
    results.append(run_test(
        8, "Boundary — non-existent student",
        "studentID=S999, logged_in=True, courseID=C101",
        "Student not found",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S999", "C101"), "S999"),
        expect_exception=True
    ))

    # TC09 — Multiple valid enrollments (different courses)
    ec = fresh_controller()
    def tc09():
        ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001")
        return ec.enroll(EnrollmentFormUI.build_request("S001", "C102"), "S001")
    results.append(run_test(
        9, "Equivalence — student enrolls in two different courses",
        "studentID=S001, courseID=C102 (second course, available)",
        "SUCCESS",
        tc09
    ))

    # TC10 — Postcondition: course appears in dashboard
    ec = fresh_controller()
    def tc10():
        ec.enroll(EnrollmentFormUI.build_request("S001", "C103"), "S001")
        return "DASHBOARD_OK" if "C103" in ec.get_enrolled_courses("S001") \
               else "DASHBOARD_FAIL"
    results.append(run_test(
        10, "Postcondition — course in enrolled list after enrollment",
        "After enrolling S001 in C103, get_enrolled_courses(S001) includes C103",
        "DASHBOARD_OK",
        tc10
    ))

    # TC11 — Postcondition: access to notes & lectures
    ec = fresh_controller()
    def tc11():
        ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001")
        return "ACCESS_OK" if ec.has_access("S001", "C101") else "ACCESS_FAIL"
    results.append(run_test(
        11, "Postcondition — student has access to course content",
        "has_access(S001, C101) == True after enrollment",
        "ACCESS_OK",
        tc11
    ))

    # TC12 — Special characters in student ID
    ec = fresh_controller()
    results.append(run_test(
        12, "Equivalence invalid — special chars in student ID",
        'studentID="S@#!", logged_in=True, courseID=C101',
        "Invalid student ID",
        lambda: EnrollmentFormUI.build_request("S@#!", "C101"),
        expect_exception=True
    ))

    # TC13 — Numeric-only student ID
    ec = fresh_controller()
    results.append(run_test(
        13, "Boundary — numeric student ID accepted",
        "studentID=1001, logged_in=True, courseID=C101, available=True",
        "SUCCESS",
        lambda: ec.enroll(EnrollmentFormUI.build_request("1001", "C101"), "1001")
    ))

    # TC14 — Course at max capacity (seats = 0)
    ec = fresh_controller()
    ec.add_course(Course("C104", "Full Course", available=True, seats_available=0))
    results.append(run_test(
        14, "Availability — course at max capacity",
        "studentID=S001, logged_in=True, courseID=C104, seats=0",
        "Course is unavailable",
        lambda: ec.enroll(EnrollmentFormUI.build_request("S001", "C104"), "S001")
    ))

    # TC15 — Two different students enroll in same course
    ec = fresh_controller()
    def tc15():
        r1 = ec.enroll(EnrollmentFormUI.build_request("S001", "C101"), "S001")
        r2 = ec.enroll(EnrollmentFormUI.build_request("S002", "C101"), "S002")
        if "SUCCESS" in r1 and "SUCCESS" in r2:
            return "SUCCESS — two separate enrollment records created"
        return "FAIL"
    results.append(run_test(
        15, "Multiple students enroll in same course independently",
        "S001 and S002 both enroll in C101 (both logged in, course available)",
        "SUCCESS",
        tc15
    ))

    # ── Print results table ────────────────────────────────────
    W_TC  = 4
    W_SCN = 50
    W_ACT = 32
    W_RES = 6
    sep = "-" * (W_TC + W_SCN + W_ACT + W_RES + 6)

    print(f"{'TC':<{W_TC}}  {'Scenario':<{W_SCN}}  "
          f"{'Actual output (truncated)':<{W_ACT}}  {'Result':<{W_RES}}")
    print(sep)

    pass_count = fail_count = 0
    for r in results:
        label  = f"T{r['id']}"
        scn    = r["scenario"][:W_SCN]
        act    = r["actual"]
        act    = (act[:W_ACT - 3] + "...") if len(act) > W_ACT else act
        result = "PASS" if r["passed"] else "FAIL"
        if r["passed"]:
            pass_count += 1
        else:
            fail_count += 1
        print(f"{label:<{W_TC}}  {scn:<{W_SCN}}  {act:<{W_ACT}}  {result:<{W_RES}}")

    print(sep)
    print(f"Total: {len(results)}  |  Pass: {pass_count}  |  Fail: {fail_count}\n")

    if fail_count == 0:
        print("All 15 test cases PASSED.")
    else:
        print(f"{fail_count} test case(s) FAILED. Review above.")


if __name__ == "__main__":
    main()

print("Test cases completed")