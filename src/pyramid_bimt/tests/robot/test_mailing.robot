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
      And I select from dropdown  trigger  x days after created
      And I input text  name=days  1
      And I input text  name=subject  Welcome!
      And I input text  name=body  Welcome to BIMT!
      And I click button  Submit
     Then location should be  http://localhost:8080/mailing/5/edit
      And page should contain  Mailing "welcome email" added.

Scenario: Edit mailing
    Given I log in as admin
     When I go to  http://localhost:8080/mailing/4/edit
      And I input text  name=name  introduction email
      And I input text  name=subject  Let's introduce ourselves!
      And I click button  Save
     Then location should be  http://localhost:8080/mailing/4/edit
      And page should contain  Mailing "introduction email" modified.

Scenario: Test mailing
    Given I log in as admin
     When I go to  http://localhost:8080/mailing/4/edit
      And I click button  Test
     Then location should be  http://localhost:8080/mailing/4/edit
      And page should contain  Mailing "welcome_email" sent to "admin@bar.com".
      And last email should contain  To: admin@bar.com
      And last email subject should be  [Mailing Test] Über Welcome!
      And last email should contain encoded  This mailing would be sent to:
      And last email should contain encoded  one@bar.com
      And last email should contain encoded  Best wishes,
      And last email should contain encoded  ${APP_TITLE} Team

Scenario: Send mailing immediately
    Given I log in as admin
     When I go to  http://localhost:8080/mailing/4/edit
      And I click button  Send immediately
     Then page should contain  Immediately send mailing "welcome_email" to all 1 recipients without date constraints?
     Wait Until Element Is Visible  xpath=//button[.='OK']  timeout=3
      And when I click button  OK
     Then location should be  http://localhost:8080/mailing/4/edit
      And page should contain  Mailing "welcome_email" sent to 1 recipients.
      And last email recipient should be  one@bar.com
      And last email subject should be  Über Welcome!
      And last email should contain encoded  Welcome to this
      And last email should contain encoded  Best wishes,
      And last email should contain encoded  ${APP_TITLE} Team


*** Keywords ***

I select checkbox trial
    Select Checkbox  css=input[value="3"]
