import os
import sys
import pickle
import hashlib
from shutil import make_archive, copyfile


PANORAMA_DLL = {
    # Legacy version of CS:GO
    "cd469787211a122125faa44138263b62" : 1308935,
    "41e8682aa02de3b7fe275dc1f2187439" : -1
}


def file_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_path(path: str):
    path = path.split("\\")[:-1]

    tmp = ""
    for directory in path:
        try:
            os.mkdir(tmp + directory)
        except FileExistsError:
            pass
        tmp += directory + '\\'


def pk_header(header: bytes):
    pk = {}

    pk["signature"]         = header[0: ][:4]
    pk["version"]           = header[4: ][:2]
    pk["gpflag"]            = header[6: ][:2]
    pk["compression"]       = header[8: ][:2]
    pk["last_mod_time"]     = header[10:][:2]
    pk["last_mod_date"]     = header[12:][:2]
    pk["crc32"]             = header[14:][:4]
    pk["comp_size"]         = int.from_bytes(header[18:][:4], byteorder="little")
    pk["uncomp_size"]       = int.from_bytes(header[22:][:4], byteorder="little")
    pk["filename_length"]   = int.from_bytes(header[26:][:2], byteorder="little")

    return pk


def pbin_unpack(file_name: str):
    """
        Unpack all packed panorama files
            file_name = path to .pbin file
        Return codes:
            0 - no errors
            1 - file doesn't exist
            2 - invalid pbin file
    """

    pbin = {}
    try:
        with open(file_name, "rb") as f:
            pbin["signature"]   = f.read(4)
            pbin["rsa"]         = f.read(512)

            file_table = {}

            if pbin["signature"] == b"\x50\x41\x4e\x02":
                raw_header = b""
                while True:
                    raw_header = f.read(30)
                    pk = pk_header(raw_header)
                    if pk["signature"] == b"\x50\x4b\x03\x04":
                        file = f.read(pk["filename_length"]).decode(encoding="utf-8")

                        print(file)
                        create_path(file)

                        with open(file, "wb") as tmp:
                            tmp.write(f.read(pk["uncomp_size"]))
                            tmp.close()

                        file_table[file] = pk["uncomp_size"]
                    else:
                        break
                file_table["__CODE_PBIN_END__"] = raw_header + f.read()
            else:
                sys.exit(2)

    except FileNotFoundError:
        return 1

    with open("code.pbin.table", "wb") as f:
        pickle.dump(file_table, f)

    return 0


def pbin_pack():
    """
        Pack panorama folder to code.pbin
        Return codes:
            0 - no errors
            1 - code.pbin.table not found (unpack original code.pbin first)
            2 - modified file larger than original
    """

    output_file_content = b""
    output_file_content += b"\x50\x41\x4E\x02"
    output_file_content += b'\x00' * 512

    try:
        with open("code.pbin.table", "rb") as f:
            file_table = pickle.load(f)
    except FileNotFoundError:
        return 1

    for root, dirs, files in os.walk("panorama"):
        for file in files:
            file_name = os.path.join(root, file).replace("/", "\\")
            file_size = os.stat(file_name).st_size

            if file_name not in file_table:
                print(f"{file_name} : Unknown file")
                continue

            file_original_size = file_table[file_name]

            output_file_content += b"\x50\x4B\x03\x04\x0A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x82\xC2\xA9\x51"
            output_file_content += file_original_size.to_bytes(4, byteorder="little")
            output_file_content += file_original_size.to_bytes(4, byteorder="little")
            output_file_content += len(file_name).to_bytes(4, byteorder="little")
            output_file_content += file_name.encode("utf-8")

            with open(file_name, "rb") as f:
                output_file_content += f.read()
                if file_size > file_original_size:
                    print(f"{file_name} : {file_size} B > {file_original_size} B")
                    return 2
                output_file_content += b'\x20' * (file_original_size - file_size)

    if "__CODE_PBIN_END__" not in file_table:
        return 1
    output_file_content += file_table["__CODE_PBIN_END__"]

    while True:
        try:
            with open("code.pbin", "wb") as f:
                f.write(output_file_content)
        except PermissionError:
            print("The file is already in use by some program. Close unnecessary programs and try again.")
            input("Press enter to try again... ")
            continue
        break

    return 0


def pbin_patch_panorama():
    """
        Patch panorama.dll
        Return codes:
            0 - no errors
            1 - invalid panorama.dll
            2 - file patched already
            3 - panorama.dll not found
            4 - unknown error
    """

    panorama_file = "../../bin/panorama.dll"
    panorama_backup = panorama_file + ".bak"

    try:
        if not os.path.isfile(panorama_file):
            return 3

        current_md5 = file_md5(panorama_file)

        if current_md5 in PANORAMA_DLL:
            if PANORAMA_DLL[current_md5] == -1:
                return 2
        else:
            return 1

        copyfile(panorama_file, panorama_backup)

        with open(panorama_backup, "rb") as f:
            original = bytearray(f.read())

        with open(panorama_file, "wb") as f:
            pos = PANORAMA_DLL[current_md5]
            f.write(original[:pos] + b'\xEB' + original[pos+1:])
    except:
        copyfile(panorama_backup, panorama_file)
        return 4

    return 0


def pbin_restore_panorama(force=False):
    """
        Restore panorama.dll
        Return codes:
            0 - no errors
            1 - panorama.dll.bak not found
            2 - invalid backup*

        * - can be avoided with force=True
    """

    panorama_file = "../../bin/panorama.dll"
    panorama_backup = panorama_file + ".bak"

    if not os.path.isfile(panorama_backup):
        return 1

    bak_md5 = file_md5(panorama_backup)
    if ((bak_md5 in PANORAMA_DLL) and (PANORAMA_DLL[bak_md5] != -1)) or force == True:
        copyfile(panorama_backup, panorama_file)
        return 0
    else:
        return 2


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "unpack":
            if len(sys.argv) > 2:
                pbin_name = sys.argv[2]
                code = pbin_unpack(pbin_name)

                match code:
                    case 1:
                        print("File doesn't exist.")

                    case 2:
                        print("Invalid pbin file.")

                sys.exit(code)
            else:
                print(f"Usage: {sys.argv[0]} unpack <pbin file>")
                sys.exit(1)

        elif sys.argv[1] == "pack":
            code = pbin_pack()

            match code:
                case 1:
                    print("'code.pbin.table' not found. Maybe you should unpack your original code.pbin first?")

                case 2:
                    print(f"The modified file size is larger than the original one.")

            sys.exit(code)

        elif sys.argv[1] == "patch_panorama":
            code = pbin_patch_panorama()

            match code:
                case 1:
                    print("Invalid panorama.dll.")

                case 2:
                    print("Your panorama.dll patched already!")
                    sys.exit(0)

                case 3:
                    print("panorama.dll not found!")

                case 4:
                    print("Unknown error, original panorama.dll restored.")

            sys.exit(code)

        elif sys.argv[1] == "restore_panorama":
            code = pbin_restore_panorama()

            match code:
                case 1:
                    print("panorama.dll.bak not found!")

                case 2:
                    print("The backup is incorrect. Are you sure you want to restore panorama.dll?")
                    if input("(y/N): ").lower().startswith('y'):
                        code = pbin_restore_panorama(force=True)

            sys.exit(code)

        else:
            print(f"Unknown function '{sys.argv[1]}'")
            sys.exit(1)
    else:
        print(f"Usage: {sys.argv[0]} unpack/pack/patch_panorama/restore_panorama")
        sys.exit(1)

