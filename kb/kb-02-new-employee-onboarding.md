# KB-02: Onboard a new employee on a Linux server (and offboard)

**Applies to:** Ubuntu Server 24.04 (ksserver, ksserver2)
**Audience:** Help desk and junior sysadmins
**Requires:** an admin account with sudo, the employee's group, and their SSH public key

## Onboarding steps
Run on each server the employee needs. Example uses the help desk group.

1. Create the group once, if it does not exist.
   ```
   sudo groupadd helpdesk
   ```
2. Create the account with a home directory, shell, group, and full name.
   ```
   sudo useradd -m -s /bin/bash -G helpdesk -c "Full Name" <username>
   ```
3. Set a temporary password and force a change at first login.
   ```
   sudo passwd <username>
   sudo chage -d 0 <username>
   ```
4. Install the employee's SSH public key. Password login over SSH is disabled, so this step is required for remote access.
   ```
   sudo mkdir -p /home/<username>/.ssh
   echo '<public key>' | sudo tee -a /home/<username>/.ssh/authorized_keys
   sudo chown -R <username>:<username> /home/<username>/.ssh
   sudo chmod 700 /home/<username>/.ssh
   sudo chmod 600 /home/<username>/.ssh/authorized_keys
   ```
5. Grant only the access the role needs. For the help desk group, the rule allows checking and restarting SSH and nothing else. Always validate a sudoers file before installing it, because a broken file can lock everyone out of sudo.
   ```
   echo '%helpdesk ALL=(root) /usr/bin/systemctl is-active ssh, /usr/bin/systemctl restart ssh' > ~/helpdesk.tmp
   sudo visudo -cf ~/helpdesk.tmp
   sudo install -m 440 -o root -g root ~/helpdesk.tmp /etc/sudoers.d/helpdesk
   rm ~/helpdesk.tmp
   ```

## Verification
```
id <username>
sudo chage -l <username> | head -3
sudo -l -U <username>
```
`id` lists the correct group, `chage` shows the password must be changed at next login, and `sudo -l -U` lists only the permitted commands. A disallowed command (for example `sudo apt update`) should be refused.

## Offboarding steps
1. Lock the account and expire it immediately.
   ```
   sudo usermod -L <username>
   sudo chage -E 0 <username>
   ```
2. Remove their SSH key from `/home/<username>/.ssh/authorized_keys`.
3. Remove them from privileged groups, then archive or delete the home directory according to policy.

## Notes
- Sudo matches commands exactly, including arguments. "systemctl status ssh --no-pager" does not match a rule for "systemctl status ssh".
- The help desk rule uses "is-active" instead of "status" because "status" can open a pager that runs as root.
