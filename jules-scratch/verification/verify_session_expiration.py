import time
from playwright.sync_api import sync_playwright, expect
import re

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Generate unique credentials for the new user
    unique_id = int(time.time())
    email = f"testuser_{unique_id}@test.com"
    password = "StrongPassword123!"
    tenant_name = f"Tenant {unique_id}"
    base_url = "http://localhost:5173"

    try:
        # 1. Sign up and log in
        print("Signing up a new user...")
        page.goto(f"{base_url}/signup")
        page.get_by_label("First Name").fill("Test")
        page.get_by_label("Last Name").fill("User")
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Sign Up").click()
        expect(page.get_by_text("Signup successful!")).to_be_visible(timeout=15000)

        print("Logging in...")
        page.goto(f"{base_url}/login")
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Login").click()
        expect(page).to_have_url(f"{base_url}/manage-tenants", timeout=15000)
        print("Login successful.")

        # 2. Create a tenant
        print("Creating a new tenant...")
        page.get_by_role("button", name="Create a Tenant").click()
        page.get_by_label("Tenant Name").fill(tenant_name)
        page.get_by_role("button", name="Create").click()
        expect(page.get_by_text(tenant_name)).to_be_visible(timeout=10000)
        print("Tenant created.")

        # 3. Simulate session expiration by removing the auth token from localStorage
        print("Simulating session expiration...")
        page.evaluate("""
            () => {
                for (const key of Object.keys(localStorage)) {
                    if (key.startsWith('sb-') && key.endsWith('-auth-token')) {
                        localStorage.removeItem(key);
                        console.log(`Removed token: ${key}`);
                        break;
                    }
                }
            }
        """)

        # 4. Trigger an API call by navigating to another protected route
        print("Triggering API call on a protected route...")
        page.get_by_role('link', name='Sources').click()

        # 5. Assert that the user is redirected to the login page
        print("Verifying redirection to login page...")
        expect(page).to_have_url(f"{base_url}/login", timeout=15000)

        # 6. Assert that the session expired toast message is displayed
        print("Verifying session expired toast message...")
        expect(page.get_by_text("Your session has expired. Please log in again.")).to_be_visible()
        print("Verification successful!")

        # 7. Take a screenshot for visual confirmation
        screenshot_path = "jules-scratch/verification/session_expired.png"
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