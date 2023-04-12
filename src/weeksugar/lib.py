import io
import logging
import pathlib
import re

_logger = logging.getLogger(__name__)

md5_manifest = pathlib.Path("/tmp/md5.txt")


msg_md5_manifest_missing = io.StringIO()
msg_md5_manifest_missing.write(
    f"oops, can't find {md5_manifest}, for now you should do this first:\n"
)
msg_md5_manifest_missing.write(
    "find DIRECTORY_PATH -type f -print0 | xargs -0 md5sum >{md5_manifest}\n"
)
msg_md5_manifest_missing.write("\n")
msg_md5_manifest_missing.write("will fix this later\n")


pat = re.compile(
    r"""
    (?P<md5sum>^[a-f0-9]{32})
    \s+
    (?P<path>.*)""",
    re.VERBOSE,
)


def write_bash(md5: str, vfile, to_delete: list[str], all: list[str]):
    vfile.write(f"# these are duplicates with md5 {md5}\n")
    for path in all:
        vfile.write(f"# {path}\n")

    vfile.write("# from those, I propose to keep one and delete the rest:\n")
    for path in to_delete:
        vfile.write(f'rm -f "{path}"\n')
        vfile.write("\n")


def main() -> str:
    if not md5_manifest.exists():
        _logger.critical(msg_md5_manifest_missing.getvalue())
        return ""

    dups = {}
    for line in md5_manifest.read_text().splitlines():
        mo = pat.search(line)
        md5 = mo.group("md5sum")
        path = mo.group("path")
        dups.setdefault(md5, []).append(path)

    # only consider md5s that have multiple paths
    md5s = list(filter(lambda md5: len(dups[md5]) > 1, dups.keys()))

    dups2 = {}
    for md5 in md5s:
        # save one file from the list:
        delete_candidates = dups[md5].copy()
        delete_candidates.pop()

        dups2[md5] = {
            "all_paths": dups[md5],
            "delete_candidates": delete_candidates,
        }

    bash = io.StringIO()
    for md5 in dups2.keys():
        write_bash(
            md5,
            bash,
            to_delete=dups2[md5]["delete_candidates"],
            all=dups2[md5]["all_paths"],
        )

    bash.write(f"# {len(dups2.keys())} duplicates found\n")
    return bash.getvalue()


if __name__ == "__main__":
    bash = main()
    print(bash)
