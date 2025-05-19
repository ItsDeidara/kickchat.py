# Kicktools Fusion Chat API Reader

This module provides a robust Python API and CLI tool for reading and parsing chat messages from the [kicktools.app Fusion Chat overlay](https://kicktools.app/fusion_chat) for [kick.com](https://kick.com) streams. It uses Selenium to automate browser interaction and extract chat data in real time.

---

## Features

- **Automated Chat Parsing:** Reads messages from the Fusion Chat overlay in real time.
- **Timestamp, Username, and Message Extraction:** Captures and normalizes all key chat fields.
- **Robust Error Handling:** Handles missing elements, network issues, and browser errors gracefully.
- **Threaded Operation:** Runs parsing in a background thread for responsive shutdown.
- **Graceful Shutdown:** Supports stopping via Ctrl+C or by creating a `stop.txt` file.
- **JSON Output:** Saves parsed messages to a JSON file (`chat_messages.json`).
- **Configurable via CLI:** Pass the Fusion Chat URL as a command-line argument.

---

## Requirements

- Python 3.8+
- [Selenium](https://pypi.org/project/selenium/)
- [pytz](https://pypi.org/project/pytz/)
- Chrome browser
- [ChromeDriver](https://chromedriver.chromium.org/) (must be in your PATH)

Install dependencies using [Rye](https://github.com/astral-sh/rye):

```bash
rye sync
```

Or with pip:

```bash
pip install -r requirements.txt
```

---

## Usage

### CLI

```bash
python kickchat.py <fusion_chat_url>
```

**Example:**

```bash
python kickchat.py "https://kicktools.app/fusion_chat/fusion-chat.html?kick=<kick_channel>&twitch=&font=Inter&fontSize=Large&fontShadow=shadow-na&fontColor=%23ffffff&theme=basic&fontCase=none&timestamp=on&userBadges=on&fadeTime=1"
```

> **Note:** You can generate a custom Fusion Chat overlay URL at [kicktools.app/fusion_chat](https://kicktools.app/fusion_chat). Replace `<kick_channel>` with your own Kick.com channel name. For more details, see the [Fusion Chat overlay generator](https://kicktools.app/fusion_chat/fusion-chat.html).

- The script will start parsing chat messages and save them to `chat_messages.json` in the current directory.
- To stop the script, press `Ctrl+C` or create a file named `stop.txt` in the same directory.

---

## Configuration

- **Fusion Chat URL:** Must start with `http://` or `https://` and contain `kicktools.app/fusion_chat`.
- **Output File:** By default, messages are saved to `chat_messages.json`. You can modify this in the code or extend the script to accept an output file argument.
- **Timezone:** Timestamps are normalized to America/New_York (EDT).

---

## Development & Structure

- **Source:** [`kickchat.py`](./kickchat.py)
- **Key Functions:**
  - `setup_driver()`: Configures Selenium Chrome driver.
  - `parse_chat(url, output_file)`: Main parsing loop.
  - `convert_timestamp(raw_timestamp)`: Normalizes timestamps.
  - `validate_url(url)`: Ensures URL is valid for Fusion Chat.
  - `signal_handler(sig, frame)`: Handles graceful shutdown.
  - `check_stop_file()`: Monitors for `stop.txt` to trigger shutdown.
- **Threading:** Parsing runs in a background thread; main thread monitors for stop signal.
- **Error Handling:** All major operations are wrapped in try/except blocks with informative logging.

---

## Integration Examples

You can use the chat parser as a standalone script or import its logic into your own Python project.

### 1. Import and Run Programmatically

Suppose you want to trigger chat parsing from your own code and process the results:

```python
from custom_apis import kickchat

# Replace with your own Fusion Chat URL
your_url = "https://kicktools.app/fusion_chat/fusion-chat.html?kick=<kick_channel>&twitch=&font=Inter&fontSize=Large&fontShadow=shadow-na&fontColor=%23ffffff&theme=basic&fontCase=none&timestamp=on&userBadges=on&fadeTime=1"

# Optionally, specify a custom output file
output_file = "my_chat_messages.json"

# Start parsing (runs until stopped)
kickchat.parse_chat(your_url, output_file=output_file)

# After parsing, load and process the messages
import json
with open(output_file, "r", encoding="utf-8") as f:
    messages = json.load(f)

for msg in messages:
    print(f"[{msg['timestamp']}] {msg['username']}: {msg['message']}")
```

### 2. Using as a Subprocess

You can also run the script as a subprocess from another Python script:

```python
import subprocess

url = "https://kicktools.app/fusion_chat/fusion-chat.html?kick=<kick_channel>&twitch=&font=Inter&fontSize=Large&fontShadow=shadow-na&fontColor=%23ffffff&theme=basic&fontCase=none&timestamp=on&userBadges=on&fadeTime=1"
subprocess.run(["python", "src/custom_apis/kickchat.py", url])
```

---

## Example Terminal Output

```
Chat container found
[30068:45748:0518/224832.836:ERROR:components\device_event_log\device_event_log_impl.cc:202] [22:48:32.837] USB: usb_service_win.cc:105 SetupDiGetDeviceProperty({{A45C254E-DF1C-4EFD-8020-67D146A850E0}, 6}) failed: Element not found. (0x490)
[30068:45748:0518/224832.838:ERROR:services\device\usb\usb_descriptors.cc:146] Failed to read length for configuration 1.
[30068:45748:0518/224832.838:ERROR:services\device\usb\usb_descriptors.cc:146] Failed to read length for configuration 2.
[30068:45748:0518/224832.838:ERROR:services\device\usb\usb_descriptors.cc:105] Failed to read all configuration descriptors. Expected 3, got 1.
[30068:45748:0518/224832.838:ERROR:components\device_event_log\device_event_log_impl.cc:202] [22:48:32.839] USB: usb_device_win.cc:95 Failed to read descriptors from \\?\usb#vid_0b95&pid_1790#00c58da5#{a5dcbf10-6530-11d2-901f-00c04fb951ed}.
Raw HTML: <span class="timestamp">10:48</span><span class="badges" data-platform="kick"><img id="platform-badge" class="logo-kick" src="assets/logo-kick.png" alt="Kick Logo"><img src="assets/broadcaster.svg" cl...
Raw timestamp: '10:48'
Raw username: 'fixingKicksSite'
Raw message: 'message1'
Parsed: {'timestamp': '10:48 AM', 'username': 'fixingKicksSite', 'message': 'message1'}
Created TensorFlow Lite XNNPACK delegate for CPU.
Attempting to use a delegate that only supports static-sized tensors with a graph that has dynamic-sized tensors (tensor#-1 is a dynamic-sized tensor).
```

> **Note:** Some USB or TensorFlow errors may appear in the output if your environment has related hardware or drivers. These do not affect chat parsing.

---

