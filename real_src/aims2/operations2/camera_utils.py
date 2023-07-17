from fabric import Connection

def read_reefscan_id_for_ip(camera_ip):
    try:
        conn = Connection(
            "jetson@" + camera_ip,
            connect_kwargs={"password": "jetson"}
        )

        r = conn.run("cat ~/reefscan_id.txt", hide=True)
        reefscan_id = r.stdout
        return reefscan_id
    except:
        return "REEFSCAN"


def delete_archives(camera_ip):
    archive_folder = "/media/jetson/*/images/archive"
    conn = Connection(
        "jetson@" + camera_ip,
        connect_kwargs={"password": "jetson"}
    )
    conn.run("rm -r " + archive_folder, hide=True)


def get_kilo_bytes_used(camera_ip, command):
    conn = Connection(
        "jetson@" + camera_ip,
        connect_kwargs={"password": "jetson"}
    )
    result = conn.run(command, hide=True)
    return int(result.stdout.split()[0])
