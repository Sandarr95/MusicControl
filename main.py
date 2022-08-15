import subprocess
import os
import sys

SP_DEST = "org.mpris.MediaPlayer2.spotify"

MP_PATH = "/org/mpris/MediaPlayer2"
MP_MEMB = "org.mpris.MediaPlayer2.Player"
PROP_PATH = "org.freedesktop.DBus.Properties.Get"

class Plugin:
    player = SP_DEST

    def _sp_dbus(self, command, parameters):
        env = os.environ.copy()
        env["DBUS_SESSION_BUS_ADDRESS"] = 'unix:path=/run/user/1000/bus'
        return subprocess.Popen(f"dbus-send --print-reply --dest={self.player} {MP_PATH} {MP_MEMB}.{command} \
            {parameters} > /dev/null", stdout=subprocess.PIPE, shell=True, env=env, universal_newlines=True).communicate()[0]

    async def _sp_open(self, uri):
        return self._sp_dbus(self, "OpenUri", f"string:{uri}")

    async def sp_play(self):
        return self._sp_dbus(self, "PlayPause", "")

    async def sp_pause(self):
        return self._sp_dbus(self, "Pause", "")
    
    async def sp_next(self):
        return self._sp_dbus(self, "Next", "")

    async def sp_previous(self):
        return self._sp_dbus(self, "Previous", "")

    async def sp_seek(self, amount):
        return self._sp_dbus(self, "Seek", f"int64:\"{amount}\"")

    async def sp_set_position(self, position : int, trackid : str):
        return self._sp_dbus(self, "SetPosition", f"objpath:\"{trackid}\" int64:\"{position}\"")

    async def sp_track_status(self):
        env = os.environ.copy()
        env["DBUS_SESSION_BUS_ADDRESS"] = 'unix:path=/run/user/1000/bus'
        result =  subprocess.Popen(f"dbus-send --print-reply --dest={self.player} {MP_PATH} {PROP_PATH} \
            string:\"{MP_MEMB}\" string:'PlaybackStatus' \
            | tail -1 \
            | cut -d \"\\\"\" -f2" \
            ,stdout=subprocess.PIPE, shell=True, env=env, universal_newlines=True).communicate()[0]
        print(result)
        sys.stdout.flush()
        return result

    async def sp_track_progress(self):
        env = os.environ.copy()
        env["DBUS_SESSION_BUS_ADDRESS"] = 'unix:path=/run/user/1000/bus'
        result = subprocess.Popen(f"dbus-send --print-reply --dest={self.player} {MP_PATH} {PROP_PATH} \
            string:\"{MP_MEMB}\" string:'Position' \
            | tail -1 \
            | rev | cut -d' ' -f 1 | rev" \
            , stdout=subprocess.PIPE, shell=True, env=env, universal_newlines=True).communicate()[0]
        return result

    async def get_meta_data(self):
        env = os.environ.copy()
        env["DBUS_SESSION_BUS_ADDRESS"] = 'unix:path=/run/user/1000/bus'
        try:
            result = subprocess.Popen(f"dbus-send --print-reply --dest={self.player} {MP_PATH} {PROP_PATH} \
                string:\"{MP_MEMB}\" string:'Metadata' \
                | grep -Ev \"^method\"                           `# Ignore the first line.`   \
                | grep -Eo '(\"(.*)\")|(\\b[0-9][a-zA-Z0-9.]*\\b)' `# Filter interesting fiels.`\
                | sed -E '2~2 a|'                              `# Mark odd fields.`         \
                | tr -d '\n'                                   `# Remove all newlines.`     \
                | sed -E 's/\\|/\\n/g'                           `# Restore newlines.`        \
                | sed -E 's/(xesam:)|(mpris:)//'               `# Remove ns prefixes.`      \
                | sed -E 's/^\"//'                              `# Strip leading...`         \
                | sed -E 's/\"$//'                              `# ...and trailing quotes.`  \
                | sed -E 's/\"+/|/'                             `# Regard "" as seperator.`  \
                | sed -E 's/ +/ /g'                            `# Merge consecutive spaces.`",  
                stdout=subprocess.PIPE, shell=True, env=env, universal_newlines=True).communicate()[0]
        except:
            result = "Unavailable"
        return result

    async def sp_list_media_players(self):
        env = os.environ.copy()
        env["DBUS_SESSION_BUS_ADDRESS"] = 'unix:path=/run/user/1000/bus'
        
        result = subprocess.Popen(f"dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames",
        stdout=subprocess.PIPE, shell=True, env=env, universal_newlines=True).communicate()[0]
        stripped = result.split('array [')[1].split(']')[0].replace("\n", "", 1).replace("\n", ",") \
            .replace(" ", "").replace("string", "").replace("\"", "").rstrip(',')
        services = stripped.split(',')
        
        mediaPlayers = []
        for service in services:
            if service.find('org.mpris.MediaPlayer2') != -1:
                mediaPlayers.append(service)
        
        servicesString = ""
        mediaPlayerCount = len(mediaPlayers)
        for i in range(mediaPlayerCount):
            servicesString = servicesString.join(mediaPlayers[i])
            if i < mediaPlayerCount - 1:
                servicesString = servicesString.join(',')
        
        print(servicesString)
        sys.stdout.flush()
        return servicesString
    
    async def sp_set_media_player(self, player : str):
        self.player = player

    async def sp_get_media_player(self):
        return self.player

    async def _main(self):
        self.player = SP_DEST
        pass