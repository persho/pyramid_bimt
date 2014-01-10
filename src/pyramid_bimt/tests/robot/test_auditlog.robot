*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Add audit log entry
    I log in as admin
    Go to  http://localhost:8080/audit-log/add
    Select From List By Label  name=user_id  one@bar.com
    Select From List By Label  name=event_type_id  UserCreated
    Input Text  name=comment  Fake create user.
    I click button  Submit
    Location Should Be  http://localhost:8080/audit-log
    Page Should Contain  Audit log entry added.

Scenario: Delete audit log entry
    I log in as admin
    Go to  http://localhost:8080/audit-log
    I click sort by  Timestamp
    I click delete audit log entry  Fake create user.
    Location Should Be  http://localhost:8080/audit-log
    Page Should Contain  Audit log entry deleted.
