*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

Scenario: Staff member adds a new group
    Given I am logged in as a staff member
     When I go to  /group/add/
      And I input text  name=name  monthly
      And I input text  name=product_id  1
      And I input text  name=validity  31
      And I input text  name=trial_validity  7
      And I select checkbox one@bar.com
      And I click button  Submit
     Then location should be  /group/7/edit/
      And page should contain  Group "monthly" added.

Scenario: Staff member renames a group
    Given I am logged in as a staff member
     When I go to  /group/3/edit/
      And I input text  name=name  yearly
      And I click button  Save
     Then location should be  /group/3/edit/
      And page should contain  Group "yearly" modified.

Scenario: Staff member edits a group
    Given I am logged in as a staff member
     When I go to  /group/3/edit/
      And I input text  name=validity  365
      And I click button  Save
     Then location should be  /group/3/edit/
      And page should contain  Group "enabled" modified.

Scenario: User cannot add groups
   Given I am logged in as a user
    When I Go to  /group/add/
    Then page should contain  Insufficient privileges.

Scenario: User cannot view the list of groups
   Given I am logged in as a user
    When I go to  /groups/
    Then page should contain  Insufficient privileges.

Scenario: User cannot edit groups
   Given I am logged in as a user
    When I Go to  /group/1/edit/
    Then page should contain  Insufficient privileges.

Scenario: Staff member cannot edit admin group
   Given I am logged in as a staff member
    When I Go to  /group/1/edit/
    Then page should contain  Insufficient privileges.

Scenario: Admin can edit admin group
   Given I am logged in as an admin
    When I Go to  /group/1/edit/
    Then page should contain  Edit Group

*** Keywords ***

I select checkbox one@bar.com
    Select Checkbox  css=input[value="2"]
