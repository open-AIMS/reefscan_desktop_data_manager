from fabric import Connection
import logging
logger = logging.getLogger("")
def read_reefscan_id_for_ip(camera_ip, username="jetson"):
    try:
        conn = Connection(
            username + "@" + camera_ip,
            connect_kwargs={"password": ("%s" % username)}
        )

        r = conn.run("cat ~/reefscan_id.txt", hide=True)
        reefscan_id = r.stdout
        return reefscan_id
    except:
        return "REEFSCAN"


def delete_archives(camera_ip, username="jetson"):
    archive_folder = "/media/%s/*/images/archive" % username
    conn = Connection(
        username + "@" + camera_ip,
        connect_kwargs={"password": ("%s" % username)}
    )
    conn.run("rm -r " + archive_folder, hide=True)


def get_kilo_bytes_used(camera_ip, command, username="jetson"):
    conn = Connection(
        username + "@" + camera_ip,
        connect_kwargs={"password": ("%s" % username)}
    )
    result = conn.run(command, hide=True)
    return int(result.stdout.split()[0])
