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
     When I go to  http://localhost:8080/user/add/
      And I input text  name=email  user@xyz.Xyz
      And I input text  name=fullname  User Xyz
      And I select checkbox staff
      And I select checkbox enabled
      And I click button  Submit
     Then location should be  http://localhost:8080/user/4/
      And page should contain  User "user@xyz.Xyz" added.

Scenario: Staff member edits a user
    Given I am logged in as a staff member
     When I go to  http://localhost:8080/user/3/edit/
      And I input text  name=email  ovca@xyz.xyz
      And I input text  name=fullname  Ovca Xyz
      And I unselect checkbox staff
      And I click button  Save
     Then location should be  http://localhost:8080/user/3/
      And page should contain  User "ovca@xyz.xyz" modified.
      And page should contain  Ovca Xyz

Scenario: Staff member disables and re-enables user
    Given I am logged in as a staff member
     When I go to  http://localhost:8080/users/
      And I click disable user  one@bar.com
     Then user is striked-through and disabled  one@bar.com
      And Page should contain  User "one@bar.com" disabled.
     When I go to  http://localhost:8080/users/
      And I click enable user  one@bar.com
     Then user is enabled  one@bar.com
      And page should contain  User "one@bar.com" enabled.

Scenario: Staff member logs in as another user
   Given I am logged in as a staff member
    When I go to  http://localhost:8080/login-as/
     And I input text  name=email  one@bar.com
     And I click button  Login as user
    Then I am logged in
     And page should contain  You have successfully logged in as user: one@bar.com

Scenario: User cannot add users
   Given I am logged in as a user
    When I Go to  http://localhost:8080/user/add/
    Then page should contain  Insufficient privileges.

Scenario: User cannot view the list of users
   Given I am logged in as a user
    When I go to  http://localhost:8080/users/
    Then page should contain  Insufficient privileges.

Scenario: User cannot view a single user
   Given I am logged in as a user
    When I go to  http://localhost:8080/user/1/
    Then page should contain  Insufficient privileges.

Scenario: User cannot edit users
   Given I am logged in as a user
    When I Go to  http://localhost:8080/user/1/edit/
    Then page should contain  Insufficient privileges.

*** Keywords ***

I select checkbox staff
    Select Checkbox  css=input[value="2"]

I select checkbox enabled
    Select Checkbox  css=input[value="3"]

I unselect checkbox staff
    Unselect Checkbox  css=input[value="2"]

I unselect checkbox enabled
    Unselect Checkbox  css=input[value="3"]
