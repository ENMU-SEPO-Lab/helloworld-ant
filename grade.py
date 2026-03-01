import os
import sys
import xml.etree.ElementTree as ET

# Directories and files
JUNIT_DIR = "reports/junit"
PMD_FILE = "reports/pmd.xml"
CHECKSTYLE_FILE = "reports/checkstyle.xml"

# Grading parameters
MAX_SCORE = 100
TEST_WEIGHT = 70
PMD_WEIGHT = 15
CHECKSTYLE_WEIGHT = 15
PMD_DEDUCTION_PER_VIOLATION = 2
CHECKSTYLE_DEDUCTION_PER_VIOLATION = 2
PASS_THRESHOLD = 70


def count_junit_failures():
    failures = 0
    tests = 0
    if not os.path.exists(JUNIT_DIR):
        return 0, 0
    for file in os.listdir(JUNIT_DIR):
        if file.endswith(".xml"):
            tree = ET.parse(os.path.join(JUNIT_DIR, file))
            root = tree.getroot()
            tests += int(root.attrib.get("tests", 0))
            failures += int(root.attrib.get("failures", 0))
            failures += int(root.attrib.get("errors", 0))
    return tests, failures


def count_pmd_violations():
    if not os.path.exists(PMD_FILE):
        return 0
    tree = ET.parse(PMD_FILE)
    root = tree.getroot()
    return len(root.findall(".//violation"))


def count_checkstyle_violations():
    if not os.path.exists(CHECKSTYLE_FILE):
        return 0
    tree = ET.parse(CHECKSTYLE_FILE)
    root = tree.getroot()
    return len(root.findall(".//file//error"))


def main():
    tests, failures = count_junit_failures()
    pmd_violations = count_pmd_violations()
    checkstyle_violations = count_checkstyle_violations()

    if tests == 0:
        print("No tests found. Setting test score to 0.")
    test_score = ((tests - failures) / tests) * TEST_WEIGHT if tests else 0

    pmd_penalty = pmd_violations * PMD_DEDUCTION_PER_VIOLATION
    pmd_score = max(PMD_WEIGHT - pmd_penalty, 0)

    checkstyle_penalty = checkstyle_violations * CHECKSTYLE_DEDUCTION_PER_VIOLATION
    checkstyle_score = max(CHECKSTYLE_WEIGHT - checkstyle_penalty, 0)

    final_score = test_score + pmd_score + checkstyle_score

    print("\n===== GRADING REPORT =====")
    print(f"Tests run: {tests}, Failures: {failures}")
    print(f"PMD violations: {pmd_violations}")
    print(f"Checkstyle violations: {checkstyle_violations}")
    print(f"Final Score: {final_score:.2f} / {MAX_SCORE}")
    print("Result: PASS" if final_score >= PASS_THRESHOLD else "Result: FAIL")

    # Optionally write feedback.md
    os.makedirs("reports", exist_ok=True)
    with open("reports/feedback.md", "w") as f:
        f.write("# Grading Feedback\n\n")
        f.write(f"- Tests run: {tests}\n")
        f.write(f"- Failures: {failures}\n")
        f.write(f"- PMD violations: {pmd_violations}\n")
        f.write(f"- Checkstyle violations: {checkstyle_violations}\n")
        f.write(f"- Final Score: {final_score:.2f} / {MAX_SCORE}\n")
        f.write(f"- Result: {'PASS' if final_score >= PASS_THRESHOLD else 'FAIL'}\n")

    if final_score < PASS_THRESHOLD:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()