# Docker Rsync with Tailscale Integration

**This is a fork and enhanced version of [insrch/rsync](https://hub.docker.com/r/insrch/rsync)**

Dockerhub page: https://hub.docker.com/r/insrch/rsync

## Overview

This project is an enhanced version of the original `insrch/rsync` Docker image, now featuring Tailscale integration, a web management interface, and JSON-based route configuration. The change was made for self-hosted remote backup solutions requiring secure access and multi-route backup capabilities.

**Key Enhancements:**
- 🔗 **Tailscale VPN Integration** - Secure networking for remote backups
- 🌐 **Web Management Interface** - Monitor logs and trigger syncs via browser
- 📄 **JSON Route Configuration** - Define multiple backup routes in a single file
- 🔒 **Enhanced SSH Security** - Improved connection handling and error reporting
- 📊 **Real-time Monitoring** - Live sync progress and detailed logging
- 🎯 **Multi-route Support** - Backup multiple directories in one operation

Instead of syncing a single remote directory, this version allows you to define multiple local-to-remote backup routes using a JSON configuration file, all accessible through a user-friendly web interface.

## Features

- **Tailscale VPN Integration** - Secure, encrypted connections to remote servers
- **Web Management Interface** - Monitor sync status and logs via browser (port 2222)
- **JSON Route Configuration** - Define multiple backup routes in `/config/backup_routes.json`
- **Real-time Logging** - Detailed sync progress and error reporting
- **Manual Sync Triggers** - Start backups on-demand through web interface
- **Enhanced SSH Security** - Automatic host key verification bypass for VPN environments
- **Multi-route Processing** - Backup multiple directories in a single operation
- **Lightweight Alpine Base** - Minimal resource usage with essential tools (rsync, jq, python3)
- **File Locking** - Prevents concurrent sync operations

## Installation

### Docker Compose Setup (Recommended)

Edit `docker-compose.yaml` with your specific values:

```yaml
services:
  tailscale: 
    container_name: tailscale-backup
    hostname: your-hostname  # Change to your desired hostname
    image: tailscale/tailscale:stable 
    ports:
      - "2222:80"  # Web interface port
    environment:
      - TS_AUTHKEY=your_tailscale_auth_key_here  # Get from Tailscale admin console
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_USERSPACE=false
    volumes: 
      - ./config/tailscale/state:/var/lib/tailscale
      - ./config/tailscale/config:/config
    cap_add:
      - net_admin
      - sys_module
    devices:
      - /dev/net/tun:/dev/net/tun
    restart: unless-stopped
    networks:
      backup:
        ipv4_address: 192.168.6.10

  rsync-backup:
    container_name: rsync-backup
    build:
      context: .
      dockerfile: build/Dockerfile
    volumes:
      - ./config:/config  # Config and logs directory
      - ~/.ssh:/mnt/ssh_keys:ro  # SSH keys (read-only)
      - /path/to/your/data1:/data/source1  # Local data to backup
      - /path/to/your/data2:/data/source2  # More local data
    restart: unless-stopped
    network_mode: service:tailscale
    depends_on:
      - tailscale
    environment:
      - REMOTE_USER=your_remote_username  # SSH username on remote server
      - REMOTE_HOST=100.x.x.x  # Tailscale IP of remote server
      - CRON_SCHEDULE=30 2 * * 1  # Weekly on Monday at 2:30 AM
      - SSH_KEY_FILE=id_rsa  # SSH key filename in ~/.ssh/
      - TZ=Europe/Madrid  # Your timezone
      - ROUTES_FILE=/src/backup_routes.json
    
networks:
  backup:
    ipam:
      config:
        - subnet: 192.168.6.0/24
```

### JSON Routes Configuration

Edit `src/backup_routes.json` (maps local paths to remote destinations):

```json
{
  "/data/source1/documents": "/mnt/backup/documents",
  "/data/source1/photos": "/mnt/backup/photos",
  "/data/source2/projects": "/mnt/backup/projects"
}
```

## Environment Variables

| Variable        | Description                                           | Example Value           | Required |
| --------------- | ----------------------------------------------------- | ----------------------- | -------- |
| `TS_AUTHKEY`    | Tailscale authentication key                         | `tskey-auth-xxx...`     | Yes      |
| `REMOTE_USER`   | SSH username on remote server                        | `your_remote_username`  | Yes      |
| `REMOTE_HOST`   | Remote server Tailscale IP address                   | `100.x.x.x`            | Yes      |
| `ROUTES_FILE`   | Path to JSON file defining backup routes             | `/src/backup_routes.json` | Yes      |
| `CRON_SCHEDULE` | Cron expression for automated sync schedule          | `30 2 * * 1` (weekly)   | Yes      |
| `SSH_KEY_FILE`  | SSH private key filename                              | `id_rsa`               | Yes      |
| `TZ`            | Timezone for container                                | `Europe/Madrid`         | No       |

### Getting Started

1. **Get Tailscale Auth Key**: Visit [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys) to generate an auth key
2. **Setup SSH Keys**: Ensure your SSH public key is authorized on the remote server
3. **Configure Routes**: Create `src/backup_routes.json` with your backup mappings  
4. **Update Variables**: Edit `docker-compose.yaml` with your specific values
5. **Start Services**: Run `docker-compose up --build -d`

## Web Interface

Access the web management interface at `http://your_host:2222`

Features:
- 📊 **Real-time Sync Logs** - Monitor backup progress and errors
- ▶️ **Manual Sync Trigger** - Start backups on-demand
- 🔄 **Auto-refresh** - Live updates every 30 seconds
- 📄 **Log Management** - Clear logs when needed
- 💾 **System Status** - View load average and log file sizes

## Usage Examples

### SSH Key Setup

1. Generate SSH key pair on your local machine:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/backup_key
```

2. Copy public key to remote server:
```bash
ssh-copy-id -i ~/.ssh/backup_key.pub user@remote_host
```

3. Place the private key in your config directory as `id_rsa`

### Directory Structure

```
your_project/
├── docker-compose.example.yaml  # Template configuration
├── docker-compose.yaml          # Your actual configuration (gitignored)
├── build/
│   ├── Dockerfile
│   └── entrypoint.sh
├── src/
│   ├── backup_routes.json       # Your backup route mappings
│   ├── sync_script.sh
│   └── web_server.py
└── config/
    ├── logs/                    # Sync and web server logs
    │   ├── sync.log
    │   └── web_server.log
    └── tailscale/
        ├── state/               # Tailscale connection state
        └── config/
```

### Volume Mapping Examples

Update the volumes in `docker-compose.yaml` to match your setup:

```yaml
volumes:
  # Configuration and logs (required)
  - ./config:/config
  
  # SSH keys (required, read-only)
  - ~/.ssh:/mnt/ssh_keys:ro
  
  # Your local data to backup (customize these paths)
  - /home/user/Documents:/data/documents
  - /home/user/Pictures:/data/pictures
  - /media/external-drive:/data/external
  - /var/lib/docker/volumes:/data/docker-volumes
```

## Troubleshooting

### SSH Connection Issues

Check SSH connection manually:
```bash
docker exec -it rsync-backup ssh -i /.ssh/id_rsa user@tailscale_ip
```

### Web Interface Not Accessible

Verify port mapping and container status:
```bash
docker logs rsync-backup
curl http://localhost:2222
```

### JSON Configuration Errors

Validate your routes file:
```bash
docker exec -it rsync-backup jq empty /config/backup_routes.json
```

### View Detailed Logs

Check sync and web server logs:
```bash
docker exec -it rsync-backup tail -f /config/logs/sync.log
```

### Manual Sync Testing

Run sync manually for testing:
```bash
docker exec -it rsync-backup /bin/bash /src/sync_script.sh
```

## Acknowledgments

This enhanced version was developed with the assistance of **GitHub Copilot** with Claude Sonnet 4 Agent.

## Contributing

If you would like to contribute, feel free to submit a pull request or open an issue on GitHub.
