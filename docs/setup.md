# Setup

## Windows

Install Python 3.10/3.11 and Wireshark. During Wireshark installation include tshark and Npcap/loopback support.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
tshark -D
```

If activation is blocked, use `Set-ExecutionPolicy -Scope Process Bypass`. Select the Npcap loopback interface shown by `tshark -D`; never assume its number.

## Linux

```bash
sudo apt install python3-venv tshark
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
chmod +x scripts/*.sh
tshark -D
```

Your distribution may require adding the user to a Wireshark group or granting dumpcap capabilities. The simulator needs no physical PLC, Raspberry Pi, or ESP32. It binds to localhost by default. To use privileged port 502, change all matching configuration deliberately and provide the required OS privileges.
