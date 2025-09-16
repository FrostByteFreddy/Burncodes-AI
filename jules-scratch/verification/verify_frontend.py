import time
from playwright.sync_api import sync_playwright, expect

def run_verification(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Navigate to the login page
        page.goto("http://localhost:5173/login")

        # Use the confirmed migration user to log in
        email = "migration-user@swiftanswer.com"
        password = "migration-password-for-swiftanswer"

        # Fill out the login form
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Login").click()

        # Verify navigation to the dashboard
        expect(page).to_have_url("http://localhost:5173/dashboard", timeout=10000)

        # Verify the dashboard heading is visible
        dashboard_heading = page.get_by_role("heading", name="My Tenants")
        expect(dashboard_heading).to_be_visible()

        # Take a screenshot of the dashboard
        page.screenshot(path="jules-scratch/verification/dashboard.png")
        print("✅ Verification successful, screenshot taken.")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        # Take a screenshot on failure for debugging
        page.screenshot(path="jules-scratch/verification/failure.png")
    finally:
        browser.close()

with sync_playwright() as playwright:
    run_verification(playwright)
