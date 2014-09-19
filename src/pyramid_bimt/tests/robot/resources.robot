*** Settings ***

Library         HttpLibrary.HTTP
Library         OperatingSystem
Library         String
Library         pyramid_bimt.tests.robot.reload_db.ReloadDB
Documentation   A resource file containing the application specific keywords
...             that create our own domain specific language. This resource
...             implements keywords for testing HTML version of the test
...             application.


*** Keywords ***

Take screenshot and dump source
    Log Source
    Capture Page Screenshot

Suite Setup
    Init DB  ${APP_NAME}
    Reset 404 count
    Reset Javascript Exception count
    Open browser  ${APP_URL}  browser=${BROWSER}  remote_url=${REMOTE_URL}  desired_capabilities=${DESIRED_CAPABILITIES}
    Set window size   1024  768


    ${app_name}=  Get API result  app_name
    @{app_name}=  Split String  ${app_name}  "
    Set Suite Variable  ${APP_NAME}  @{app_name}[1]

    ${app_title}=  Get API result  app_title
    @{app_title}=  Split String  ${app_title}  "
    Set Suite Variable  ${APP_TITLE}  @{app_title}[1]

    ${app_domain}=  Get API result  app_domain
    @{app_domain}=  Split String  ${app_domain}  "
    Set Suite Variable  ${APP_DOMAIN}  @{app_domain}[1]

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

I Select From Dropdown
    [Arguments]  ${name}  ${value}
    # A bit hacky but only way so it works with chosen jquery plugin
    # as we can't select (now hidden) select options
    Click Element  xpath=//select[@name="${name}"]/../div
    Click Element  xpath=//select[@name="${name}"]/../div/div/ul[@class="chosen-results"]/li[text()="${value}"]

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

I go to
    [Arguments]  ${location}
    Go to  ${location}

I go to Login Form
    Go to  http://localhost:8080/login/

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
    Go to  http://localhost:8080/login/
    Input Text  name=email  one@bar.com
    Input Text  name=password  secret
    Click Button  Login
    I am logged in

I log in as a staff member
    Go to  http://localhost:8080/login/
    Input Text  name=email  staff@bar.com
    Input Text  name=password  secret
    Click Button  Login
    I am logged in

I log in as admin
    Go to  http://localhost:8080/login/
    Input Text  name=email  admin@bar.com
    Input Text  name=password  secret
    Click Button  Login
    I am logged in

I log out
    Click Element  id=usermenu
    Click Link  Logout
    Page Should Contain  You have been logged out.
    I am logged out

I am logged in as an admin
    I log in as admin

I am logged in as a staff member
    I log in as a staff member

I am logged in as a user
    I log in as a user

Last email should contain
    [Arguments]  ${value}
    Wait Until Created  ${MAIL_DIR}
    Wait Until Keyword Succeeds  10 sec  1 sec  Directory Should Not Be Empty  ${MAIL_DIR}
    @{mails}=       List Files In Directory  ${MAIL_DIR}
    ${mail_path}=   Join Path  ${MAIL_DIR}  @{mails}[-1]
    ${mail}=        Get File  ${mail_path}
    Should Contain  ${mail}  ${value}

Last email should contain encoded
    [Arguments]  ${value}
    ${value_encoded}=  Evaluate  quopri.encodestring("${value}", 1)  modules=quopri
    Last email should contain  ${value_encoded}

Last email subject should be
    [Arguments]  ${value}
    ${value_encoded}=  Evaluate  email.header.Header("${value}", 'utf-8').encode()  modules=email
    Last email should contain  Subject: ${value_encoded}

Last email recipient should be
    [Arguments]  ${value}
    Last email should contain  To: ${value}

Remove last email
    @{mails}=       List Files In Directory  ${MAIL_DIR}
    ${mail_path}=   Join Path  ${MAIL_DIR}  @{mails}[-1]
    Remove File  ${mail_path}

I add group
    [Arguments]  ${group}
    Click Element  xpath=//*[@id="deformField4-seqAdd"]
    Input Text  xpath=//*[@id="deformField4-orderable"]/div[last()]/div[1]/input[1]  ${group}

I remove group
    [Arguments]  ${group}
    Click Element  xpath=//*[@value="${group}"]/../../*/*[@title="Remove"]

I click disable user
    [Arguments]  ${email}
    Click Element  xpath=//*[.="${email}"]/../../td/a[contains(.,"Disable")]

I click enable user
    [Arguments]  ${email}
    Click Element  xpath=//*[.="${email}"]/../../td/a[contains(.,"Enable")]

User is striked-through and disabled
    [Arguments]  ${email}
    Page Should Contain Element  xpath=//*[.="${email}" and @style="text-decoration: line-through"]/../../td/a[contains(.,"Enable")]

User is enabled
    [Arguments]  ${email}
    Page Should Contain Element  xpath=//*[.="${email}"]/../../td/a[contains(.,"Disable")]

I click delete audit log entry
    [Arguments]  ${value}
    Click Element  xpath=//*[.="${value}"]/../td/a[contains(.,"Delete")]

I click delete first audit log entry of type
    [Arguments]  ${value}
    Click Element  xpath=//*[contains(.,"${value}")]/../td/a[contains(.,"Delete")]

I click sort by
    [Arguments]  ${value}
    Click Element  xpath=//*[.="${value}"]

I wait until table is loaded
    Wait Until Element Is Visible  DataTables_Table_0_wrapper
