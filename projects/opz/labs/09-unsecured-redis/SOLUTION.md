# Lab 09 · Solution (spoilers)

## What was wrong

- `ports: "6309:6379"` publishes Redis on **every** interface of the host
  (`0.0.0.0`). The app never needed it: it reaches Redis as `redis:6379` on the
  compose network. The published port was only ever for an attacker (or a
  developer's convenience).
- No password. Redis's protected mode would refuse remote clients in that case,
  but the official Docker image starts Redis with protected mode **off**,
  because otherwise other containers couldn't connect. So anyone who reached the
  port got full access.
- Full access includes `CONFIG SET dir/dbfilename` + `SAVE`, which writes a file
  of your choosing onto the server. That's how "open Redis" becomes "server taken over".

## The fix: three layers

**1. Network: don't publish the port.** Delete `ports:` from the redis service.
The app still reaches it over the compose network. If you need `redis-cli` while
developing, use `docker compose exec redis redis-cli`, or publish to
`127.0.0.1:6309:6379` only. That's reachable from your laptop but not from the network.

**2. Authentication, with ACLs.** `users.acl`:

```
user default off
user app on #<sha256 of the password> ~* &* +@all -@dangerous
```

- `user default off` disables the anonymous user entirely.
- `#<sha256>` stores a hash, so reading the ACL file doesn't reveal the password.
  Make it with `printf '<password>' | shasum -a 256`.
- `~* &*` = all keys and channels. `+@all -@dangerous` = every command except
  the dangerous category (`CONFIG`, `FLUSHALL`, `DEBUG`, `KEYS`, `SHUTDOWN`…).

**3. Wire it up** in `compose.yaml`:

```yaml
services:
  app:
    environment:
      REDIS_HOST: redis
      REDIS_PORT: "6379"
      REDIS_USERNAME: app
      REDIS_PASSWORD_FILE: /run/secrets/redis_password
    secrets:
      - redis_password
    ...
  redis:
    image: redis:7.4-alpine
    container_name: opz-lab09-redis
    # no ports:
    command: ["redis-server", "--appendonly", "no", "--aclfile", "/etc/redis/users.acl"]
    volumes:
      - ./users.acl:/etc/redis/users.acl:ro

secrets:
  redis_password:
    file: ./redis_password.txt     # FAKE value; in real life, not in git
```

Check the last layer by hand:

```bash
docker run --rm --network opz-lab09_default redis:7.4-alpine \
  redis-cli -h opz-lab09-redis --user app --pass <password> CONFIG SET dir /tmp
# NOPERM User app has no permissions to run the 'config|set' command
```

## Details worth knowing

- **`--requirepass` works too**, but it puts the password in the process's
  arguments (`docker inspect`, `ps`), and it's one shared password with every
  permission. ACLs give you named users, hashed passwords and per-command limits.
- **Docker publishing bypasses host firewalls.** On Linux, Docker writes its own
  iptables rules, so a published port can be open even if `ufw` says it's
  closed. Not publishing is the reliable control.
- **What this doesn't cover:** encryption. Redis traffic is plaintext, so anyone
  on the network path can read the password and the data. Redis supports TLS
  (`--tls-port`); managed Redis enforces it. Also: back up, because "attacker ran
  FLUSHALL" is a data-loss incident, not just a security one.
