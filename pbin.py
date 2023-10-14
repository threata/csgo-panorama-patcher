import os
import sys
import pickle
import hashlib
from shutil import make_archive, copyfile


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

    pbin = {
        "signature": b"",
        "rsa": b""
    }

    try:
        with open(file_name, "rb") as f:
            # First of all, let's check PAN signature
            pbin["signature"]   = f.read(4)
            pbin["rsa"]         = f.read(512)

            file_table = {}

            if pbin["signature"] == b"\x50\x41\x4e\x02":
                while True:
                    pk = pk_header(f.read(30))
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

            else:
                f.close()
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
            file_original_size = file_table[file_name]

            output_file_content += b"\x50\x4B\x03\x04\x0A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x82\xC2\xA9\x51"
            output_file_content += file_table[file_name].to_bytes(4, byteorder="little")
            output_file_content += file_table[file_name].to_bytes(4, byteorder="little")
            output_file_content += len(file_name).to_bytes(4, byteorder="little")
            output_file_content += file_name.encode("utf-8")

            with open(file_name, "rb") as f:
                output_file_content += f.read()
                if file_size > file_original_size:
                    print(f"{file_name} : {file_size} B > {file_table[file_name]} B")
                    return 2
                output_file_content += b'\x20' * (file_original_size - file_size)

    with open("code.pbin.end", "rb") as f:
        output_file_content += f.read()

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
    """

    MD5_ORIGINAL = "cd469787211a122125faa44138263b62"
    MD5_PATCHED  = "41e8682aa02de3b7fe275dc1f2187439"

    copyfile("../../bin/panorama.dll", "../../bin/panorama.dll.bak")

    try:
        current_md5 = file_md5("../../bin/panorama.dll.bak")

        if current_md5 == MD5_ORIGINAL:
            pass
        elif current_md5 == MD5_PATCHED:
            return 2
        else:
            return 1

        with open("../../bin/panorama.dll.bak", "rb") as f:
            original = bytearray(f.read())

        with open("../../bin/panorama.dll", "wb") as f:
            modified = original[:1308935] + b'\xEB' + original[1308935+1:]
            f.write(modified)
    except:
        print("Something bad happened! Idk what, just let me restore your panorama.dll?")
        copyfile("../../bin/panorama.dll.bak", "../../bin/panorama.dll")

    return 0


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
                    print("Invalid panorama.dll. Are you sure that you are using latest CS:GO build?")
                case 2:
                    print("Your panorama.dll patched already!")
                    sys.exit(0)

            sys.exit(code)

        else:
            print(f"Unknown function '{sys.argv[1]}'")
            sys.exit(1)
    else:
        print(f"Usage: {sys.argv[0]} unpack/pack/patch_panorama")
        sys.exit(1)
