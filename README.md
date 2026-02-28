# aws-ec2-mcserver
Utilizing AWS EC2 Spot Fleet to reduce cost and host a modded Minecraft server.

# Navigating folder structure
This project has separate folders that contain scripts, service files and python files.

* /discordbot contains files for running the discord bot and the aws boto3 api calls.
* /scripts contains scripts that are run via service files and utility scripts for downloading packages.
* /services contains service files to run minecraft, to check the player connections and to save the world file.

# About this repo
This repository contains files that can be used to run a Minecraft server on AWS EC2, using AWS boto3 to make Spot Fleet requests.
The server automatically shuts down by checking if players are connected every 30 minutes.
The server automatically checks for instance interruptions as well. 
Either the case, backups are stored on AWS S3.

# Kubernetes Deployment

The Discord bot supports a `KUBERNETES` deployment mode that manages Minecraft server pods via the Kubernetes API instead of Docker Compose or AWS EC2.

## How it works

When a user runs `/server start`, the bot creates a pod running `itzg/minecraft-server:java21` (configurable). The MC server container handles its own lifecycle including autostop on inactivity. The bot monitors server status via mcstatus polling.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT` | `local` | Set to `kubernetes` |
| `KUBERNETES_NAMESPACE` | `default` | Namespace for the MC server pod |
| `KUBERNETES_MC_POD_NAME` | `mc-server` | Name of the MC server pod |
| `KUBERNETES_MC_IMAGE` | `itzg/minecraft-server:java21` | Container image for the MC server |
| `KUBERNETES_MC_CONFIGMAP` | `mc-server-config` | ConfigMap name injected as env vars into the MC server pod |
| `KUBERNETES_MC_PVC` | `mc-server-data` | PVC name mounted at `/data` for world data |
| `SERVER_STATUS_HOST` | — | Set to the K8s Service DNS name (e.g. `mc-server.minecraft.svc`) |

## Prerequisites

- The bot pod's **service account must have RBAC permissions** to `get`, `create`, and `delete` pods in the target namespace.
- A **PersistentVolumeClaim** for MC world data must exist in the target namespace.
- A **ConfigMap** with MC server settings (e.g. `EULA=TRUE`, `ENABLE_AUTOSTOP=TRUE`) must exist in the target namespace.
- A **Service** exposing port 25565 for the MC server pod so `SERVER_STATUS_HOST` can resolve.

## Building the image

```bash
docker build -f discordbot/Dockerfile.k8s -t discord-mc-bot:latest discordbot/
```
