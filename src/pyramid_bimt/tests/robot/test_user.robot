*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Add new user
    I log in as admin
    Go to  http://localhost:8080/user/add
    Input Text  name=email  user@xyz.xyz
    Input Text  name=fullname  User Xyz
    I add group  enabled
    I add group  admins
    I click button  Save
    Location Should Be  http://localhost:8080/user/3
    Page Should Contain  User user@xyz.xyz has been added.

Scenario: Edit user
    I log in as admin
    Go to  http://localhost:8080/user/3/edit
    Input Text  name=email  ovca@xyz.xyz
    Input Text  name=fullname  Ovca Xyz
    I remove group  admins
    I click button  Save
    Location Should Be  http://localhost:8080/user/3
    Page Should Contain  User ovca@xyz.xyz has been modified.
    Page Should Contain  Ovca Xyz

Scenario: Disable user
    I log in as admin
    Go to  http://localhost:8080/users
    I click disable user  ovca@xyz.xyz
    User is strike through and disabled  ovca@xyz.xyz
    Page Should Contain  User ovca@xyz.xyz disabled.

Scenario: Enable user
    I log in as admin
    Go to  http://localhost:8080/users
    I click enable user  ovca@xyz.xyz
    User is enabled  ovca@xyz.xyz
    Page Should Contain  User ovca@xyz.xyz enabled.
