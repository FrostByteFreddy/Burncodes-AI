from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Login
    page.goto("http://localhost:5173/login")
    page.get_by_label("Email").fill("test@test.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Log In").click()
    page.wait_for_url("http://localhost:5173/manage-tenants")

    # Navigate to the first tenant's analytics page
    page.locator('.tenant-card').first.click()
    page.wait_for_url("**/tenant/**")
    page.get_by_role("link", name="Analytics").click()
    page.wait_for_url("**/analytics")

    # Take a screenshot of the analytics page
    page.screenshot(path="jules-scratch/verification/analytics-page.png")

    # Navigate to the chat logs page
    page.get_by_role("link", name="Chat Logs").click()
    page.wait_for_url("**/chat-logs")

    # Take a screenshot of the chat logs page
    page.screenshot(path="jules-scratch/verification/chat-logs-page.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)