*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Add new portlet
    Given I log in as admin
     When I go to  /portlet/add/
      And I input text  name=name  downtime notice
      And I select checkbox admins
      And I Select From Dropdown  position  Above Footer
      And I input text  name=html  Site will be down this weekend!
      And I click button  Submit
     Then location should be  /portlet/2/edit/
      And page should contain  Portlet "downtime notice" added.

Scenario: Edit portlet
    Given I log in as admin
     When I go to  /portlet/1/edit/
      And I input text  name=name  maintenance notice
      And I click button  Save
     Then location should be  /portlet/1/edit/
      And page should contain  Portlet "maintenance notice" modified.


*** Keywords ***

I select checkbox admins
    Select Checkbox  css=input[value="1"]
