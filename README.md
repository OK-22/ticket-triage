# Monitoring Homelab: Prometheus, Grafana, and Alerts

Monitoring for two Ubuntu lab servers (ksserver and ksserver2) using Prometheus, Grafana, and node_exporter. The agents are installed with an Ansible playbook, the stack runs in Docker on ksserver, and three alert rules were tested with a planned outage.

## What is in here
- `docker-compose.yml`: Prometheus and Grafana, with ports bound to localhost and reached through an SSH tunnel
- `prometheus.yml`: scrape configuration for both servers and the alert rules file
- `alerts.yml`: three rules (InstanceDown, HighCPU, LowDiskSpace)
- `monitoring.yml`: Ansible playbook that installs and enables node_exporter on both servers
- `runbook.md`: what each alert means and how to respond
- `postmortem.md`: mock postmortem for a planned ksserver2 outage
- `docs/images/`: screenshots from the test

## How it works
1. `ansible-playbook monitoring.yml -K` installs `prometheus-node-exporter` on both servers.
2. `sudo docker compose up -d` starts Prometheus and Grafana on ksserver.
3. An SSH tunnel (`ssh -L 3000:localhost:3000 -L 9090:localhost:9090 ksserver`) exposes the two web pages on the workstation without opening ports on the network.
4. Grafana uses Prometheus as its data source (`http://prometheus:9090`) and shows the community Node Exporter Full dashboard (imported, not built here).

## Results of the practice outage
ksserver2 was shut down on purpose to test InstanceDown.

| Stage | Evidence |
|---|---|
| Target down | `docs/images/targets-down.png` shows 1 / 2 up and the error "no route to host" |
| Alert pending | `docs/images/alert-pending.png` (active for 48.9 seconds) |
| Alert firing | `docs/images/alert-firing.png` (active for 1 minute 4 seconds) |
| Recovery | `docs/images/targets-up.png` shows 2 / 2 up |

The server then froze during boot and needed a hard reset, so recovery took about 30 minutes. The details, timeline, and lessons are in `postmortem.md`.

![Target down](docs/images/targets-down.png)
![Alert pending](docs/images/alert-pending.png)
![Alert firing](docs/images/alert-firing.png)
![Target up again](docs/images/targets-up.png)

## Limits
- Alerts are visible in Prometheus only. Notification delivery (Alertmanager) is not configured.
- The Grafana dashboard is a community template.
- This is a small lab on virtual machines, not a production design.
