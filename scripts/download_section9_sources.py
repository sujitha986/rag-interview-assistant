from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests
from requests import RequestException
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sources"
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "mitchell_machine_learning.pdf": "https://www.cs.cmu.edu/~tom/files/MachineLearningTomMitchell.pdf?utm_source=chatgpt.com",
    "hundred_page_ml.pdf": "https://ema.cri-info.cm/wp-content/uploads/2019/07/2019BurkovTheHundred-pageMachineLearning.pdf?utm_source=chatgpt.com",
    "ml_absolute_beginners.pdf": "https://www.hlevkin.com/hlevkin/45MachineDeepLearning/ML/Machine%20Learning%20For%20Absolute%20Beginners.pdf?utm_source=chatgpt.com",
    "intro_ml_python.pdf": "https://www.nrigroupindia.com/e-book/Introduction%20to%20Machine%20Learning%20with%20Python%20%28%20PDFDrive.com%20%29-min.pdf?utm_source=chatgpt.com",
    "master_ml_algorithms.pdf": "https://github.com/khurrameycon/Data-Science-Books/blob/main/Master%20Machine%20Learning%20Algorithms%20-%20Discover%20how%20they%20work%20and%20Implement%20Them%20From%20Scratch%20by%20Jason%20Brownlee%20%28z-lib.org%29.pdf?raw=1",
    "bishop_prml.pdf": "https://www.microsoft.com/en-us/research/wp-content/uploads/2006/01/Bishop-Pattern-Recognition-and-Machine-Learning-2006.pdf?utm_source=chatgpt.com",
    "ai_ml_deep_learning.pdf": "https://jcer.in/jcer-docs/E-Learning/Digital%20Library%20/E-Books/Artificial%20Intelligence%2C%20Machine%20Learning%2C%20and%20Deep%20Learning.pdf?utm_source=chatgpt.com",
}


def clean_url(url: str) -> str:
    parts = urlsplit(url)
    query = "&".join(part for part in parts.query.split("&") if part and not part.startswith("utm_"))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def main() -> None:
    failures = []
    for filename, url in SOURCES.items():
        target = OUT / filename
        if target.exists() and target.stat().st_size > 0:
            print(f"skip {filename}")
            continue
        print(f"download {filename}")
        try:
            response = requests.get(clean_url(url), timeout=60)
            response.raise_for_status()
        except requests.exceptions.SSLError:
            response = requests.get(clean_url(url), timeout=60, verify=False)
            response.raise_for_status()
        except RequestException as exc:
            failures.append((filename, str(exc)))
            print(f"failed {filename}: {exc}")
            continue
        target.write_bytes(response.content)
        print(f"wrote {target} ({target.stat().st_size:,} bytes)")
    if failures:
        print("\nSome sources could not be downloaded:")
        for filename, reason in failures:
            print(f"- {filename}: {reason}")


if __name__ == "__main__":
    main()
