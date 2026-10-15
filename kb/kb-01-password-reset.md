# KB-01: Reset a Linux user's password and force a change at next login

**Applies to:** Ubuntu Server 24.04 (ksserver, ksserver2)
**Audience:** Help desk and junior sysadmins
**Requires:** an admin account with sudo (admink1)

## When to use this
A user is locked out because they forgot or mistyped their temporary password, or their password has expired.

## Before you start
Verify the requester's identity using your organization's process (for example, a call-back or a manager approval). Never reset a password on an unverified request.

## Steps
Log in to the server over SSH as an admin, then run:

1. Set a new temporary password. Choose something long and easy to type, such as three words plus digits.
   ```
   sudo passwd <username>
   ```
2. Force the user to choose their own password at next login.
   ```
   sudo chage -d 0 <username>
   ```
3. Confirm the account state. "P" means a password is set.
   ```
   sudo passwd -S <username>
   ```
4. Give the temporary password to the user through a separate, approved channel.

## What the user will see
At their next login Linux prints "You are required to change your password immediately". They enter the temporary password as the current password, then choose a new one.

## If the new password is rejected
Ubuntu enforces password quality rules. A password that is too short, too simple, or too similar to the old one is refused with "The password has not been changed". Ask the user to try a longer password.

## Verification
The user can log in and the forced-change prompt does not appear again.

## Notes
- SSH password login is disabled on these servers (key-only), so a password reset affects console logins and `su`/`sudo` only. If the user cannot SSH in, see KB-03.
- Seen in the lab: repeated "Authentication failure" at `su` was a mistyped temporary password, because nothing is displayed while typing. Resetting it again fixed it.

## Escalate if
The account is locked (`passwd -S` shows "L"), the user reports they did not request the reset, or the reset fails with an error other than the quality check.
