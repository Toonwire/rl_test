import re
import subprocess
import sys
from subprocess import check_output
from subprocess import PIPE
from subprocess import Popen
import git
import logging

# NOTE: Parts and their values must match the ones configured in `.bumpversion.cfg`
PART__RELEASE = "release"
PART__BUILD = "build"
RELEASE__RELEASE_CANDIDATE = "rc"

# extra part only used by bump_version wrapper function
PART__PRE_RELEASE = "prerelease"

# single point of reference for remote
REMOTE = "origin"

logger = logging.getLogger()


def main():
    bump_ok = bump_version()
    if bump_ok:
        postversion()


def bump_version():
    """Wrapper for `bump2version` with a prerelease part extension for creating release candidates as a new patch.\\
    The prerelease part runs bump2version with a new-version equal to bumping release and patch parts.\\
    When bumping an already release candidate, only the build part is incremented.

    Returns:
        bool: Whether the version bump succeeded

    Example: (using version = 5.3.2)
        `python bump_version.py prerelease`
            5.3.2 \u2192 5.3.3-rc.0
        `python bump_version.py prerelease`
            5.3.3-rc.0 \u2192 5.3.3-rc.1
    """
    cmd_args = sys.argv[1:]
    out = check_output(("bump2version", "--dry-run", "--list", "patch"))
    decoded = out.decode("ascii")
    lines = decoded.splitlines()
    current_is_rc = False
    major = 0
    minor = 0
    patch = 0
    release = RELEASE__RELEASE_CANDIDATE
    build = 0
    for l in lines:
        if l.startswith("new_version"):
            base_matches = re.findall(r"=(\d+)\.(\d+)\.(\d+)$", l)
            if base_matches:
                major, minor, patch = base_matches[0]
                new_patch = str(int(patch) + 1)
                patch = new_patch
                break

            rc_matches = re.findall(r"=(\d+)\.(\d+)\.(\d+)-([a-z]+)\.(\d+)$", l)
            if rc_matches:
                major, minor, patch, release, build = rc_matches[0]
                if release == RELEASE__RELEASE_CANDIDATE:
                    current_is_rc = True
                    new_build = str(int(build) + 1)
                    build = new_build
                else:
                    current_is_rc = False
                    release = RELEASE__RELEASE_CANDIDATE
                    build = 0

                break

    if PART__PRE_RELEASE in cmd_args:
        cmd_args = ["--new-version", f"{major}.{minor}.{patch}-{release}.{build}"] + cmd_args

    elif current_is_rc and PART__BUILD not in cmd_args:
        # warn about deviating from release flow
        if PART__RELEASE not in cmd_args:
            print(
                "\033[93mCurrent version is marked as a release candidate and must be bumped as a either a build or release for targeted version. "
                "Run command with part 'release' to bump as release.\033[0m"
            )
            return False

        cmd_args = ["--new-version", f"{major}.{minor}.{patch}"] + cmd_args

    completed_process = subprocess.run(["bump2version"] + cmd_args, capture_output=True)

    if completed_process.returncode != 0:
        print(
            f"Failed to bump version: {completed_process.stdout.decode('ascii')} {completed_process.stderr.decode('ascii')}"
        )
        return False

    print(completed_process.stderr.decode("ascii"))
    print(completed_process.stdout.decode("ascii"))

    return True


def postversion():
    """Runs additional Git commands associated with the version bump.

    If the new version release part matches the release candidate string
    - Creates a release candidate branch and push it to remote.
    - Pushes the new version tag to remote.

    If the new version release part is the release string
    - Merges the release candidate back into 'dev'
    - Creates a release branch and push it to remote.
    - Pushes the new version tag to remote.
    """
    # load version after bump
    from __version__ import __version__

    # ##########################
    # # GET TAG INFO FROM GIT
    # ##########################
    # latest_tag_cmd = Popen(["git", "describe", "--exact-match", "--abbrev=0"], stdout=PIPE)
    # stdout = latest_tag_cmd.communicate()[0]
    # latest_tag = stdout.decode("ascii").strip()  # remove newline from decoded bytes

    # # sorted_tags_cmd = Popen(["git", "tag", "--sort=creatordate"], stdout=PIPE)
    # # tail_cmd = Popen(["tail", "-2"], stdin=sorted_tags_cmd.stdout, stdout=PIPE)
    # # head_cmd = Popen(["head", "-1"], stdin=tail_cmd.stdout, stdout=PIPE)

    # p = Popen("git tag --sort=creatordate | tail -2 | head -1", shell=True, stdout=PIPE)

    # stdout, stderr = p.communicate()

    # print(stdout.decode("ascii").strip())  # remove newline from decoded bytes
    # # print(stdout.decode("ascii").strip())  # remove newline from decoded bytes

    # # if sorted_tags_cmd.stdout:
    # #     sorted_tags_cmd.stdout.close()  # allow sorted_tags_cmd to receive a SIGPIPE if prev_tag_cmd exits.

    # # if tail_cmd.stdout:
    # #     tail_cmd.stdout.close()  # allow tail_cmd to receive a SIGPIPE if head_cmd exits.

    # # stdout = head_cmd.communicate()[0]
    # prev_tag = stdout.decode("ascii").strip()  # remove newline from decoded bytes

    r = git.Repo(".")


    latest_tag = r.git.describe("--abbrev=0")
    prev_tag = r.git.describe("--abbrev=0", latest_tag+"^")

    print(latest_tag)
    print(prev_tag)

    # ##########################
    # # CREATE RELEASE CANDIDATE
    # ##########################
    # # check for release candidate version (-rc), e.g. 5.0.24-rc.0

    # if re.match(r"^\d+\.\d+\.\d+-rc\.\d+$", __version__):
    #     print(f"Creating candidate branch candidate/{latest_tag}")
    #     completed_process = subprocess.run(["git", "checkout", "-b", f"candidate/{latest_tag}"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print(f"Pushing candidate branch candidate/{latest_tag} to remote")
    #     completed_process = subprocess.run(["git", "push", REMOTE, f"candidate/{latest_tag}"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print(f"Pushing candidate tag {latest_tag} to remote")
    #     completed_process = subprocess.run(["git", "push", REMOTE, latest_tag], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    if re.match(r"^\d+\.\d+\.\d+-rc\.\d+$", __version__):
        print(f"Creating candidate branch candidate/{latest_tag}")
        print("----------------------------------------------------------")
        # out = r.git.checkout("-b", f"candidate/{latest_tag}")
        # out = r.create_head(f"candidate/{latest_tag}", extended_output=True)
        cmd = f"git checkout -b candidate/{latest_tag}"
        status, stdout, stderr = r.git.execute(cmd.split(" "), with_extended_output=True)
        print(stdout)
        print(stderr)
        if status != 0:
            raise Exception("Failed to create candidate branch")


        print("----------------------------------------------------------")
        print("----------------------------------------------------------\n")
        print(f"Pushing candidate branch candidate/{latest_tag} to remote")
        print("----------------------------------------------------------")
        cmd = f"git push {REMOTE} candidate/{latest_tag}"
        status, stdout, stderr = r.git.execute(cmd.split(" "), with_extended_output=True)
        print(stdout)
        print(stderr)
        if status != 0:
            raise Exception("Failed to create candidate branch")


        print("----------------------------------------------------------")
        print("----------------------------------------------------------\n")
        print(f"Pushing candidate tag {latest_tag} to remote")
        print("----------------------------------------------------------")
        cmd = f"git push {REMOTE} {latest_tag}"
        status, stdout, stderr = r.git.execute(cmd.split(" "), with_extended_output=True)
        print(stdout)
        print(stderr)
        if status != 0:
            raise Exception("Failed to create candidate branch")





    # ##########################
    # # CREATE RELEASE
    # ##########################
    # # check for stable release version, e.g. 5.0.24

    # elif re.match(r"^\d+\.\d+\.\d+$", __version__):
    #     print(f"Creating release branch release/{latest_tag}")
    #     completed_process = subprocess.run(["git", "checkout", "-b", f"release/{latest_tag}"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print(f"Pushing release branch release/{latest_tag} to remote")
    #     completed_process = subprocess.run(["git", "push", REMOTE, f"release/{latest_tag}"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print(f"Pushing release tag {latest_tag} to remote")
    #     completed_process = subprocess.run(["git", "push", REMOTE, latest_tag], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print("Fetching latest changes from 'master'")
    #     completed_process = subprocess.run(["git", "checkout", "master"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     completed_process = subprocess.run(["git", "pull"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print(f"Merging release/{latest_tag} back into 'master'")
    #     completed_process = subprocess.run(["git", "merge", f"release/{latest_tag}"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print("Pushing release merge to master on remote")
    #     completed_process = subprocess.run(["git", "push", REMOTE, "master"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print("Fetching latest changes from 'dev'")
    #     completed_process = subprocess.run(["git", "checkout", "dev"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     completed_process = subprocess.run(["git", "pull"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print(f"Merging release/{latest_tag} back into 'dev'")
    #     completed_process = subprocess.run(["git", "merge", f"release/{latest_tag}"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))

    #     print("Pushing release merge to dev on remote")
    #     completed_process = subprocess.run(["git", "push", REMOTE, "dev"], capture_output=True)
    #     print(completed_process.stdout.decode("ascii"))
    #     print(completed_process.stderr.decode("ascii"))


if __name__ == "__main__":
    main()
