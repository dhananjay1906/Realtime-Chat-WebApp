"""End-to-end check: two separate browsers chat in real time.

Usage: start the app (see README), then
    python e2e/two_users.py [base_url] [screenshot_dir]
"""

import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
SHOTS = Path(sys.argv[2]) if len(sys.argv) > 2 else None


def join(page, name):
    page.goto(BASE)
    page.get_by_label("Display name").fill(name)
    page.get_by_role("button", name="Join chat →").click()
    expect(page.locator(".status-online")).to_be_visible()


def say(page, text):
    page.get_by_label("Message").fill(text)
    page.keyboard.press("Enter")


with sync_playwright() as p:
    browser = p.chromium.launch()
    ada = browser.new_context(viewport={"width": 1280, "height": 760}).new_page()
    linus = browser.new_context(viewport={"width": 1280, "height": 760}).new_page()
    errors = []
    for page in (ada, linus):
        page.on("pageerror", lambda e: errors.append(str(e)))

    join(ada, "Ada Lovelace")
    join(linus, "Linus")

    # presence: both see each other
    expect(ada.locator(".people")).to_contain_text("Linus")
    expect(linus.locator(".people")).to_contain_text("Ada Lovelace")

    # typing indicator shows up for the other person
    linus.get_by_label("Message").press_sequentially("hey", delay=40)
    expect(ada.locator(".typing")).to_contain_text("Linus is typing")
    linus.get_by_label("Message").fill("")

    # messages arrive instantly in both directions
    say(ada, "Hey Linus! Real-time chat is live 🚀")
    expect(linus.locator(".msg-text").last).to_have_text("Hey Linus! Real-time chat is live 🚀")
    say(linus, "Nice — FastAPI WebSockets + React?")
    expect(ada.locator(".msg-text").last).to_have_text("Nice — FastAPI WebSockets + React?")
    say(ada, "Yep. History is saved too, refresh and it's still here.")
    say(ada, "And you can make your own rooms from the sidebar.")
    expect(linus.locator(".msg-text")).to_have_count(4)

    # history survives a reload
    linus.reload()
    expect(linus.locator(".msg-text")).to_have_count(4)

    # rooms are separate
    ada.get_by_role("button", name="dev-talk").click()
    expect(ada.locator(".chat-head h2")).to_contain_text("dev-talk")
    say(ada, "This one only shows up in #dev-talk")
    expect(ada.locator(".msg-text")).to_have_count(1)
    expect(linus.locator(".msg-text")).to_have_count(4)
    ada.get_by_role("button", name="general").click()
    expect(ada.locator(".msg-text")).to_have_count(4)

    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        linus.get_by_label("Message").press_sequentially("Let's ship it", delay=30)
        expect(ada.locator(".typing")).to_contain_text("Linus is typing")
        ada.wait_for_timeout(400)
        ada.screenshot(path=SHOTS / "chat.png")
        join_page = browser.new_context(viewport={"width": 1280, "height": 760}).new_page()
        join_page.goto(BASE)
        join_page.get_by_label("Display name").fill("Grace Hopper")
        join_page.screenshot(path=SHOTS / "join.png")
        mobile = browser.new_context(viewport={"width": 390, "height": 760}, device_scale_factor=2).new_page()
        join(mobile, "Grace")
        mobile.wait_for_timeout(600)
        mobile.screenshot(path=SHOTS / "mobile.png")

    assert not errors, errors
    browser.close()
    print("E2E passed: presence, typing, live messages, history, rooms")
