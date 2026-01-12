# pomodoro-linux

<code>
sudo apt update
sudo apt install python3 python3-pip pulseaudio-utils alsa-utils -y

python3 -m venv venv
source venv/bin/activate

pip3 install PyQt6 qtawesome
pip install pyinstaller
python3 pomodoro.py
</code>

To Install:
<code>
pyinstaller   --onefile   --windowed   --name pomodoro   pomodoro.py
</code>

To Run:
<code>
./run_pomodoro.sh
</code>
