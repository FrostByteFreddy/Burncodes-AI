from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:5173/signup")

    # Sign up
    page.get_by_label("Email").fill("test@example.com")
    page.get_by_label("Password").fill("password123")
    page.get_by_label("Confirm Password").fill("password123")
    page.get_by_role("button", name="Create Account").click()

    # Wait for navigation to the manage tenants page
    expect(page).to_have_url("http://localhost:5173/manage-tenants")

    # Create a new tenant
    page.get_by_role("button", name="Create New Tenant").click()
    page.get_by_label("Tenant Name").fill("Test Tenant")
    page.get_by_role("button", name="Create").click()

    # Get the tenant ID from the URL
    expect(page).to_have_url(lambda url: "http://localhost:5173/tenant/" in url)
    tenant_id = page.url.split("/")[-1]

    # Navigate to the fine-tuning page
    page.goto(f"http://localhost:5173/tenant/{tenant_id}/fine-tune")

    # Wait for the page to load
    expect(page.get_by_role("heading", name="Fine-Tuning Rules")).to_be_visible()

    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/verification.png")

    browser.close()
