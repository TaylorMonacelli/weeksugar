import io
import logging
import pathlib
import re

_logger = logging.getLogger(__name__)


def manifest_missing_message(path: str) -> str:
    msg_md5_manifest_missing = io.StringIO()
    msg_md5_manifest_missing.write(
        f"oops, can't find {path}, for now you should do this first:\n"
    )
    msg_md5_manifest_missing.write(
        f"find DIRECTORY_PATH -type f -print0 | xargs -0 md5sum >{path}\n"
    )
    msg_md5_manifest_missing.write("\n")
    msg_md5_manifest_missing.write("will fix this later\n")

    return msg_md5_manifest_missing.getvalue()


pat = re.compile(
    r"""
    (?P<md5sum>^[a-f0-9]{32})
    \s+
    (?P<path>.*)""",
    re.VERBOSE,
)


def write_bash(md5: str, bash, to_delete: list[str], all: list[str]):
    bash.write("#!/usr/bin/env bash\n")
    bash.write("\n")
    bash.write(f"# {len(to_delete):,d} duplicates found\n")

    bash.write(f"# these are duplicates with md5 {md5}\n")
    for path in all:
        bash.write(f"# {path}\n")

    bash.write("# from those, I propose to keep one and delete the rest:\n")
    for path in to_delete:
        bash.write(f'rm -f "{path}"\n')
        bash.write("\n")


def main(manifest_path: str) -> str:
    manifest_path = pathlib.Path(manifest_path)
    if not manifest_path.exists():
        _logger.critical(manifest_missing_message(manifest_path))
        return ""

    dups = {}
    for line in manifest_path.read_text().splitlines():
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
