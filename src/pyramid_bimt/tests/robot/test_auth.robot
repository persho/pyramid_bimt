*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: User logs in
    When I go to  /login/
     And I input text  name=email  one@bar.com
     And I input text  name=password  secret
     And I click button  Login
    Then I am logged in

Scenario: User logs out
   Given I am logged in as a user
    When I go to  /
     And I log out
    Then I am logged out

Scenario: User resets its password
    When I go to  /login/
     And I input text  name=email  one@bar.com
     And I click button  Reset password
    Then page should contain  A new password was sent to your email.
     And last email should contain  To: one@bar.com
     And last email should contain  Subject: BIMT Password Reset
     And last email should contain encoded  Login to the members' area: ${APP_URL}/login/

Scenario: User not logged in
    When I go to  /
     Then page should contain  Login
