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
     And I am logged in as a user
    When I go to  http://localhost:8080/activity
     And I wait until table is loaded
    Then entries table should have rows  1
     and entries table should contain row  1  User Logged In one@bar.com

Scenario: Admin views all Recent Activity
   Given password reset is requested by staff member
     And I am logged in as an admin
    When I go to  http://localhost:8080/activity
     And I wait until table is loaded
    Then entries table should have rows  2
    Then entries table should contain row  1  User Logged In admin@bar.com
     And entries table should contain row  2  User Changed Password staff@bar.com Delete

Scenario: Admin adds a new audit-log entry
   Given I am logged in as an admin
    When I go to  http://localhost:8080/audit-log/add
     And I select from dropdown  user_id  one@bar.com
     And I select from dropdown  event_type_id  UserCreated
     And Input Text  name=comment  Fake create user.
     And I click button  Submit
     And I wait until table is loaded
    Then location should be  http://localhost:8080/activity
     And entries table should have rows  2
     And entries table should contain row  1  User Created one@bar.com Fake create user. Delete
     And entries table should contain row  2  User Logged In admin@bar.com

Scenario: Admin deletes an audit log entry
   Given I am logged in as an admin
    When I go to  http://localhost:8080/activity
     And I wait until table is loaded
     And I click delete first audit log entry of type  User Logged In
     And I wait until table is loaded
    Then location should be  http://localhost:8080/activity
     And entries table should have rows  1
     And entries table should contain row  1  No data available in table


*** Keywords ***

Password reset is requested by staff member
    Go To  http://localhost:8080/login
    Input Text  name=email  staff@bar.com
    Click Button  reset_password

Entries table should contain row
    [Arguments]  ${row_number}  ${text}
    Table Row Should Contain  css=.table  ${row_number}  ${text}

Entries table should have rows
    [Arguments]  ${row_count}
    ${rows}=  Get Matching XPath Count  //table[contains(@class, 'table')]/tbody/tr
    Fail Unless Equal  ${rows}  ${row_count}
