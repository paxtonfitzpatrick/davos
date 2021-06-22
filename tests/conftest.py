import json
import re
import time
from os import getenv
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException, 
    TimeoutException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class NotebookDriver:
    def __init__(self, url, browser='firefox'):
        self.url = url
        if browser.lower() != 'firefox':
            raise NotImplementedError("Test only implemented for Firefox")
        options = Options()
        options.headless = False
        self.driver = webdriver.Firefox(options=options, 
                                        executable_path=getenv('DRIVER_PATH'))
        self.driver.get(url)
        
    def click(
            self, 
            __locator_or_el, 
            /,
            by=By.CSS_SELECTOR, 
            timeout=10, 
            poll_frequency=0.5, 
            ignored_exceptions=None
    ):
        if isinstance(__locator_or_el, WebElement):
            start_time = time.time()
            while True:
                try:
                    __locator_or_el.click()
                except (ElementNotInteractableException, *ignored_exceptions) as e:
                    if time.time() - start_time >= timeout:
                        raise TimeoutException(
                            f"{__locator_or_el} was not clickable after "
                            f"{timeout} seconds"
                        ) from e
                    else:
                        pass
                else:
                    return __locator_or_el
        else:
            wait = WebDriverWait(self.driver, timeout=timeout, 
                                 poll_frequency=poll_frequency, 
                                 ignored_exceptions=ignored_exceptions)
            el_is_clickable = EC.element_to_be_clickable((by, __locator_or_el))
            clickable_el = wait.until(el_is_clickable)
            clickable_el.click()
            return clickable_el

    def quit(self):
        self.driver.quit()


class ColabDriver(NotebookDriver):
    def __init__(self, notebook_path, browser='firefox'):
        username = getenv("GITHUB_ACTOR")
        ref = getenv("GITHUB_SHA")
        url = f"https://colab.research.google.com/github/{username}/davos/blob/{ref}/{notebook_path}"
        super().__init__(url=url, browser=browser)
        self.sign_in_google()

    def sign_in_google(self):
        # click "Sign in" button
        self.click("#gb > div > div.gb_Se > a")
        # enter email
        email_input_box = self.driver.find_element_by_id("identifierId")
        email_input_box.send_keys(getenv("GMAIL_ADDRESS"))
        self.click("identifierNext", By.ID)
        # screen takes a moment to progress
        time.sleep(3)
        # enter password
        pwd_input_box = self.driver.find_element_by_name("password")
        pwd_input_box.send_keys(getenv("GMAIL_PASSWORD"))
        self.click("passwordNext", By.ID)
        
    def run_all_cells(self, pre_approved=False):
        keyboard_shortcut = ActionChains(self.driver) \
            .key_down(Keys.META).send_keys() \
            .send_keys(Keys.F9) \
            .key_up(Keys.META)
        keyboard_shortcut.perform()
        if not pre_approved:
            # approve notebook not authored by Google
            # (button takes a second to become clickable)
            self.click("ok", By.ID)
            
    def get_test_result(self, func_name):
        # TODO: implement me
        return True


class JupyterDriver(NotebookDriver):
    def __init__(self, notebook_path, ip='127.0.0.1', port='8888', browser='firefox'):
        self.set_kernel(notebook_path)
        url = f"http://{ip}:{port}/notebooks/{notebook_path}"
        super().__init__(url=url, browser=browser)
        
    def run_all_cells(self):
        # wait up to 10 seconds for "Cell" menu item to be clickable
        self.click("#menus > div > div > ul > li:nth-child(5) > a")
        self.click("run_all_cells", By.ID)
        
    def get_test_result(self, func_name):
        # TODO: implement me
        return True
        
    def set_kernel(self, notebook_path):
        repo_root = Path(getenv("GITHUB_WORKSPACE")).resolve(strict=True)
        notebook_path = repo_root.joinpath(notebook_path)
        with notebook_path.open() as nb:
            notebook_json = json.load(nb)
        notebook_json['metadata']['kernelspec'] = {
            'display_name': 'kernel-env',
            'language': 'python',
            'name': 'kernel-env'
        }
        with notebook_path.open('w') as nb:
            json.dump(notebook_json, nb)



class NotebookFile(pytest.File):
    test_func_pattern = re.compile('(?<=def )test_[^(]+', re.MULTILINE)

    def __init__(self, fspath, *, driver_cls, parent=None, config=None, session=None, nodeid=None):
        super().__init__(fspath=fspath, parent=parent, config=config, session=session, nodeid=nodeid)
        self.driver_cls = driver_cls
        self.driver = None
        repo_root = Path(getenv("GITHUB_WORKSPACE")).resolve(strict=True)
        notebook_abspath = Path(self.fspath).resolve(strict=True)
        self.notebook_path = str(notebook_abspath.relative_to(repo_root))
        
    def collect(self):
        with self.fspath.open() as nb:
            notebook_json = json.load(nb)
        for cell in notebook_json['cells']:
            if cell['cell_type'] == 'code':
                cell_contents = ''.join(cell['source'])
                # noinspection PyCompatibility
                # TODO: make sure tests_require is being enforced
                if match := self.test_func_pattern.search(cell_contents):
                    yield NotebookTest.from_parent(self, name=match.group())
    
    def setup(self):
        super().setup()
        self.driver = self.driver_cls(self.notebook_path)
        self.driver.run_all_cells()
    
    def teardown(self):
        if self.driver is not None:
            self.driver.quit()
        return super().teardown()
        

class NotebookTest(pytest.Item):
    def runtest(self): 
        test_result = self.parent.driver.get_test_result(self.name)
        return test_result
    
    def repr_failure(self, execinfo):
        # TODO: write me
        ...
    
    def reportinfo(self):
        # TODO: write me
        return self.fspath, None, ""
        

def pytest_collect_file(path, parent):
    notebook_type = getenv("NOTEBOOK_TYPE")
    if notebook_type == 'colab':
        driver_cls = ColabDriver
    else:
        driver_cls = JupyterDriver
    if path.basename.startswith('test') and path.ext == ".ipynb":
        if any(key in path.basename for key in (notebook_type, 'shared', 'common')):
            return NotebookFile.from_parent(parent, fspath=path, driver_cls=driver_cls)
