*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Add new Group
    Given I log in as admin
     When I go to  http://localhost:8080/group/add
      And I input text  name=name  monthly
      And I input text  name=product_id  1
      And I input text  name=validity  31
      And I input text  name=trial_validity  7
      And I select checkbox one@bar.com
      And I click button  Submit
     Then location should be  http://localhost:8080/group/6/edit
      And page should contain  Group "monthly" added.

Scenario: Edit group
    Given I log in as admin
     When I go to  http://localhost:8080/group/4/edit
      And I input text  name=name  yearly
      And I input text  name=validity  365
      And I click button  Save
     Then location should be  http://localhost:8080/group/4/edit
      And page should contain  Group "yearly" modified.


*** Keywords ***

I select checkbox one@bar.com
    Select Checkbox  css=input[value="2"]
