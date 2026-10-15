# KB-03: Troubleshoot an SSH access problem

**Applies to:** Ubuntu Server 24.04 lab servers reached from a Windows host through VirtualBox port forwarding (ksserver on port 2211, ksserver2 on port 2212)
**Audience:** Help desk and junior sysadmins

## First check: are you on the right machine?
Look at the prompt before typing anything.
- `PS C:\Users\...>` is the Windows host. Run `ssh ksserver` here.
- `admink1@ksserver:~$` is inside the server. The forwarded ports (2211, 2212) do not exist here, so `ssh -p 2211 admink1@127.0.0.1` from inside the server always fails with "Connection refused".

## Symptoms and fixes

**"Connection refused"**
1. Check the VM is running: `VBoxManage list runningvms`. If it is missing, start it with `VBoxManage startvm "<name>" --type headless` and wait about 40 seconds.
2. Check the forwarding rules exist: `VBoxManage natnetwork list`. Both ssh rules should appear under the network.
3. On the server console, check SSH is listening: `sudo ss -tlnp | grep :22`.

**"Connection reset" or a blinking cursor that never connects**
The forward answered but the server did not. It is probably still booting or hung.
1. Take a screenshot of the VM console without opening the GUI: `VBoxManage controlvm "<name>" screenshotpng "<path>.png"`.
2. If the screen shows a boot message that does not change between screenshots, hard-reset it: `VBoxManage controlvm "<name>" reset`.
3. Test server to server from a healthy machine: `ping 10.10.10.11`. "Destination Host Unreachable" means the server is not on the network yet.

**"Permission denied (publickey)"**
The server is up but rejected your key. Password login is disabled on purpose.
1. Run `ssh -v ksserver` and look for which key is offered.
2. Check the key is in `~/.ssh/authorized_keys` on the server and that permissions are 700 on `.ssh` and 600 on `authorized_keys`.
3. Remember a key-less login attempt is supposed to fail. That is how the lockdown was verified.

**"REMOTE HOST IDENTIFICATION HAS CHANGED"**
The server's host key no longer matches the saved one, which is expected after a clone or rebuild. Verify that the change is legitimate first, then remove the old entry: `ssh-keygen -R "[127.0.0.1]:2211"`.

**VM will not start ("session was aborted" or "closed before any attempt to power it on")**
Read the VM's log in its Logs folder. In this lab the cause was a VM folder the user could not write to (VERR_ACCESS_DENIED), fixed by granting Modify rights with `icacls` from an elevated shell.

## Escalate if
The server is unreachable after a reset, the VM disk files are missing, or you are asked to restore a snapshot that would undo recent configuration.
