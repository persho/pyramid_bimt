*** Settings ***

Variables  pyramid_bimt/tests/robot/variables.py
Library    Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}
Library    DebugLibrary
Resource   pyramid_bimt/tests/robot/resources.robot

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown


*** Test Cases ***

404s are logged
    Reset 404 count
    ${body}=  Get API result  list_notfound
    Json Value Should Equal  ${body}  /result  "ok"
    Selenium2Library.Go To  http://localhost:8080/doesnotexist/
    ${body}=  Get API result  list_notfound
    Json Value Should Equal  ${body}  /result  "error"
    Json Value Should Equal  ${body}  /errors/0/url  "http://${APP_ADDR}/doesnotexist/"

Javascript errors are logged
    I log in as admin
    Reset Javascript Exception count
    ${body}=  Get API result  list_js_exceptions
    Json Value Should Equal  ${body}  /result  "ok"
    Selenium2Library.Go To  http://localhost:8080/raise-error/js
    ${body}=  Get API result  list_js_exceptions
    Json Value Should Equal  ${body}  /result  "error"
