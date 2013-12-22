*** Settings ***

Library         HttpLibrary.HTTP
Library         OperatingSystem
Documentation   A resource file containing the application specific keywords
...             that create our own domain specific language. This resource
...             implements keywords for testing HTML version of the test
...             application.


*** Keywords ***

Take screenshot and dump source
    Log Source
    Capture Page Screenshot

Suite Setup
    Reset 404 count
    Reset Javascript Exception count
    Open browser  ${APP_URL}  browser=${BROWSER}  remote_url=${REMOTE_URL}  desired_capabilities=${DESIRED_CAPABILITIES}
    Set window size   1024  768
    Register Keyword To Run On Failure  Take screenshot and dump source

Suite Teardown
    Close All Browsers

Sanity check
    There were no 404s
    There were no Javascript exceptions

Call API method  [Arguments]  ${method_name}
    ${body}=  Get API result  ${method_name}
    Json Value Should Equal  ${body}  /result  "ok"

Get API result  [Arguments]  ${method_name}
    Create HTTP Context  ${APP_ADDR}
    POST  /robot/${method_name}
    ${body}=  Get Response Body
    [Return]  ${body}

Assert no errors  [Arguments]  ${method_name}
    ${body}=  Get API result  ${method_name}
    Json Value Should Equal  ${body}  /errors  []

Reset 404 count
    Call API method  reset_notfound

There were no 404s
    Assert no errors  list_notfound

Reset Javascript Exception count
    Call API method  reset_js_exceptions

There were no Javascript exceptions
    Assert no errors  list_js_exceptions

I Select radio button
    [Arguments]  ${selector}  ${value}
    Select Radio Button  ${selector}  ${value}

I Select checkbox
    [Arguments]  ${value}
    Select Checkbox  css=input[value="${value}"]

I Unselect checkbox
    [Arguments]  ${value}
    Unselect Checkbox  css=input[value="${value}"]

Checkbox is not selected
    [Arguments]  ${value}
    Checkbox Should Not Be Selected  css=input[value="${value}"]

Checkbox is selected
    [Arguments]  ${value}
    Checkbox Should Be Selected  css=input[value="${value}"]

I go to Login Form
    Go to  http://localhost:8080/login

I click link
    [Arguments]  ${link}
    Click Link  ${link}

I click button
    [Arguments]  ${button}
    Click Button  ${button}

I input text
    [Arguments]  ${selector}  ${text}
    Input Text  ${selector}  ${text}

I choose file
    [Arguments]  ${selector}  ${filename}
    Choose file  ${selector}  ${filename}

I am logged in
    Page Should Contain  Logout

I am logged out
    Page Should Contain  Login

I log in as a user
    Go to  http://localhost:8080/login
    Input Text  name=email  one@bar.com
    Input Text  name=password  secret
    Click Button  Login
    Page Should Contain  Login successful.
    I am logged in

I log in as admin
    Go to  http://localhost:8080/login
    Input Text  name=email  admin@bar.com
    Input Text  name=password  secret
    Click Button  Login
    Page Should Contain  Login successful.
    I am logged in

I log out
    Click Element  id=usermenu
    Click Link  Logout
    Page Should Contain  You have been logged out.
    I am logged out

Last email should contain
    [Arguments]  ${value}
    ${value_encoded}=  Evaluate  quopri.encodestring('${value}', 1)  modules=quopri
    Wait Until Created  ${MAIL_DIR}
    @{mails}=       List Files In Directory  ${MAIL_DIR}
    ${mail_path}=   Join Path  ${MAIL_DIR}  @{mails}[-1]
    ${mail}=        Get File  ${mail_path}
    Should Contain  ${mail}  ${value_encoded}
