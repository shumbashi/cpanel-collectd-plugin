# cPanel Collectd Plugin

[Collectd](https://collectd.org/) plugin to gather metrics from a [cPanel](https://cpanel.net/) server, written in Python..

## Collected Metrics

| Type | Name | Description | Status |
| --- | --- | --- | --- |
| Gauge | active_users | Number of active cPanel user account | Done |
| Gauge | suspended_users | Number of suspended cPanel user accounts | Done |
| Gauge | domains_configured | Number of total domains configured, main , subdomains, and aliases on the server| TBD |
| Counter Vector | version | cPanel version number | TBD |
| Gauge Vector | plans | Number of accounts per plan | TBD |
| Gauge Vector | bandwidth | Bandwidth consumed per user account | TBD |
| Gauge Vector | quota_percent | Percentage of quota used per user account | TBD |
| Gauge Vector | quota_used | Amount of quota used per user account | TBD |
| Gauge | emails_configured | Number of total email accounts configured on the server | TBD |
| Gauge | ftp_accounts | Number of total FTP accounts configured on the server | TBD |
| Gauge | sessions_email | Number of active Webmail login sessions | TBD |
| Gauge | sessions_web | Number of active cPanel login sessions | TBD |

## Why

Previously we were using [Prometheus](https://prometheus.io/) with (cpanel-exporter)[https://github.com/shumbashi/cpanel_exporter] to collect and visulaize the above metrics. The original exporter was written in GoLang. This plugin is an attempt to mimic the same metrics in a Python based plugin for Collectd.

## Requirements

*TBD*