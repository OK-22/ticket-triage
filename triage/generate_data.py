"""Builds a synthetic training set of IT help desk tickets.

The tickets are filled in from templates and then made messy (typos, greetings,
sign-offs, casing). This is NOT real data. The model is judged on a separate,
hand-written test set in data/handwritten_test.csv.
"""
import random

SLOTS = {
    "system": ["Windows", "email", "VPN", "domain", "laptop", "Teams", "work"],
    "name": ["a colleague", "jsmith", "mlopez", "our intern", "the new manager"],
    "day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "resource": ["finance share", "HR portal", "project drive", "CRM", "ticketing system", "shared folder"],
    "group": ["finance", "HR", "engineering", "marketing", "helpdesk"],
    "place": ["conference room", "lobby", "second floor", "warehouse", "break room"],
    "server": ["file server", "web server", "database server", "dev server"],
    "app": ["Excel", "Word", "Zoom", "Visual Studio Code", "Python", "Adobe Reader", "Chrome", "the accounting software"],
    "device": ["headset", "charger", "keyboard", "monitor", "docking station", "webcam"],
}

TEMPLATES = {
    "password_reset": [
        "I forgot my {system} password and cannot log in",
        "my {system} password has expired and I can't sign in",
        "please reset my {system} password",
        "I am locked out of my {system} account after too many failed attempts",
        "the new password I set is not working",
        "how do I change my password, it is about to expire",
        "account locked, need it unlocked",
        "cannot sign in, it says incorrect username or password",
        "need a temporary password for a user who is out of the office",
        "password reset request for {name}",
    ],
    "account_access": [
        "new hire starting {day} needs an account and a laptop",
        "please create a user account for our new employee {name}",
        "I need access to the {resource}",
        "add me to the {group} group please",
        "requesting permission to use the {resource}",
        "employee is leaving on {day}, please disable their account",
        "set up login and email for a new contractor",
        "I moved to a new team and need matching access",
        "please grant read access to the {resource}",
        "onboarding request: account, email, and building badge",
    ],
    "network_connectivity": [
        "cannot connect to the VPN from home",
        "wifi keeps dropping in the {place}",
        "no internet access on my desktop",
        "ssh to the {server} times out",
        "remote desktop says the computer cannot be reached",
        "the network drive is not available",
        "internet is very slow today",
        "cannot reach the {server}, connection refused",
        "ethernet cable plugged in but there is no connection",
        "the website loads for others but not for me",
    ],
    "software_issue": [
        "please install {app} on my computer",
        "{app} crashes every time I open it",
        "I need a license for {app}",
        "{app} will not start after the update",
        "the installer for {app} fails with an error",
        "can you update {app} to the latest version",
        "{app} is very slow and keeps freezing",
        "how do I uninstall {app}",
        "application shows an error message on launch",
        "need {app} for a new project",
    ],
    "hardware_issue": [
        "my laptop will not turn on",
        "the monitor flickers and goes black",
        "keyboard keys have stopped working",
        "printer on the {place} is offline",
        "laptop battery drains very fast",
        "my mouse is not responding",
        "I need a replacement {device}",
        "computer makes a loud noise and shuts down",
        "the screen is cracked",
        "the {device} is broken",
    ],
    "email_problem": [
        "I am not receiving emails from external senders",
        "outlook will not sync my mailbox",
        "my mailbox is full and I cannot send messages",
        "emails are stuck in the outbox",
        "calendar invites are not showing up",
        "messages I send are bouncing back",
        "too much spam in my inbox",
        "my out of office reply is not working",
        "cannot open attachments in email",
        "the shared mailbox is missing from outlook",
    ],
}

PREFIXES = ["", "", "", "hi, ", "hello, ", "hi team, ", "good morning, ", "urgent: ", "quick question, "]
SUFFIXES = ["", "", "", " thanks", " thank you", " asap", " please advise", " any help appreciated"]


def _fill(template, rng):
    out = template
    for key, values in SLOTS.items():
        token = "{" + key + "}"
        while token in out:
            out = out.replace(token, rng.choice(values), 1)
    return out


def _typo(word, rng):
    if len(word) < 4:
        return word
    i = rng.randrange(1, len(word) - 2)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def _noisy(text, rng):
    words = [_typo(w, rng) if rng.random() < 0.05 else w for w in text.split()]
    out = rng.choice(PREFIXES) + " ".join(words) + rng.choice(SUFFIXES)
    return out.lower() if rng.random() < 0.3 else out


def make_dataset(n_per_class=120, seed=7):
    """Return a list of (text, label) pairs, the same every time for a given seed."""
    rng = random.Random(seed)
    rows = []
    for label, templates in TEMPLATES.items():
        for _ in range(n_per_class):
            rows.append((_noisy(_fill(rng.choice(templates), rng), rng), label))
    rng.shuffle(rows)
    return rows
