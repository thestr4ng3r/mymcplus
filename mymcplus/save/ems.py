
from . import ps2save
from .. import ps2mc_dir
from .utils import *
from ..round import round_up

def load(save, f):
    """Load EMS (.psu) save files."""

    cluster_size = 1024

    dirent = ps2save.unpack_dirent(read_fixed(f, ps2mc_dir.PS2MC_DIRENT_LENGTH))
    dotent = ps2save.unpack_dirent(read_fixed(f, ps2mc_dir.PS2MC_DIRENT_LENGTH))
    dotdotent = ps2save.unpack_dirent(read_fixed(f, ps2mc_dir.PS2MC_DIRENT_LENGTH))
    if (not ps2save.mode_is_dir(dirent[0])
            or not ps2save.mode_is_dir(dotent[0])
            or not ps2save.mode_is_dir(dotdotent[0])
            or dirent[2] < 2):
        raise ps2save.Corrupt("Not a EMS (.psu) save file.", f)

    dirent[2] -= 2
    save.set_directory(dirent)

    for i in range(dirent[2]):
        ent = ps2mc_dir.unpack_dirent(read_fixed(f, ps2mc_dir.PS2MC_DIRENT_LENGTH))
        if not ps2mc_dir.mode_is_file(ent[0]):
            raise ps2save.Subdir(f)
        flen = ent[2]
        save.set_file(i, ent, read_fixed(f, flen))
        read_fixed(f, round_up(flen, cluster_size) - flen)


def save(save, f):
    cluster_size = 1024

    dirent = save.dirent[:]
    dirent[2] += 2
    f.write(ps2mc_dir.pack_dirent(dirent))
    f.write(ps2mc_dir.pack_dirent((ps2mc_dir.DF_RWX | ps2mc_dir.DF_DIR | ps2mc_dir.DF_0400 | ps2mc_dir.DF_EXISTS,
                                   0, 0, dirent[3],
                                   0, 0, dirent[3], 0, b".")))
    f.write(ps2mc_dir.pack_dirent((ps2mc_dir.DF_RWX | ps2mc_dir.DF_DIR | ps2mc_dir.DF_0400 | ps2mc_dir.DF_EXISTS,
                                   0, 0, dirent[3],
                                   0, 0, dirent[3], 0, b"..")))

    for i in range(dirent[2] - 2):
        (ent, data) = save.get_file(i)
        f.write(ps2mc_dir.pack_dirent(ent))
        if not ps2mc_dir.mode_is_file(ent[0]):
            # print ent
            # print hex(ent[0])
            raise ps2save.Error("Directory has a subdirectory.")
        f.write(data)
        f.write(b"\0" * (round_up(len(data), cluster_size) - len(data)))
    f.flush()



