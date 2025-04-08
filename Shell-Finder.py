import requests
import re
import base64
import zlib
import threading
import concurrent.futures
import itertools
import sys
import time
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# Shell indikator kuat
confirmed_shells = {
    "wso": "WSO Shell",
    "c99": "C99 Shell",
    "r57": "R57 Shell",
    "FilesMan": "FilesMan",
    "Mini Shell": "Mini Shell",
    "PHP Shell": "PHP Shell",
    "Uploader": "File Uploader",
    "cmd shell": "CMD Shell",
    "shell": "Generic Shell"
}

common_dangerous = {
    "system", "exec", "passthru", "eval", "base64_decode", "shell_exec", "assert"
}

output_file = "Shell_Valid.txt"
spinner_done = False
lock = threading.Lock()

brute_paths = [
    "/wso.php", "/c99.php", "/shell.php", "/up.php", "/cmd.php", "/adminer.php",
    "/files.php", "/r57.php", "/backdoor.php"
]

def spinner():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if spinner_done:
            break
        with lock:
            sys.stdout.write(Fore.YELLOW + f'\r[LOADING] Sedang scanning... {c}')
            sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * 60 + '\r')

def decode_content(content):
    try:
        for _ in range(3):
            content = base64.b64decode(content).decode('utf-8', errors='ignore')
    except:
        pass
    try:
        content = zlib.decompress(content.encode()).decode("utf-8")
    except:
        pass
    return content

def detect_type(content):
    full_content = content + decode_content(content)
    for key in confirmed_shells:
        if re.search(key, full_content, re.IGNORECASE):
            return 'shell', confirmed_shells[key]
    for func in common_dangerous:
        if re.search(func, full_content, re.IGNORECASE):
            return 'danger', func
    return None, None

def detect_waf(response):
    waf_headers = ['server', 'x-sucuri-id', 'x-cdn', 'cf-ray', 'x-firewall']
    for header in response.headers:
        if header.lower() in waf_headers:
            return True
    return False

def print_result(message):
    with lock:
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        print(message)
        sys.stdout.write(Fore.YELLOW + '\r[LOADING] Sedang scanning...')

def log_shell(url, shell_type):
    with open(output_file, 'a') as f:
        f.write(f"{url} | Detected: {shell_type}")

def scan_brute_paths(base_url):
    if not base_url.endswith('/'):
        base_url += '/'
    found = False
    for path in brute_paths:
        url = base_url.rstrip('/') + path
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                tipe, keyword = detect_type(response.text)
                if tipe == 'shell':
                    msg = Fore.CYAN + f"[SHELL] {url} | Status: 200 | Detected: {keyword}"
                    print_result(msg)
                    log_shell(url, keyword)
                    found = True
        except:
            continue
    return found

def scan_url(url):
    try:
        response = requests.get(url, timeout=10)
        status = response.status_code
        waf = detect_waf(response)
        content = response.text
        tipe, keyword = detect_type(content)

        if tipe == 'shell':
            msg = Fore.CYAN + f"[SHELL] {url} | Status: {status} | WAF: {'Yes' if waf else 'No'} | Detected: {keyword}"
            print_result(msg)
            log_shell(url, keyword)

        elif tipe == 'danger':
            msg = Fore.GREEN + f"[SAFE]  {url} | Status: {status} | Detected: {keyword}"
            print_result(msg)

        elif waf:
            msg = Fore.YELLOW + f"[WAF?]  {url} | Status: {status} | WAF Detected"
            print_result(msg)

        else:
            msg = Fore.GREEN + f"[SAFE]  {url} | Status: {status}"
            print_result(msg)

        if tipe != 'shell':
            scan_brute_paths(url)

    except Exception as e:
        print_result(Fore.LIGHTBLACK_EX + f"[ERROR] {url} -> {e}")

def main():
    print(Fore.MAGENTA + """
███████ ██   ██ ███████ ██      ██       ███████ ██ ███    ██ ██████  ███████ ██████  
██      ██   ██ ██      ██      ██       ██      ██ ████   ██ ██   ██ ██      ██   ██ 
███████ ███████ █████   ██      ██ █████ █████   ██ ██ ██  ██ ██   ██ █████   ██████  
     ██ ██   ██ ██      ██      ██       ██      ██ ██  ██ ██ ██   ██ ██      ██   ██ 
███████ ██   ██ ███████ ███████ ███████  ██      ██ ██   ████ ██████  ███████ ██   ██ 
    """)
    print(Fore.CYAN + "MR P3T0K | Z-BL4CX-H4T TEAM\n")

    file_input = input(Fore.CYAN + "Masukkan nama file .txt berisi daftar URL: ").strip()
    try:
        with open(file_input, 'r') as f:
            urls = [u.strip() for u in f if u.startswith("http")]
    except FileNotFoundError:
        print(Fore.RED + "[X] File tidak ditemukan.")
        return

    if not urls:
        print(Fore.RED + "[X] Tidak ada URL valid ditemukan.")
        return

    print(Fore.CYAN + f"\n[INFO] Memulai scan {len(urls)} URL...\n")

    global spinner_done
    t = threading.Thread(target=spinner)
    t.start()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(scan_url, urls)

    spinner_done = True
    t.join()
    print(Fore.CYAN + f"\n[SELESAI] Shell valid disimpan di: {output_file}")

if __name__ == "__main__":
    main()
