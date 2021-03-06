*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Staff member adds a new user
    Given I am logged in as a staff member
     When I go to  /user/add/
      And I input text  name=email  user@xyz.Xyz
      And I input text  name=fullname  User Xyz
      And I select checkbox staff
      And I click button  Submit
     Then location should be  /user/4/
      And page should contain  User "user@xyz.Xyz" added.

Scenario: Staff member edits a user
    Given I am logged in as a staff member
     When I go to  /user/3/edit/
      And I input text  name=email  ovca@xyz.xyz
      And I input text  name=fullname  Ovca Xyz
      And I unselect checkbox staff
      And I click button  Save
     Then location should be  /user/3/
      And page should contain  User "ovca@xyz.xyz" modified.
      And page should contain  Ovca Xyz

Scenario: Staff member disables and re-enables user
    Given I am logged in as a staff member
     When I go to  /users/
      And I wait until table is loaded
      And I click disable user  one@bar.com
     Then user is striked-through and disabled  one@bar.com
      And Page should contain  User "one@bar.com" disabled.
     When I go to  /users/
      And I click enable user  one@bar.com
     Then user is enabled  one@bar.com
      And page should contain  User "one@bar.com" enabled.

Scenario: Staff member logs in as another user
   Given I am logged in as a staff member
    When I go to  /login-as/
     And I input text  name=email  one@bar.com
     And I click button  Login as user
    Then I am logged in
     And page should contain  You have successfully logged in as user "one@bar.com".

Scenario: User cannot log in as another user
   Given I am logged in as a user
    When I go to  /login-as/
    Then page should contain  page does not exist
    Reset 404 count

Scenario: User cannot add users
   Given I am logged in as a user
    When I Go to  /user/add/
    Then page should contain  page does not exist
    Reset 404 count

Scenario: User cannot view the list of users
   Given I am logged in as a user
    When I go to  /users/
    Then page should contain  page does not exist
    Reset 404 count

Scenario: User cannot view a single user
   Given I am logged in as a user
    When I go to  /user/1/
    Then page should contain  page does not exist
    Reset 404 count

Scenario: User cannot edit users
   Given I am logged in as a user
    When I Go to  /user/1/edit/
    Then page should contain  page does not exist
    Reset 404 count

*** Keywords ***

I select checkbox staff
    Select Checkbox  css=input[value="2"]

I unselect checkbox staff
    Unselect Checkbox  css=input[value="2"]

I unselect checkbox enabled
    Unselect Checkbox  css=input[value="3"]
