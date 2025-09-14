# SMBClient CLI Tools

- [SMBClient CLI Tools](#smbclient-cli-tools)
  - [Connect to SMB Share - Basic Connection \& Authentication](#connect-to-smb-share---basic-connection--authentication)
    - [Connect to share](#connect-to-share)
    - [Connect with specific domain](#connect-with-specific-domain)
    - [Connect with password in command (not secure)](#connect-with-password-in-command-not-secure)
    - [Connect anonymously](#connect-anonymously)
    - [Interactive Commands (Once Connected)](#interactive-commands-once-connected)
    - [Navigation \& Listing](#navigation--listing)
    - [File Operations](#file-operations)
    - [Advanced Operations](#advanced-operations)
  - [Non-Interactive (Scripting) Mode](#non-interactive-scripting-mode)
    - [List Files](#list-files)
      - [List share contents](#list-share-contents)
      - [List specific directory](#list-specific-directory)
  - [Download Files](#download-files)
    - [Download single file](#download-single-file)
    - [Download to specific location](#download-to-specific-location)
    - [Download all files in directory](#download-all-files-in-directory)
  - [Upload Files](#upload-files)
    - [Upload single file](#upload-single-file)
    - [Upload to specific directory](#upload-to-specific-directory)
    - [Upload multiple files](#upload-multiple-files)
  - [Discovery \& Information](#discovery--information)
    - [List Shares on Server](#list-shares-on-server)
      - [List available shares](#list-available-shares)
      - [List shares anonymously](#list-shares-anonymously)
      - [List with specific port](#list-with-specific-port)
  - [Server Information](#server-information)
    - [Get server info](#get-server-info)
    - [Check server version](#check-server-version)
  - [Authentication Options](#authentication-options)
    - [Password Methods](#password-methods)
      - [Interactive password prompt](#interactive-password-prompt)
      - [Password file](#password-file)
      - [Environment variable](#environment-variable)
  - [Kerberos Authentication](#kerberos-authentication)
    - [Use Kerberos ticket](#use-kerberos-ticket)
    - [Specify realm](#specify-realm)
  - [Advanced Options](#advanced-options)
    - [Performance \& Behavior](#performance--behavior)
      - [Specify SMB protocol version](#specify-smb-protocol-version)
      - [Set timeout](#set-timeout)
      - [Debug level (0-10)](#debug-level-0-10)
      - [Use specific port](#use-specific-port)
  - [Scripting Example](#scripting-example)
    - [Download all files from today](#download-all-files-from-today)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
      - [Connection refused](#connection-refused)
      - [Authentication failed](#authentication-failed)
      - [Permission denied](#permission-denied)
      - [Timeout issues](#timeout-issues)
  - [Testing Connectivity](#testing-connectivity)
    - [Test if server is reachable](#test-if-server-is-reachable)
    - [Test SMB port](#test-smb-port)
    - [Check SMB shares](#check-smb-shares)

## Connect to SMB Share - Basic Connection & Authentication

### Connect to share

```sh
smbclient //server/share -U username
```

### Connect with specific domain

```sh
smbclient //server/share -U domain\\username
```

### Connect with password in command (not secure)

```sh
smbclient //server/share -U username%password
```

### Connect anonymously

```sh
smbclient //server/share -N
```

### Interactive Commands (Once Connected)

### Navigation & Listing

```sh
smb: \> ls                    # List files in current directory
smb: \> cd folder             # Change directory
smb: \> pwd                   # Print working directory
smb: \> dir                   # Alternative to ls
```

### File Operations

```sh
smb: \> get filename          # Download file
smb: \> put localfile         # Upload file
smb: \> mget pattern          # Download multiple files (wildcards)
smb: \> mput pattern          # Upload multiple files
smb: \> del filename          # Delete file
smb: \> mkdir foldername      # Create directory
smb: \> rmdir foldername      # Remove directory
```

### Advanced Operations

```sh
smb: \> lcd /local/path       # Change local directory
smb: \> !ls                   # Execute local shell command
smb: \> prompt                # Toggle prompting for mget/mput
smb: \> recurse               # Toggle recursive directory operations
smb: \> tar c backup.tar      # Create tar archive of remote files
```

## Non-Interactive (Scripting) Mode

### List Files

#### List share contents

```sh
smbclient //server/share -U username -c "ls"
```

#### List specific directory

```sh
smbclient //server/share -U username -c "cd folder; ls"
```

## Download Files

### Download single file

```sh
smbclient //server/share -U username -c "get file.txt"
```

### Download to specific location

```sh
smbclient //server/share -U username -c "lcd /local/path; get file.txt"
```

### Download all files in directory

```sh
smbclient //server/share -U username -c "prompt; recurse; mget *"
```

## Upload Files

### Upload single file

```sh
smbclient //server/share -U username -c "put localfile.txt"
```

### Upload to specific directory

```sh
smbclient //server/share -U username -c "cd remote/folder; put localfile.txt"
```

### Upload multiple files

```sh
smbclient //server/share -U username -c "prompt; mput *.txt"
```

## Discovery & Information

### List Shares on Server

#### List available shares

```sh
smbclient -L //server -U username
```

#### List shares anonymously

```sh
smbclient -L //server -N
```

#### List with specific port

```sh
smbclient -L //server -p 445 -U username
```

## Server Information

### Get server info

```sh
smbclient //server/IPC$ -U username -c "help"
```

### Check server version

```sh
nmblookup -A server_ip
```

## Authentication Options

### Password Methods

#### Interactive password prompt

```sh
smbclient //server/share -U username
```

#### Password file

```sh
echo "password" > ~/.smbpass
chmod 600 ~/.smbpass
smbclient //server/share -U username -A ~/.smbpass
```

#### Environment variable

```sh
export PASSWD=mypassword
smbclient //server/share -U username
```

## Kerberos Authentication

### Use Kerberos ticket

```sh
kinit <username@DOMAIN.COM>
smbclient //server/share -k
```

### Specify realm

```sh
smbclient //server/share -U username@REALM -k
```

## Advanced Options

### Performance & Behavior

#### Specify SMB protocol version

```sh
smbclient //server/share -U username --option='client min protocol=SMB2'
```

#### Set timeout

```sh
smbclient //server/share -U username -t 30
```

#### Debug level (0-10)

```sh
smbclient //server/share -U username -d 3
```

#### Use specific port

```sh
smbclient //server/share -U username -p 139
```

## Scripting Example

```sh
# !/bin/bash
SERVER="//fileserver/backup"
USERNAME="backupuser"
SHARE_PATH="/remote/backups"
LOCAL_PATH="/local/backups"
```

### Download all files from today

```sh
smbclient $SERVER -U $USERNAME -c "
    cd $SHARE_PATH
    lcd $LOCAL_PATH
    prompt
    recurse
    mget $(date +%Y-%m-%d)*
    quit
"
```

## Troubleshooting

### Common Issues

#### Connection refused

```sh
smbclient //server/share -U username --option='client min protocol=SMB1'
```

#### Authentication failed

```sh
smbclient //server/share -U domain\\username
```

#### Permission denied

```sh
smbclient //server/share -U username --option='client use spnego=no'
```

#### Timeout issues

```sh
smbclient //server/share -U username -t 60
```

## Testing Connectivity

### Test if server is reachable

```sh
ping server
```

### Test SMB port

```sh
telnet server 445
```

### Check SMB shares

```sh
showmount -e server  # For NFS, but similar concept
```
