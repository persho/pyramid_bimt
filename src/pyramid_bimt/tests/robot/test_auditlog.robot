*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: User views only its own Recent Activity
   Given password reset is requested by staff member
     And I use the login form to login
    When I go to  /activity/
     And I wait until table is loaded
    Then entries table should have rows  1
     and entries table should contain row  1  User Logged In one@bar.com

Scenario: Admin views all Recent Activity
   Given password reset is requested by staff member
     And I am logged in as an admin
    When I go to  /activity/
     And I wait until table is loaded
    Then entries table should have rows  1
     And entries table should contain row  1  User Changed Password staff@bar.com Delete

Scenario: Admin adds a new audit-log entry
   Given I am logged in as an admin
    When I go to  /audit-log/add/
     And I select from dropdown  user_id  one@bar.com
     And I select from dropdown  event_type_id  UserCreated
     And Input Text  name=comment  Fake create user.
     And I click button  Submit
     And I wait until table is loaded
    Then location should be  /activity/
     And entries table should have rows  1
     And entries table should contain row  1  User Created one@bar.com Fake create user. Delete

Scenario: Admin deletes an audit log entry
   Given I use the login form to login
     And I am logged in as an admin
    When I go to  /activity/
     And I wait until table is loaded
     And I click delete first audit log entry of type  User Logged In
     And I wait until table is loaded
    Then location should be  /activity/
     And entries table should have rows  1
     And entries table should contain row  1  No data available in table


*** Keywords ***

Password reset is requested by staff member
    I go to  /login/
    Input Text  name=email  staff@bar.com
    Click Button  reset_password

Entries table should contain row
    [Arguments]  ${row_number}  ${text}
    Table Row Should Contain  css=.table  ${row_number}  ${text}

Entries table should have rows
    [Arguments]  ${row_count}
    ${rows}=  Get Matching XPath Count  //table[contains(@class, 'table')]/tbody/tr
    Fail Unless Equal  ${rows}  ${row_count}

I use the login form to login
    I go to  /login/
    Input Text  name=email  one@bar.com
    Input Text  name=password  secret
    Click Button  Login
    I am logged in
