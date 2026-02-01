import json
import time
import os
import base64
from getpass import getpass
from concurrent.futures import ThreadPoolExecutor, as_completed
import pyperclip
from playwright.sync_api import sync_playwright
import config
from ask_watson import ask_watson

SESSION_FILE = "session.json"

def safe_click(page, selector, timeout=3000, force=True):
    """
    Attempts to click a selector using multiple strategies.
    """
    try:
        # Strategy 1: Standard click
        # Use Force=True by default for this agent as we care more about result than human-simulation accuracy
        page.click(selector, timeout=timeout, force=force)
        return True
    except Exception as e:
        # Ignore syntax errors from bad AI selectors (e.g. jquery :contains)
        if "SyntaxError" not in str(e):
             print(f"Debug: Standard click failed on {selector}: {e}")
        
    try:
        # Strategy 2: JS Click
        page.evaluate(f"document.querySelector('{selector}').click()")
        return True
    except Exception as e:
        print(f"Debug: JS click failed on {selector}: {e}")
        
    return False

def safe_fill(page, selector, value, timeout=3000):
    """
    Attempts to fill an input using multiple strategies (fill, type, JS).
    """
    # 1. Wait for visibility
    try:
        page.wait_for_selector(selector, state="visible", timeout=timeout)
    except:
        print(f"Debug: Selector {selector} not visible within timeout.")
    
    # Strategy 1: Standard Fill
    try:
        page.fill(selector, value, timeout=timeout, force=True)
        # Verify
        actual_val = page.input_value(selector, timeout=1000)
        if actual_val == value:
            return True
    except Exception as e:
        print(f"Debug: Standard fill failed on {selector}: {e}")

    # Strategy 2: Click + Type (simulates keyboard)
    try:
        print(f"Debug: Retrying with Click+Type on {selector}...")
        page.click(selector, force=True)
        # page.keyboard.press("Control+A")
        # page.keyboard.press("Backspace")
        page.keyboard.type(value, delay=50) # Slow typing
        return True
    except Exception as e:
        print(f"Debug: Click+Type failed on {selector}: {e}")

    # Strategy 3: JS Injection (Last resort)
    try:
        print(f"Debug: Retrying with JS Injection on {selector}...")
        page.evaluate(f"document.querySelector('{selector}').value = '{value}'")
        # Trigger events so React/Vue notices the change
        page.evaluate(f"""
            const el = document.querySelector('{selector}');
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        """)
        return True
    except Exception as e:
        print(f"Debug: JS Inject failed on {selector}: {e}")
        
    return False

def handle_otp(page, selector, code):
    """
    Robust 4-stage OTP entry strategy:
    1. Paste without clicking (Simulates Ctrl+V)
    2. Click + Paste
    3. Click + Type (Char by char)
    4. Manual Fallback
    """
    print(f"Debug: Handling OTP with code length {len(code)}")

    # Helper to check if any input has the code (or partial code if split)
    def check_success():
        # Check if any input value matches the code
        try:
            # Simple check: is the full code in any input?
            is_full = page.evaluate(f"Array.from(document.querySelectorAll('input')).some(el => el.value === '{code}')")
            if is_full: return True
            
            # Complex check: are the characters distributed across inputs? 
            # (Only checks if we find inputs with values matching the first few chars, a bit loose but okay)
            if len(code) > 0:
                first_char_match = page.evaluate(f"Array.from(document.querySelectorAll('input')).some(el => el.value === '{code[0]}')")
                return first_char_match
        except:
            pass
        return False

    # Stage 1: Paste without clicking (Simulate Ctrl+V)
    print("Stage 1: Attempting global paste (Ctrl+V)...")
    try:
        pyperclip.copy(code)
        # Focus on body first just in case
        page.evaluate("document.body.focus()") 
        page.keyboard.press("Control+V")
        time.sleep(1)
        if check_success():
            print(">> OTP Success: Global paste worked.")
            return True
    except Exception as e:
        print(f"Stage 1 failed: {e}")

    # Determine best selector to click
    target_selector = selector
    if not target_selector:
        target_selector = "input" # Fallback to generic input
    
    print(f"Debug: Using target selector '{target_selector}' for click stages.")

    # Stage 2: Click & Paste
    print("Stage 2: Clicking input and pasting...")
    try:
        # Try to find the element
        # If generic 'input', getting the first visible one is usually what we want for OTP
        elem = page.locator(target_selector).first
        if elem.is_visible():
            elem.click(force=True)
            time.sleep(0.5)
            page.keyboard.press("Control+V")
            time.sleep(1)
            if check_success():
                print(">> OTP Success: Click & Paste worked.")
                return True
        else:
            print(f"Debug: Selector {target_selector} not visible.")
    except Exception as e:
        print(f"Stage 2 failed: {e}")

    # Stage 3: Click & Type
    print("Stage 3: Clicking input and typing manually...")
    try:
        elem = page.locator(target_selector).first
        if elem.is_visible():
            elem.click(force=True)
            # Clear it first? Maybe dangerous if it's split inputs. 
            # Let's just type.
            for char in code:
                page.keyboard.type(char, delay=100)
            
            time.sleep(1)
            if check_success():
                print(">> OTP Success: Click & Type worked.")
                return True
    except Exception as e:
        print(f"Stage 3 failed: {e}")

    # Stage 4: Manual Fallback
    print("\n" + "="*40)
    print("CRITICAL: AI could not enter OTP automatically.")
    print(f"Please enter the code '{code}' MANUALLY in the browser window.")
    print("="*40 + "\n")
    # We wait a bit to let the user do it
    # We can't really block forever here easily without disrupting the flow, 
    # but we can give them a generous pause or ask for confirmation in console?
    # Asking for confirmation in console:
    input(">> Press ENTER once you have manually entered the OTP...")
    return True # We assume they did it

def load_cookies(context, path):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                cookies = json.load(f)
            # Clean cookies for Playwright
            valid_cookies = []
            for c in cookies:
                # Remove fields that Playwright doesn't like or that cause issues
                if 'url' in c:
                    del c['url']
                if 'sameSite' in c and c['sameSite'] not in ["Strict", "Lax", "None"]:
                    c['sameSite'] = "None" # Default to None if unspecified/no_restriction logic is complex
                valid_cookies.append(c)
                
            context.add_cookies(valid_cookies)
            print(f"Succefully loaded {len(valid_cookies)} cookies.")
        except Exception as e:
            print(f"Error loading cookies: {e}")
    else:
        print(f"WARNING: Cookies file not found at {path}. You will not be logged in.")

def analyze_network_event(event):
    """Uses AI to understand what a network request does and returns context."""

    # Skip noisy/unimportant requests
    url = event.get("url", "")
    if any(skip in url for skip in ["analytics", "sentry", "batch", "heartbeat", "gasv3"]):
        return None

    prompt = f"""Analyze this API request and explain its PURPOSE in 1 short sentence.
Focus on what USER ACTION or DATA this relates to.

Method: {event.get('method')}
URL: {url}
Post Data: {event.get('post_data', 'None')[:500] if event.get('post_data') else 'None'}

Return ONLY a JSON object:
{{"purpose": "Brief description of what this does", "category": "read|write|auth|analytics|other", "useful_for_tool": boolean}}
"""

    try:
        response = ask_watson(prompt)
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text)
    except Exception as e:
        return None


def analyze_page_with_ai(screenshot_bytes):
    """
    Analyzes a page for login fields.
    Note: Watson does not support image/screenshot analysis.
    Returns default selectors for common login patterns.
    """
    # Watson doesn't support multimodal (image) inputs
    # Return common selectors as fallback
    print("Warning: Watson does not support screenshot analysis. Using default selectors.")
    return {
        "email_selector": "input[type='email'], input[name='email'], input[name='username']",
        "password_selector": "input[type='password']",
        "primary_action_button_selector": "button[type='submit'], input[type='submit']",
        "cookie_button_selector": None,
        "otp_selector": "input[type='text']",
        "is_logged_in": False,
        "step_description": "Default login selectors (no AI analysis available)"
    }

def smart_login(page):
    """
    Uses AI to interactively log the user in.
    """
    print(f"page is {page}")
    print("\n[AI Login Agent] Starting Smart Login Sequence...")
    max_steps = 10
    
    for step in range(max_steps):
        print(f"\n[Step {step+1}] Analyzing page...")
        time.sleep(2) # Wait for animations
        
        # Take screenshot
        screenshot = page.screenshot()
        print("Screenshot taken.\nStart analyzing...")
        # Analyze
        analysis = analyze_page_with_ai(screenshot)
        if not analysis:
            print("Failed to analyze page. Retrying...")
            continue
            
        print(f"[AI Analysis] Status: {analysis.get('step_description')}")
        
        if analysis.get('is_logged_in'):
            print(">> SUCCESS: Logged in successfully!")
            return True
            
        # Handle Cookies First
        if analysis.get('cookie_button_selector'):
            print("Found cookie banner. Accepting...")
            try:
                page.click(analysis['cookie_button_selector'])
                time.sleep(1)
                continue # Re-analyze after click
            except:
                pass

        # Handle Inputs
        # Helper flag to prevent clicking submit if we failed to type in a field
        # Helper counters
        successful_fills = 0
        failed_fills = 0

        # Email
        if analysis.get('email_selector'):
            email = input(">> AI sees an Email Field. Please enter your email (leave empty to skip): ")
            if email:
                print(f"Attempting to fill email using selector: {analysis['email_selector']}")
                if safe_fill(page, analysis['email_selector'], email):
                    print(">> Verification using safe_fill: Success")
                    did_interaction = True
                    successful_fills += 1
                else:
                    print(f"Correction: Could not fill email field even with fallback strategies.")
                    failed_fills += 1
                    did_interaction = True

        # Password
        if analysis.get('password_selector'):
            pwd = getpass(">> AI sees a Password Field. Please enter your password (leave empty to skip): ")
            if pwd:
                print(f"Attempting to fill password...")
                if safe_fill(page, analysis['password_selector'], pwd):
                    print(">> Verification using safe_fill: Success")
                    did_interaction = True
                    successful_fills += 1
                else:
                    print(f"Correction: Could not fill password field.")
                    failed_fills += 1
                    did_interaction = True

        # OTP / 2FA
        if analysis.get('otp_selector'):
            code = input(">> AI sees a 2FA Code Field. Please enter your code: ")
            if code:
                # Use our new robust handler
                # Pass the selector from AI, but handle_otp will fallback to 'input' if needed
                if handle_otp(page, analysis['otp_selector'], code):
                    did_interaction = True
                    successful_fills += 1
                else:
                    print(f"Correction: Could not fill OTP field.")
                    failed_fills += 1
                    did_interaction = True
            
        # Submit / Continue / Next
        clicked_action = False
        
        # Logic: We click submit if:
        # A) We successfully filled something (successful_fills > 0)
        # B) We didn't try to fill anything (waiting for manual input? or just clicking a button)
        # We invalid click IF: 
        # C) We tried to fill something, failed, AND didn't succeed at filling anything else (failed_fills > 0 and successful_fills == 0)
        
        should_click = True
        if failed_fills > 0 and successful_fills == 0:
            should_click = False

        # 1. Try AI Suggestion
        if analysis.get('primary_action_button_selector'):
            if not should_click:
                 print("Skipping action button click because input filling failed completely. Retrying analysis loop...")
            else:
                print(f"Clicking primary action button (selector: {analysis['primary_action_button_selector']})...")
                if safe_click(page, analysis['primary_action_button_selector']):
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except:
                        pass
                    did_interaction = True
                    clicked_action = True
        
        # 2. Brute Force Fallback (if AI didn't find one or failed to click)
        print(f"DEBUG: clicked_action={clicked_action}, failed_fills={failed_fills}, successful_fills={successful_fills}")
        if not clicked_action and should_click:
            print("AI finding failed. Attempting brute-force button search...")
            keywords = ["Log in", "Log In", "Sign in", "Sign In", "Next", "next", "NEXT", "Continue", "continue", "CONTINUE", "Login", "login", "LOGIN", "Submit", "submit", "SUBMIT"]
            
            time.sleep(2)
            for kw in keywords:
                try:
                    # Look for buttons with this text
                    # We check: specific text locator, or buttons containing text
                    # Playwright's 'text=' is quite powerful
                    loc = page.get_by_role("button", name=kw, exact=True)
                    if loc.is_visible():
                        print(f"Brute-force: Found button with text '{kw}'. Clicking...")
                        try:
                            loc.click(timeout=3000, force=True)
                        except:
                            # Use JS click as fallback for stubborn elements
                            print("Standard click failed. Using JS dispatch...")
                            loc.evaluate("e => e.click()")
                            
                        try:
                            page.wait_for_load_state("networkidle", timeout=5000)
                        except:
                            pass
                        did_interaction = True
                        clicked_action = True
                        break
                    
                    # Fallback to interactive elements (links, inputs) containing text
                    # Avoid clicking just 'text' because it hits headers like "Log in to continue"
                    selectors = [
                        f"a:text-is('{kw}')", 
                        f"a:has-text('{kw}')",
                        f"input[type='submit'][value='{kw}']",
                        f"input[type='button'][value='{kw}']",
                        f"button:has-text('{kw}')"
                    ]
                    
                    found_fallback = False
                    for sel in selectors:
                        locs = page.locator(sel)
                        count = locs.count()
                        if count > 0:
                             for i in range(count):
                                if locs.nth(i).is_visible():
                                    print(f"Brute-force: Found interactive element ({sel}) with text '{kw}'. Clicking...")
                                    try:
                                        locs.nth(i).click(timeout=3000, force=True)
                                    except:
                                         print("Standard click failed. Using JS dispatch...")
                                         locs.nth(i).evaluate("e => e.click()")
                                    
                                    try:
                                        page.wait_for_load_state("networkidle", timeout=5000)
                                    except:
                                        pass
                                    did_interaction = True
                                    clicked_action = True
                                    found_fallback = True
                                    break
                        if found_fallback: break
                    
                    if clicked_action: break
                    
                except Exception as e:
                    print(f"Brute-force attempt on '{kw}' failed/skipped: {e}")
                
        if not did_interaction:
            print("AI didn't know what to do. Waiting for manual input or refresh...")
            time.sleep(5)
            
    print("Max login steps reached.")
    return False

def record():
    if "yourboard" in config.TARGET_URL:
        print("\n\nCRITICAL WARNING: It looks like you are using the default placeholder URL ('yourboard').")
        print("Please check your .env file or config.py and set a REAL Trello board URL.\n\n")

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=False) 
        # 1. Check for valid session
        if os.path.exists(SESSION_FILE):
            print(f"Loading session from {SESSION_FILE}...")
            context = browser.new_context(storage_state=SESSION_FILE)
            page = context.new_page()
            page.goto(config.TARGET_URL, timeout=60000)
        else:
            print("No session found. Initiating AI Smart Login...")
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to generic Trello login to start
            try:
                page.goto("https://trello.com/login", timeout=60000)
            except:
                pass
                
            if smart_login(page):
                # Save session
                print(f"Saving session to {SESSION_FILE}...")
                context.storage_state(path=SESSION_FILE)
                
                # Navigate to target if we aren't there
                if config.TARGET_URL not in page.url:
                    page.goto(config.TARGET_URL)
            else:
                print("Login failed or timed out. Continuing as guest (might fail)...")
        # storage for events
        network_events = []
        
        def handle_response(response):
            try:
                # Capture only XHR/Fetch requests that are successful
                if response.request.resource_type in ["fetch", "xhr"] and response.status < 400:
                    # Filter out some noise?
                    url = response.url
                    if "analytics" in url or "log" in url:
                        return

                    event = {
                        "method": response.request.method,
                        "url": url,
                        "request_headers": response.request.headers,
                        "status": response.status
                    }

                    # Handle post_data safely - it may be binary/gzip compressed
                    try:
                        post_data = response.request.post_data
                        if post_data:
                            event["post_data"] = post_data
                    except Exception:
                        # If post_data is binary (gzip), try to get raw bytes and base64 encode
                        try:
                            post_data_buffer = response.request.post_data_buffer
                            if post_data_buffer:
                                event["post_data_base64"] = base64.b64encode(post_data_buffer).decode('ascii')
                                event["post_data_is_binary"] = True
                        except Exception:
                            pass  # Skip post_data if we can't get it at all

                    network_events.append(event)
                    print(f"Captured: {event['method']} {event['url']}")
            except Exception as e:
                print(f"Error handling response: {e}")

        page.on("response", handle_response)
        
        print(f"Navigating to {config.TARGET_URL}")
        try:
            page.goto(config.TARGET_URL, timeout=60000)
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Navigation error (continuing): {e}")
        
        # Interactive Helper
        print("Starting Interaction Phase...")
        
        # Highlight interactables
        page.evaluate("""
            const elements = document.querySelectorAll('button, a, [role="button"]');
            elements.forEach(el => el.style.border = '2px solid red');
        """)
        
        # TODO: Implement cleaner crawler interaction
        # For now, we scrape clicks on a few items
        interactables = page.locator("button, [role='button']").all()
        print(f"Found {len(interactables)} potential buttons.")
        
        # Limit to first few to avoid chaos
        for i, elem in enumerate(interactables[:3]): 
            try:
                if elem.is_visible():
                    print(f"Clicking element {i}")
                    # Screenshot before
                    # page.screenshot(path=f"step_{i}_before.png")
                    
                    elem.click(timeout=2000)
                    page.wait_for_timeout(3000) # Wait for network
                    
                    # Screenshot after
                    # page.screenshot(path=f"step_{i}_after.png")
            except Exception as e:
                print(f"Skipping element {i}: {e}")

        # Save events
        with open(config.EVENTS_LOG, "w") as f:
            json.dump(network_events, f, indent=2)
        print(f"Saved {len(network_events)} events to {config.EVENTS_LOG}")

        # AI Analysis of captured events (parallel for speed)
        print("\n[AI Analysis] Analyzing captured network events in parallel...")

        def analyze_with_index(args):
            idx, event = args
            return idx, analyze_network_event(event)

        # Use ThreadPoolExecutor for parallel API calls (10 workers)
        results = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(analyze_with_index, (i, e)): i for i, e in enumerate(network_events)}
            done_count = 0
            for future in as_completed(futures):
                done_count += 1
                print(f"\r  Analyzed {done_count}/{len(network_events)} events...", end="", flush=True)
                try:
                    idx, analysis = future.result()
                    results[idx] = analysis
                except Exception:
                    pass

        print()  # newline after progress

        # Apply results to events
        enriched_events = []
        for i, event in enumerate(network_events):
            analysis = results.get(i)
            if analysis:
                event["ai_context"] = analysis
                if analysis.get("useful_for_tool"):
                    print(f"  - {analysis.get('purpose')} [{analysis.get('category')}]")
            enriched_events.append(event)

        # Save enriched events
        enriched_path = config.EVENTS_LOG.replace(".json", "_enriched.json")
        with open(enriched_path, "w") as f:
            json.dump(enriched_events, f, indent=2)
        print(f"Saved enriched events to {enriched_path}")
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    record()
