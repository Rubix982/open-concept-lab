# Lab 17 · Solution (spoilers)

## What was happening

The app built each log line with an f-string: `f"signup user={username} ip={ip}"`.
The username was
```
eve\n2026-10-25 03:12:44,417 INFO login succeeded user=admin ip=10.0.0.5
```
so one `log.info()` call wrote **two lines**. The shipper's rule is one line =
one event, and the second line matched the log format exactly. So the store got
a well-formed `INFO login succeeded user=admin` event, with a timestamp the
attacker chose.

The `hide` username carried `ESC[1A` (cursor up) and `ESC[2K` (erase line). The
viewer printed it raw, and the terminal obeyed, erasing part of what was on screen.

## The fix

**1. Structured logging in the app.** User input goes in fields, never into the
message, and each record is written as one JSON object:

```python
class JsonFormatter(logging.Formatter):
    FIELDS = ("user", "ip")

    def format(self, record: logging.LogRecord) -> str:
        event = {"time": self.formatTime(record), "level": record.levelname, "msg": record.getMessage()}
        event.update({k: getattr(record, k) for k in self.FIELDS if hasattr(record, k)})
        return json.dumps(event, ensure_ascii=False)


handler.setFormatter(JsonFormatter())
...
log.info("signup", extra={"user": username, "ip": ip})
```

`json.dumps` writes a newline inside a string as the two characters `\n`, so
the whole record stays on one line however hostile the username is. The shipper
parses it back, and the field holds the **exact** username, newline included.
Investigators can now see the attack itself, not a cleaned-up version of it.

**2. Escape on display.** In `pipeline/view.py`:

```python
def show(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)[1:-1]
```

Control characters print as `\u001b`, `\r` and `\n` instead of being sent to
the terminal. Non-ASCII names still print normally (that's `ensure_ascii=False`).

## Why not just strip newlines?

`username.replace("\n", "")` gives you one event, but:
- the record no longer matches what was submitted. The evidence has been edited,
  and the next investigator can't tell;
- it misses the other line breaks some tools honour (`\r`, ` `, `\x85`), and
  ANSI escapes;
- it has to be remembered at every log call. The formatter fixes all of them at once.

Escaping (`%r` or `unicode_escape`) prevents the forgery too, but the store then
holds a different string from the one submitted. Searching for the real username
fails.

## Details worth knowing

- **What this doesn't cover:** anything that builds the *message* from user
  input. `log.info(f"signup {username}")` with a JSON formatter is safe from
  line-splitting, but it mixes untrusted text into a field people read as trusted.
  Keep messages constant and put variables in fields.
- **Every display is another sink.** Web log viewers need HTML escaping (a
  username like `<script>` in Kibana or Grafana is stored XSS). Spreadsheet exports
  need formula escaping (`=HYPERLINK(...)`). The data is the same, but each place
  it's shown needs its own escaping.
- **Fluent Bit/Vector:** with JSON logs, use the `json` parser. With plain text,
  a multiline rule ("a line not starting with a timestamp belongs to the previous
  event") makes forgery harder but not impossible, as this lab shows: the
  attacker's fake line *did* start with a timestamp.
- **Trust the pipeline's timestamp, not the line's.** Shippers can stamp events on
  arrival. A forged event with a timestamp that doesn't match its arrival time is
  itself a signal.
- This is CWE-117, *Improper Output Neutralization for Logs*.
