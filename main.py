import json
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote

def get_data(url):
    """Get JSON data from PyPI."""
    try:
        # Open the URL and fetch the response from PyPI
        with urlopen(url, timeout=10) as response:
            # Read the response, convert it to text, and parse the JSON
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as e:
        # Return None if the requested package or version does not exist
        if e.code == 404:
            return None

        # Raise the error again if it is not a 404 error
        raise


def main():
    # Open requirements.txt and read all non-empty lines
    with open("requirements.txt", "r") as file:
        lines = [line.strip() for line in file if line.strip()]

    # Count the dependencies and initialize the counters
    checked = len(lines)
    missing_packages = 0
    missing_versions = 0
    oldest_release = None  # Stores information about the oldest release found

    # Check each dependency in the requirements file
    for line in lines:

        # Skip lines that do not specify a pinned version using ==
        if "==" not in line:
            continue

        # Separate the package name and its required version
        name, version = line.split("==", 1)
        name = name.strip()
        version = version.strip()

        # Create the PyPI API URL to check whether the package exists
        package_url = f"https://pypi.org/pypi/{quote(name, safe='')}/json"

        # Fetch the package information from PyPI
        package_data = get_data(package_url)

        # If the package does not exist, increase the counter and skip it
        if package_data is None:
            missing_packages += 1
            continue

        # Create the PyPI API URL to check the specific version
        version_url = (
            f"https://pypi.org/pypi/"
            f"{quote(name, safe='')}/{quote(version, safe='')}/json"
        )

        # Fetch information about the requested version
        version_data = get_data(version_url)

        # If the package exists but its version does not, count it
        if version_data is None:
            missing_versions += 1
            continue

        # Get the list of files uploaded for this version
        urls = version_data.get("urls", [])

        # Skip this version if no uploaded files are listed
        if not urls:
            continue

        # Get the upload timestamp of the first file listed by the API
        upload_time = urls[0]["upload_time"]

        # Extract the year from the upload timestamp
        year = int(upload_time[:4])

        # Check whether this release is older than the current oldest release
        if oldest_release is None or upload_time < oldest_release["time"]:

            # Store the package name, version, year, and full timestamp
            oldest_release = {
                "name": name,
                "version": version,
                "year": year,
                "time": upload_time
            }

    # Print the total number of dependencies in the file
    print("Dependencies checked:", checked)

    # Print how many package names do not exist on PyPI
    print("Packages not on PyPI:", missing_packages)

    # Print how many pinned versions do not exist on PyPI
    print("Versions not on PyPI:", missing_versions)

    # Print the oldest valid pinned release and its year
    if oldest_release:
        print(
            "Oldest pinned release: "
            f'{oldest_release["name"]}=={oldest_release["version"]} '
            f'({oldest_release["year"]})'
        )
    else:
        # Print this if no valid pinned release was found
        print("Oldest pinned release: None")


# Run main() only when this file is executed directly
if __name__ == "__main__":
    try:
        # Start checking the dependencies
        main()

    # Handle common network, timeout, and data-related errors
    except (URLError, TimeoutError, KeyError, ValueError) as e:
        print("Error while checking PyPI:", e)