#! /bin/sh
#
# Usage: ./tools/run_fake_zeitgeist.sh <additional Zeitgeist arguments>
#
# This script sets up a bus in a fake X server (Xvfb) and launches
# a Zeitgeist instance (without datahub or FTS) into it.
#
# It then spawns a terminal set up to interact with that instance.
# When the terminal is closed (Ctrl+D), the Zeitgeist instance and
# bus are terminated.

if [ ! -x ./src/zeitgeist-daemon ]; then
    echo "Please run in root directory."
    exit 1
fi

r=`python -c "import random; print random.randint(20, 100)"`
export DISPLAY=":$r"

Xvfb ":$r" -screen 0 "1024x768x8" >/dev/null 2>&1 &
pid=$!

eval `dbus-launch --sh-syntax`

dir=`mktemp -d --tmpdir "zeitgeist.fake.XXXX"`

echo "Launching Zeitgeist with data directory $dir"

ZEITGEIST_DISABLED_EXTENSIONS=SearchEngine \
    ZEITGEIST_DATA_PATH="$dir" \
    ./src/zeitgeist-daemon --no-datahub --log-level=debug \
    --log-file="$dir/zeitgeist.log" $* &
pid_zg=$!

# Create setup script
cat >$dir/setup.sh <<EOF
export DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS
export DISPLAY=$DISPLAY
export PS1="zeitgeist>> "
EOF
chmod +x $dir/setup.sh

echo "Spawning shell..."

eval $SHELL

echo "Bye!"
kill $pid_zg
kill $pid

echo "Zeitgeist database left at $dir..."
