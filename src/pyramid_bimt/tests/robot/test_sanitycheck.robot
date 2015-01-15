*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Open the Sanity Check view
   Given I am logged in as a staff member
    When I go to  /sanity-check/
    Then page should contain  Everything in order, nothing to report.

Scenario: User cannot view the Sanity Check view
   Given I am logged in as a user
    When I go to  /sanity-check/
    Then page should contain  Sorry, but the page you were trying to view does not exist.
    Reset 404 count
