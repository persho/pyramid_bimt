*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Open the Sanity Check view
    Given I log in as admin
     When I go to  http://localhost:8080/sanity-check/
     Then page should contain  Everything in order, nothing to report.


*** Keywords ***

I select checkbox trial
    Select Checkbox  css=input[value="3"]
