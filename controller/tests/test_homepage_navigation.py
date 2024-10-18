from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time # had to use for simulating real-user clicks some js stuff (like selector2) doesn't work well with selenium functions

from insider_py_wrapper.helpers import run_test
from insider_py_wrapper.generic_page import GenericPage, Actions

###############################
####### Driver Options ########
###############################

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--window-size=1200,943")

driver = webdriver.Chrome(
   options=chrome_options
)

window_size = driver.get_window_size()
print(f"Window Width: {window_size['width']}")
print(f"Window Height: {window_size['height']}")

## xpaths - will/can be moved to a YAML file later on for ease of maintainability
cookie_banner_xpath = '//*[@id="cookie-law-info-bar"]'
cookie_reject_all_xpath = '//*[@id="wt-cli-reject-btn"]'

navbar_company_xpath = '//*[@id="navbarNavDropdown"]/ul[1]/li[6]'
navbar_company_career_xpath = '//*[@id="navbarNavDropdown"]/ul[1]/li[6]/div/div[2]/a[2]'
burger_icon_xpath = '//*[@id="navigation"]/div[2]/a[2]'
burger_company_xpath = '//*[@id="navbarNavDropdown"]/ul[1]/li[6]'
location_section_xpath = '//*[@id="career-our-location"]'
see_all_teams_btn_xpath = '//*[@id="career-find-our-calling"]/div/div/a'

quality_assurance_header_xpath = '//*[@id="career-find-our-calling"]/div/div/div[2]/div[12]/div[2]'
see_all_qa_jobs_btn_xpath = '//*[@id="page-head"]/div/div/div[1]/div/div/a'

team_section_xpath = '//*[@id="career-find-our-calling"]'

filter_by_location_dropd_xpath = '//*[@id="select2-filter-by-location-container"]'
istanbul_option_xpath = '//li[contains(text(), "Istanbul, Turkey")]'
filter_by_department_dropd_xpath = '//*[@id="select2-filter-by-department-container"]'
qa_option_xpath = '//li[contains(text(), "Quality Assurance")]'

# life section doesn't have a section id, maybe intentional? so we can't do a relative xpath
# and absolute xpath is not very dependable
# but there's an aria-label="life-at-insider-X" on all the elements under that section (and no other)
# (only 11 instances of life-at-insider-X, all of them under life section)
life_section_css_selector = "[aria-label^='life-at-insider']"


# NOTE: Enforced test creations as functions, so we can mark a test as fail and continue
# executing other uncoupled tests
# All defined functions are ran via run_test from helpers.py
# assert makes it easy to show exactly which action failed. 

# NOTE: 
# GenericPage functions requires a small description as well, so QAs can exactly pinpoint the problembs via logs 
# e.g. assert homepage.perform_action_on_visible_element(3, By.XPATH, navbar_company_xpath, Actions.CLICK, "Company Menu")
# will write Clicked element: Company Menu, or Fail and logs: Error: Element Company Menu is not visible or interactable for action '{action}'


#################################
####### Init GenericPage ########
#################################

homepage = GenericPage(driver, "https://useinsider.com")

# Test Case: Home page loaded (Step 1)
def test_homepage_opened():
    assert homepage.is_page_loaded(10, By.XPATH, "//title[contains(text(), 'Insider')]"), "Home page failed to load"

# Test Case: Decline Cookies (to unblock elements on the page)
def test_decline_cookies():
    return homepage.decline_cookies(cookie_reject_all_xpath, 10)

# Test Case: Navigate to Careers and check if life/location/teams exists (Step 2)
def test_navigate_to_careers():
    success = homepage.perform_action_on_visible_element(3, By.XPATH, navbar_company_xpath, Actions.CLICK, "Company Menu")
    assert success, "Company menu not clickable"

    success = homepage.perform_action_on_visible_element(3, By.XPATH, navbar_company_career_xpath, Actions.CLICK, "Careers Link")
    assert success, "Careers link not clickable"

    location_section, visible = homepage.is_element_visible(5, By.XPATH, location_section_xpath, "Locations Section")
    assert visible, "Locations section not visible"

    elements = homepage.get_all_elements(By.CSS_SELECTOR, life_section_css_selector, "Life at Insider Elements")
    assert len(elements) > 0, "No element found for life_section"


# running Tests - run_test(<Descriotion for logging>, <Defined test function()>)
run_test("Test: home page loaded", test_homepage_opened)
run_test("Test cookie banner decline all", test_decline_cookies)
run_test("Test: navigate to careers", test_navigate_to_careers)
print("all jobs ran, results are printed out")
driver.quit() 