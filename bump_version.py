import re
import subprocess
import sys
from subprocess import check_output
import logging

# NOTE: Parts and their values must match the ones configured in `.bumpversion.cfg`
PART__RELEASE = "release"
PART__BUILD = "build"
RELEASE__RELEASE_CANDIDATE = "rc"

# extra part only used by bump_version wrapper function
PART__PRE_RELEASE = "prerelease"

# single point of reference for remote
REMOTE = "origin"

# stable branch declarations
MASTER_BRANCH = "master"
DEV_BRANCH = "dev"

logger = logging.getLogger()


def main():
    bump_ok = bump_version()
    # if bump_ok:
    #     postversion()


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
    # load version pre bump
    from __version__ import __version__

    print(f"Current version = {__version__}")

    cmd_args = sys.argv[1:]
    # out = check_output(("bump2version", "--dry-run", "--list", "path"))
    # decoded = out.decode("ascii")
    # lines = decoded.splitlines()
    is_rc = False

    major = 0
    minor = 0
    patch = 0
    release = RELEASE__RELEASE_CANDIDATE
    build = 0
    base_matches = re.findall(r"=(\d+)\.(\d+)\.(\d+)$", __version__)
    if base_matches:
        major, minor, patch = base_matches[0]
        new_patch = str(int(patch) + 1)
        patch = new_patch

    rc_matches = re.findall(r"=(\d+)\.(\d+)\.(\d+)-([a-z]+)\.(\d+)$", __version__)
    if rc_matches:
        major, minor, patch, release, build = rc_matches[0]
        if release == RELEASE__RELEASE_CANDIDATE:
            is_rc = True
            new_build = str(int(build) + 1)
            build = new_build
        else:
            is_rc = False
            release = RELEASE__RELEASE_CANDIDATE
            build = 0

    if PART__PRE_RELEASE in cmd_args:
        cmd_args = [
            "--new-version",
            f"{major}.{minor}.{patch}-{release}.{build}",
        ] + cmd_args

    elif is_rc and PART__BUILD not in cmd_args:
        # warn about deviating from release flow
        if PART__RELEASE not in cmd_args:
            print(
                "\033[93mCurrent version is marked as a release candidate and must be bumped as a either a build or release for targeted version. "
                "Run command with part 'release' to bump as release.\033[0m"
            )
            return False

        cmd_args = ["--new-version", f"{major}.{minor}.{patch}"] + cmd_args

    print(cmd_args)

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
    completed_process = subprocess.run(["git", "describe", "--abbrev=0"], capture_output=True)
    latest_tag = completed_process.stdout.decode("ascii").strip()

    # ##########################
    # # CREATE RELEASE CANDIDATE
    # ##########################
    # # check for release candidate version (-rc), e.g. 5.0.24-rc.0

    if re.match(r"^\d+\.\d+\.\d+-rc\.\d+$", __version__):
        print()
        print("----------------------------------------------------------")
        print(f"Creating candidate branch candidate/{latest_tag}")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "checkout", "-b", f"candidate/{latest_tag}"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Pushing candidate branch candidate/{latest_tag} to remote")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "push", REMOTE, f"candidate/{latest_tag}"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Pushing candidate tag {latest_tag} to remote")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "push", REMOTE, latest_tag], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

    # ##########################
    # # CREATE RELEASE
    # ##########################
    # # check for stable release version, e.g. 5.0.24

    elif re.match(r"^\d+\.\d+\.\d+$", __version__):
        print()
        print("----------------------------------------------------------")
        print(f"Creating release branch release/{latest_tag}")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "checkout", "-b", f"release/{latest_tag}"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Pushing release branch release/{latest_tag} to remote")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "push", REMOTE, f"release/{latest_tag}"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Pushing release tag {latest_tag} to remote")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "push", REMOTE, latest_tag], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Fetching latest changes from '{MASTER_BRANCH}'")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "checkout", "master"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        completed_process = subprocess.run(["git", "pull"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Merging release/{latest_tag} back into '{MASTER_BRANCH}'")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "merge", f"release/{latest_tag}"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Pushing release merge to {MASTER_BRANCH} on remote")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "push", REMOTE, "master"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Fetching latest changes from '{DEV_BRANCH}'")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "checkout", "dev"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        completed_process = subprocess.run(["git", "pull"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Merging release/{latest_tag} back into '{DEV_BRANCH}'")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "merge", f"release/{latest_tag}"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))

        print()
        print("----------------------------------------------------------")
        print(f"Pushing release merge to {DEV_BRANCH} on remote")
        print("----------------------------------------------------------")
        completed_process = subprocess.run(["git", "push", REMOTE, "dev"], capture_output=True)
        print(completed_process.stdout.decode("ascii"))
        print(completed_process.stderr.decode("ascii"))


if __name__ == "__main__":
    main()
