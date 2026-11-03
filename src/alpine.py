"""Read Alpine APKINDEX metadata using only the Python standard library."""

import io
import re
import tarfile
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


INDEX_FILENAME = "APKINDEX.tar.gz"
DEP_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9+_.-]*)")


def index_url(repository):
    """Resolve a repository directory or an APKINDEX archive URL."""
    if repository.rstrip("/").endswith(INDEX_FILENAME):
        return repository
    return repository.rstrip("/") + "/" + INDEX_FILENAME


def parse_index(content):
    """Convert APKINDEX paragraphs into a package-to-dependencies map."""
    result = {}
    for block in content.split("\n\n"):
        record = {}
        for line in block.splitlines():
            if len(line) >= 2 and line[1] == ":":
                record[line[0]] = line[2:]
        name = record.get("P")
        if not name:
            continue
        dependencies = []
        for item in record.get("D", "").split():
            if item.startswith(("so:", "cmd:", "pc:", "!")):
                continue
            match = DEP_NAME.match(item)
            if match:
                dependencies.append(match.group(1))
        result[name] = sorted(set(dependencies))
    return result


def read_apkindex(repository):
    """Download and unpack the Alpine package index without apk."""
    url = index_url(repository)
    try:
        with urlopen(url, timeout=15) as response:
            archive = response.read()
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            member = tar.extractfile(INDEX_FILENAME)
            if member is None:
                raise ValueError("APKINDEX.tar.gz has no APKINDEX file.")
            text = member.read().decode("utf-8")
    except (HTTPError, URLError, OSError, tarfile.TarError) as error:
        raise ValueError(f"Could not read Alpine repository: {error}") from error
    return parse_index(text)


def direct_dependencies(index, package):
    """Return direct dependencies, or explain a missing package."""
    if package not in index:
        raise ValueError(f"Package not found in repository: {package}")
    return index[package]
