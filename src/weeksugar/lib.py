import io
import pathlib
import re

sums_path = pathlib.Path("/tmp/md5.txt")

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


def main():
    dups = {}
    for line in sums_path.read_text().splitlines():
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
