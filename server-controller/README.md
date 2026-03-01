# Server Controller

Discord bot (or HTTP server) that manages a Minecraft server. Supports three deployment strategies:

- **local** — manages the MC server via Docker Compose on the same host
- **ec2** — launches a spot fleet instance on AWS to run the MC server
- **k8s** — creates a pod in a Kubernetes cluster

## Project Layout

```
server-controller/
├── bot/src/          # Application source
├── tests/            # Tests
└── etc/              # Dockerfiles, compose, scripts, deploy configs
```

## Building

Run from the `server-controller/` directory:

```bash
./etc/build.sh <deploy-strategy> <starter>
```

| Arg | Values |
|-----|--------|
| `deploy-strategy` | `local`, `ec2`, `k8s` |
| `starter` | `discord`, `http` |

Example: `./etc/build.sh ec2 discord` builds image `mc-server-controller:ec2-discord`.

## Running

### Environment Variables

**All strategies:**

| Variable | Required | Description |
|----------|----------|-------------|
| `DEPLOYMENT` | Set by build | `local`, `aws_ec2`, or `kubernetes` |
| `DISCORD_API_TOKEN` | Yes (discord) | Discord bot token |
| `DISCORD_API_TOKEN_FILE` | Alt | Path to file containing the token |
| `SERVER_ADDRESS` | Yes | Address shown to users |
| `SERVER_STATUS_HOST` | No | Host to query for MC status (defaults to `SERVER_ADDRESS`) |
| `SERVER_PORT_JAVA` | No | Java edition port (default `25565`) |
| `SERVER_PORT_BEDROCK` | No | Bedrock edition port (default `19132`) |
| `LOG_LEVEL` | No | `debug`, `info`, `warning`, `error` (default `info`) |
| `DUCK_DNS_DOMAIN` | No | DuckDNS domain for dynamic DNS |
| `DUCK_DNS_TOKEN` | No | DuckDNS token |

### Local

Manages the MC server via Docker Compose on the same machine. Requires the Docker socket and a compose file mounted into the container.

Additional env vars:
- `MC_SERVER_CONTAINER_NAME` — compose project name for the MC server

Volumes:
- `/var/run/docker.sock` — Docker socket
- MC server `compose.yaml` mounted to `/data/compose.yaml`

Quick start with compose: `./etc/compose-up.sh` (edit `etc/compose-prod.yaml` first).

### EC2

Launches an AWS spot fleet instance to run the MC server.

Additional env vars:
- `AWS_SERVER_TAG` — tag to identify the MC server instance
- `AWS_REGION` — AWS region
- `AWS_LAUNCH_TEMPLATE_NAME` — launch template for the spot fleet

Requires AWS credentials (IAM role or env vars). See `etc/aws/` for IAM policies and launch template examples.

To deploy the image to an EC2 host: `./etc/push-remote.sh <ssh-key> <host>`.

### Kubernetes

Creates a Minecraft server pod in a Kubernetes cluster.

Additional env vars:
- `KUBERNETES_POD_TEMPLATE_PATH` — path to pod template JSON (default `/config/pod-template.json`)

Requires a ServiceAccount with pod create/delete/get/list permissions. See `etc/example/` for example deployment configs.
