*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Add new user
    Given I log in as admin
     When I go to  http://localhost:8080/user/add
      And I input text  name=email  user@xyz.xyz
      And I input text  name=fullname  User Xyz
      And I select checkbox admins
      And I select checkbox enabled
      And I click button  Submit
     Then location should be  http://localhost:8080/user/3
      And page should contain  User "user@xyz.xyz" added.

Scenario: Edit user
    Given I log in as admin
     When I go to  http://localhost:8080/user/3/edit
      And I input text  name=email  ovca@xyz.xyz
      And I input text  name=fullname  Ovca Xyz
      And I unselect checkbox admins
      And I click button  Save
     Then location should be  http://localhost:8080/user/3
      And page should contain  User "ovca@xyz.xyz" modified.
      And page should contain  Ovca Xyz

Scenario: Disable user
    I log in as admin
    Go to  http://localhost:8080/users
    I click disable user  ovca@xyz.xyz
    User is strike through and disabled  ovca@xyz.xyz
    Page Should Contain  User "ovca@xyz.xyz" disabled.

Scenario: Enable user
    I log in as admin
    Go to  http://localhost:8080/users
    I click enable user  ovca@xyz.xyz
    User is enabled  ovca@xyz.xyz
    Page Should Contain  User "ovca@xyz.xyz" enabled.


*** Keywords ***

I select checkbox admins
    Select Checkbox  css=input[value="1"]

I select checkbox enabled
    Select Checkbox  css=input[value="2"]

I unselect checkbox admins
    Unselect Checkbox  css=input[value="1"]

I unselect checkbox enabled
    Unselect Checkbox  css=input[value="2"]
