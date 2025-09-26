import time
from playwright.sync_api import sync_playwright, expect
import re

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Generate unique credentials for the new user with a stronger password
    unique_id = int(time.time())
    email = f"testuser_{unique_id}@test.com"
    password = "StrongPassword123!"
    tenant_name = f"Tenant {unique_id}"
    base_url = "http://localhost:5173"

    try:
        # 1. Sign up a new user
        print("Navigating to signup page...")
        page.goto(f"{base_url}/signup")
        page.get_by_label("First Name").fill("Test")
        page.get_by_label("Last Name").fill("User")
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Sign Up").click()
        print("Waiting for signup to complete...")
        # Check for success message
        expect(page.get_by_text("Signup successful! Please check your email to confirm your account.")).to_be_visible(timeout=15000)
        print("Signup form submitted successfully.")

        # 2. Log in directly
        print("Navigating to login page...")
        page.goto(f"{base_url}/login")
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Login").click()
        expect(page).to_have_url(f"{base_url}/manage-tenants", timeout=15000)
        print("Login successful after signup.")

        # 3. Create a new tenant
        print("Creating a new tenant...")
        page.get_by_role("button", name="Create a Tenant").click()
        page.get_by_label("Tenant Name").fill(tenant_name)
        page.get_by_role("button", name="Create").click()
        expect(page.get_by_text(tenant_name)).to_be_visible(timeout=10000)
        print("Tenant created.")

        # 4. Navigate to a specific page to set the last visited route
        print("Navigating to Sources page...")
        page.get_by_role('link', name='Sources').click()
        expect(page).to_have_url(re.compile(r'/tenant/.*/sources'), timeout=10000)
        print(f"Current URL: {page.url}")

        # 5. Log out
        print("Logging out...")
        page.get_by_role("button", name="Logout").click()
        expect(page).to_have_url(f"{base_url}/login", timeout=10000)
        print("Logout successful.")

        # 6. Log back in
        print("Logging back in...")
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Login").click()

        # 7. Verify redirection and state restoration
        print("Verifying persistence...")
        expect(page).to_have_url(re.compile(r'/tenant/.*/sources'), timeout=15000)
        expect(page.get_by_text(tenant_name)).to_be_visible()
        print("Verification successful! State was persisted.")

        # 8. Take a screenshot for visual confirmation
        screenshot_path = "jules-scratch/verification/verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

    except Exception as e:
        print(f"An error occurred during verification: {e}")
        page.screenshot(path="jules-scratch/verification/error.png")
        raise
    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)