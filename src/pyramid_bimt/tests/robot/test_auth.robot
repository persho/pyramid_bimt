*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: User logs in
    When I log in as a user
    Then I am logged in

Scenario: User logs out
    When I log in as a user
     And I log out
    Then I am logged out

Scenario: User resets its password
    When I go to Login Form
     And I input text  name=email  one@bar.com
     And I click button  Reset password
    Then page should contain  A new password was sent to your email.
     And last email should contain  From: info@${APP_DOMAIN}
     And last email should contain  To: one@bar.com
     And last email should contain  Subject: ${APP_TITLE} Password Reset
     And last email should contain encoded  Hi One Bar
     And last email should contain encoded  your new password for ${APP_TITLE} is
     And last email should contain encoded  http://localhost:8080/login
