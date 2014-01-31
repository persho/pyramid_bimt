*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Add new mailing
    Given I log in as admin
     When I go to  http://localhost:8080/mailing/add
      And I input text  name=name  welcome email
      And I select checkbox trial
      And I select from dropdown  name=trigger  x days after created
      And I input text  name=days  1
      And I input text  name=subject  Welcome!
      And I input text  name=body  Welcome to BIMT!
      And I click button  Submit
     Then location should be  http://localhost:8080/mailing/1/edit
      And page should contain  Mailing "welcome email" added.

Scenario: Edit mailing
    Given I log in as admin
     When I go to  http://localhost:8080/mailing/1/edit
      And I input text  name=name  introduction email
      And I input text  name=subject  Let's introduce ourselves!
      And I click button  Save
     Then location should be  http://localhost:8080/mailing/1/edit
      And page should contain  Mailing "introduction email" modified.

Scenario: Test mailing
    Given I log in as admin
     When I go to  http://localhost:8080/mailing/1/edit
      And I click button  Test
     Then location should be  http://localhost:8080/mailing/1/edit
      And page should contain  Mailing "introduction email" sent to "admin@bar.com".
      And last email should contain  To: admin@bar.com
      And last email should contain  Subject: [Mailing Test] Let's introduce ourselves!
      And last email should contain encoded  Hello Admin,
      And last email should contain encoded  This mailing would be sent to:
      And last email should contain encoded  one@bar.com
      And last email should contain encoded  Best wishes,
      And last email should contain encoded  ${APP_TITLE} Team

Scenario: Send mailing immediately
    Given I log in as admin
     When I go to  http://localhost:8080/mailing/1/edit
      And I click button  Send immediately
     Then page should contain  Immediately send mailing "introduction email" to all 1 recipients without date constraints?
      And when I click button  OK
     Then location should be  http://localhost:8080/mailing/1/edit
      And page should contain  Mailing "introduction email" sent to 1 recipients.
      And last email should contain  To: one@bar.com
      And last email should contain  Subject: Let's introduce ourselves!
      And last email should contain encoded  Hello One Bar,
      And last email should contain encoded  Welcome to BIMT!
      And last email should contain encoded  Best wishes,
      And last email should contain encoded  ${APP_TITLE} Team


*** Keywords ***

I select checkbox trial
    Select Checkbox  css=input[value="3"]
