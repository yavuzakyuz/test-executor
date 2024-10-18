from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from enum import Enum


## Actions.CLICK or Actions.HOVER to do actions, passed as ref to this class methods. 
Actions = Enum('Actions', ['CLICK', 'HOVER'])

# class init (think url is a good idea here)
class GenericPage: 
    def __init__(self, driver, url):
        self.driver = driver
        self.url = url
        self.driver.get(url)


##### Below I define wrapper functions for selenium expected_conditions function 
##### Thus, we can manage element/fetch reference easier and do generic error handling
##### also eaiser to maintain log outputs

#### Functions below take By methods and locator value (xpath, css class, css selector)

    # page load checker / presence of an important element should be a good indicator
    def is_page_loaded(self, timeout, by_method, locator_value):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                expected_conditions.presence_of_element_located((by_method, locator_value))
            )
            return element is not None
        except TimeoutException:
            print(f"Error: Timeout. Page did not load within {timeout} seconds")
            return False
        except Exception as e:
            print(f"Error: {str(e)}")
            return False   
    
    # generic decline cookie function... because banner blocked some elements
    def decline_cookies(self, cookie_reject_all_xpath, timeout):
        try:
            cookie_reject_btn = WebDriverWait(self.driver, timeout).until(
                expected_conditions.element_to_be_clickable((By.XPATH, cookie_reject_all_xpath))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", cookie_reject_btn)
            cookie_reject_btn.click()
            print(f"Success: Cookie banner closed now")
            return True
        except TimeoutException:
            print(f"Error: Timeout. Can't close cookie banner, it may block some elements")
            return False
        except Exception as e:
            print(f"Error: Can't close cookie banner: {str(e)}")
            return False    

    # Combine visibility check and action in one method with variable names for logging
    def perform_action_on_visible_element(self, timeout, by_method, locator_value, action: Actions, element_name: str):
        element, visible = self.is_element_visible(timeout, by_method, locator_value, element_name)
        if visible:
            return self.perform_action(element, action, element_name)
        else:
            print(f"Error: Element '{element_name}' is not visible or interactable for action '{action}'")
            return False

    # Check visibility of an element and if it is actionable (clickable/hoverable)
    # uses _find_element and used by other functions 
    def is_element_visible(self, timeout, by_method, locator_value, element_name: str):
        try:
            element = self._find_element(timeout, by_method, locator_value)
            if element and element.is_displayed() and element.is_enabled():
                print(f"Success: Element '{element_name}' is visible and enabled", flush=True)
                return element, True
            else:
                print(f"Error: Element '{element_name}' is not reachable or interactable", flush=True)
                if element and not element.is_displayed():
                    print(f"Element '{element_name}' is not displayed")
                if element and not element.is_enabled():
                    print(f"Element '{element_name}' is displayed but not enabled")
                return None, False
        except Exception as e:
            print(f"Error: {str(e)}")
            return None, False

    # Perform an action (click/hover) on an element with variable name for logging. 
    # NOTE: This doesn't check if it's clickable, QA is responsible for making sure with other (is_visible etc.)
    def perform_action(self, element, action: Actions, element_name: str):
        try:
            if action == Actions.CLICK:
                ActionChains(self.driver).move_to_element_with_offset(element, 10, 10).click().perform()
                print(f"Success: Clicked element '{element_name}'")
            elif action == Actions.HOVER:
                ActionChains(self.driver).move_to_element_with_offset(element, 20, 20).perform() 
                # Offset was needed to click/hover on some different screen res. 
                print(f"Success: Hovered over element '{element_name}'")
            return True
        except Exception as e:
            print(f"Error: Failed to perform '{action}' on element '{element_name}': {str(e)}", flush=True)
            return False

    # Private class find_element method. For single element. 
    # is_visible uses this, it's good to separate it because gives better error explanation
    # than selenium's own locate element method. 
    # Other functions only references the element once it fetches, so no performance suffering
    def _find_element(self, timeout, by_method, locator_value): 
        try:
            element = WebDriverWait(self.driver, timeout).until(
                expected_conditions.presence_of_element_located((by_method, locator_value))
            )
            return element
        except TimeoutException:
            print(f"Error: Timeout. Element '{locator_value}' not found using locator '{by_method}' within {timeout} seconds", flush=True)
            return None
        except NoSuchElementException:
            print(f"Error: No such element. Element '{locator_value}' not found using locator '{by_method}'", flush=True)
            return None
        
    # I added this later on because CSS selector will give multiple matches so the QA engineers can 
    # decide how/which they'll use the elements on the case. 
    def get_all_elements(self, by_method, locator_value, element_name: str):
        try:
            elements = self.driver.find_elements(by_method, locator_value)
            if len(elements) > 0:
                print(f"Success: Found {len(elements)} elements matching '{element_name}'")
            else:
                print(f"Error: No elements found matching '{element_name}'")
            return elements
        except Exception as e:
            print(f"Error: Unable to find elements matching '{element_name}': {str(e)}")
            return []    