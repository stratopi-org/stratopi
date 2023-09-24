# Highlight.io

Ship _systemd_ service logs to [Highlight.io](https://www.highlight.io/).

## Install OpenTelemetry

```shell
cd /tmp
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.85.0/otelcol-contrib_0.85.0_linux_arm64.deb
sudo dpkg -i otelcol-contrib_0.85.0_linux_arm64.deb
```

## OpenTelemetry configuration

```yaml
receivers:
  journald:
    directory: /var/log/journal
    units:
      - stratopi-battery
      - stratopi-location
      - stratopi-environmental
    priority: info
exporters:
    otlp/highlight:
        endpoint: 'https://otel.highlight.io:4317'
processors:
    attributes/highlight-project:
        actions:
            - key: highlight.project_id
              value: 'project-id-here'
              action: insert
    batch:
service:
    pipelines:
        logs:
            receivers: [journald]
            processors: [attributes/highlight-project, batch]
            exporters: [otlp/highlight]
```

```shell
sudo mv /tmp/config.yaml /etc/otelcol-contrib/config.yaml
sudo chown root:root /etc/otelcol-contrib/config.yaml
sudo usermod -aG systemd-journal otelcol-contrib
sudo service otelcol-contrib restart
```
