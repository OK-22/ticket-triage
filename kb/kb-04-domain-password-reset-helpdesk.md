# KB-04: Reset a domain user's password as help desk (delegated rights)

- **Applies to:** Active Directory domain kslab.local, workstation KSW10 (Windows 10 Pro)
- **Audience:** Help desk staff in the HelpDesk group
- **Requires:** membership in the HelpDesk group, signed in to a domain-joined workstation as a standard user (no local or domain admin rights needed)

## How the access is set up
The HelpDesk group was granted three rights on the KSLab Users OU, using dsacls on the domain controller:
- Reset Password on user objects
- Write access to pwdLastSet (used for "must change password at next logon")
- Write access to lockoutTime (used for unlocking accounts)

The rights are inherited by every user in that OU. They do not apply to the built-in Administrator account, which lives in a different container.

## Before you start
Verify the requester's identity using your organization's process (for example, a call-back or a manager approval). Never reset a password on an unverified request.

## Steps (PowerShell, as the help desk user)
1. Open a regular PowerShell window. Do not use "Run as administrator", because the help desk account has no local admin rights.
2. Confirm who you are and that you have the group:
   ```
   whoami
   whoami /groups | findstr /i helpdesk
   ```
3. Generate a temporary password that meets the domain policy (minimum 7 characters, complexity on, history of 24):
   ```
   $new = "Ks" + (Get-Random -Minimum 100000 -Maximum 999999) + "-Zq!"
   $new
   ```
4. Reset the user's password through LDAP:
   ```
   $u = [ADSI]"LDAP://CN=James Smith,OU=Users,OU=KSLab,DC=kslab,DC=local"
   $u.SetPassword($new)
   ```
   No output means the reset worked.
5. Give the temporary password to the user through a separate, approved channel.

## Verification
The user can sign in with the temporary password. Test it yourself by signing in as that user on a workstation, or ask the user to try.

## What was tested in the lab
- As a HelpDesk member on KSW10, SetPassword on James Smith succeeded.
- The same call against the built-in Administrator account failed with "Access is denied (E_ACCESSDENIED)", which is the expected result and confirms the delegation is limited.
- "net user jsmith <password> /domain" run from the same session returned "System error 5, Access is denied", even though the right was granted and the LDAP method worked. The likely reason is that net user uses an older remote protocol that Windows restricts for non-admin users. Use the LDAP method above, or Active Directory Users and Computers, instead.

## Common problems
- **"The value provided for the new password does not meet the length, complexity, or history requirements of the domain":** the new password failed the policy. Use a longer one with uppercase, lowercase, a number, and a symbol, and make sure it does not contain part of the user's name or a previous password.
- **"Access is denied" on a standard user:** check that the user is in the KSLab Users OU, that you are in the HelpDesk group (sign out and back in after a membership change), and that the account is not a protected admin account.

## Escalate if
The account is a privileged or admin account, the user reports they did not request the reset, or the reset fails for a standard user whose account is in the correct OU.
