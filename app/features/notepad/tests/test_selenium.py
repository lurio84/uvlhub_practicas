"""End-to-end browser tests for the notepad feature.

Driven by the selenium grid started by::

    docker compose -f docker/docker-compose.dev.yml up

Run with::

    rosemary test notepad --e2e

The driver comes from ``tests/selenium_support``, not from
``splent_framework.selenium.common``. The framework helper builds a local
Chrome through webdriver_manager, and there is no browser inside
web_app_container, so it cannot reach the grid. See that module's docstring.

These tests run against the live application and the seeded development
database, not the test database. There is no fixture and no reset between
tests, so keep them read-only or clean up after yourself: the CRUD test
deletes the notepad it creates, under a unique title.
"""
import uuid

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tests.selenium_support import close_driver, get_host_for_selenium_testing, initialize_driver

pytestmark = pytest.mark.e2e

SEEDED_EMAIL = "user1@example.com"
SEEDED_PASSWORD = "1234"


def _log_in(driver, host):
    driver.get(f"{host}/login")
    driver.find_element(By.NAME, "email").send_keys(SEEDED_EMAIL)
    driver.find_element(By.NAME, "password").send_keys(SEEDED_PASSWORD)
    driver.find_element(By.ID, "submit").click()
    # The logout control is an icon link, so match on its href.
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="/logout"]')))


def _click_when_settled(driver, element):
    """Click only once the page has settled, so the click does not land mid-layout."""
    WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    element.click()


def _wait_for_text(driver, text):
    WebDriverWait(driver, 15).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))


def test_notepad_index_redirects_anonymous_user_to_login():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/notepad")
        WebDriverWait(driver, 15).until(EC.url_contains("/login"))

        assert "/login" in driver.current_url
    finally:
        close_driver(driver)


def test_notepad_index_shows_new_notepad_link_when_logged_in():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        _log_in(driver, host)
        driver.get(f"{host}/notepad")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.LINK_TEXT, "New notepad")))

        assert "Page not found" not in driver.title
        assert driver.current_url.endswith("/notepad")
    finally:
        close_driver(driver)


def test_create_and_delete_notepad_through_the_interface():
    driver = initialize_driver()
    title = f"Selenium notepad {uuid.uuid4().hex[:8]}"
    try:
        host = get_host_for_selenium_testing()
        _log_in(driver, host)

        driver.get(f"{host}/notepad/create")
        title_input = driver.find_element(By.NAME, "title")
        title_input.send_keys(title)
        driver.find_element(By.NAME, "body").send_keys("written by a browser")
        # The Chrome node can drop keystrokes, so check what was typed.
        assert title_input.get_attribute("value") == title
        _click_when_settled(driver, driver.find_element(By.ID, "submit"))

        _wait_for_text(driver, "Notepad created successfully!")
        assert driver.find_elements(By.LINK_TEXT, title)

        delete_button = driver.find_element(By.XPATH, f"//li[.//a[text()='{title}']]//button[@type='submit']")
        _click_when_settled(driver, delete_button)

        _wait_for_text(driver, "Notepad deleted successfully!")
        assert not driver.find_elements(By.LINK_TEXT, title)
    finally:
        close_driver(driver)
