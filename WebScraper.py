#!/bin/Python3
# Created by: Barath
# Tool name: WebScraper
# version: 2.2

# usage: python3 WebScraper.py -u http://example.com

import argparse
import re
from urllib.parse import urljoin, urldefrag, urlparse
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from xml.etree import ElementTree as ET


def banner():
    print("""

    
                     #   ,                        %                    
                        ,                          @    (              
                  (.   .(                           @    @             
                 &*   .@                            &&    @            
                @@    @.                             @/   /@           
               &@    @@                              @@    @@          
              ,@@   #@&                              ,@@   *@#         
              @@.   @@&                              .@@#   @@         
             ,@@    .@@%#//(((/#@& @    @ ,@@.*#####&@@#    @@&        
             @@@       .&@@@@@@@,@@@@@@@@@@.@@@@@@@@*       &@@        
             @@@@@@@@.           @@@@@@@@@@            @@@@@@@@        
                .        @@@&*. (@@@@@@@@@@@  ,/@@@/        *          
                      @@@    *@@, @@@@@@@@  @@%    @@@                 
                   @@@    @@@@   @@@@@@@@@@   &@@@    @@@              
                @@@       @@@.   @@@@@@@@@@    @@@       @@@*          
          @(&@@@.         @@@*    @@@@@@@@#    @@@          @@@@*%     
          @@@&            @@@.    &@@@@@@@     @@@            *@@@     
          %@@             @@@      @@@@@@      @@@             @@@     
          ,@@             @@@       @@@@/      @@@             @@@     
           @@,            &@@        @@(       @@@             @@      
           %@&            ,@@                  @@@            ,@@      
            @@             @@                  @@(            @@       
            .@,            @@.                 @@             @%       
             *@            (@/                 @@            %@        
              (#            @@                *@,            @         
               *.           #@                @@            @          
                .            @/               @            %           
                              @              @,           /            
                              .&            .(                         
                                (           /                          
                                 &        .                            
                             
                                 WebScraper
                                 Version 2.2

             usage : python3 WebScraper.py -u http://example.com
    """)


def build_session(timeout: float = 10.0) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "WebScraper/2.2 (+https://example.org)"
    })
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.request_timeout = timeout  # convenience attribute
    return session


def is_http_url(href: str) -> bool:
    return href.startswith("http://") or href.startswith("https://")


def should_skip(href: str) -> bool:
    if not href:
        return True
    href = href.strip()
    if href in ("#",):
        return True
    if href.startswith(("mailto:", "javascript:", "tel:", "data:")):
        return True
    return False


# ---------- Recon helpers ----------

def fetch_text(session: requests.Session, url: str, timeout: float):
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except requests.RequestException:
        return None


def extract_emails(text: str):
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    return set(re.findall(pattern, text or ""))


def get_robots(session: requests.Session, base_url: str, timeout: float):
    robots_url = urljoin(base_url, "/robots.txt")
    txt = fetch_text(session, robots_url, timeout)
    disallow = []
    sitemaps = []
    if txt:
        for line in txt.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("disallow:"):
                disallow.append(line.split(":", 1)[1].strip())
            elif line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":", 1)[1].strip())
    return txt, disallow, sitemaps


def fetch_sitemap_urls(session: requests.Session, sitemap_url: str, timeout: float):
    xml = fetch_text(session, sitemap_url, timeout)
    if not xml:
        return []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []
    # urlset
    for loc in root.findall(".//sm:url/sm:loc", ns):
        if loc.text:
            urls.append(loc.text.strip())
    # sitemap index
    for loc in root.findall(".//sm:sitemap/sm:loc", ns):
        if loc.text:
            urls.extend(fetch_sitemap_urls(session, loc.text.strip(), timeout))
    return urls


def passive_subdomains_crtsh(domain: str):
    try:
        resp = requests.get(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=10)
        if resp.status_code != 200:
            return set()
        data = resp.json()
        results = set()
        for row in data:
            name = row.get("name_value", "")
            for part in name.split("\n"):
                part = part.strip().lower()
                if part and not part.startswith("*."):
                    results.add(part)
        return results
    except Exception:
        return set()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True, help="Target URL")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds (default: 10)")
    parser.add_argument("--method", choices=["HEAD", "GET"], default="HEAD", help="HTTP method used to check links")
    parser.add_argument("--emails", action="store_true", help="Extract emails from the main page")
    parser.add_argument("--robots", action="store_true", help="Fetch and print robots.txt Disallow and Sitemap entries")
    parser.add_argument("--sitemap", action="store_true", help="Fetch and parse sitemap URLs (from robots or /sitemap.xml)")
    parser.add_argument("--subdomains", action="store_true", help="Passive subdomain enumeration via crt.sh")
    args = parser.parse_args()

    url = args.url.strip()
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        print("[-] Check your input URL (must start with http:// or https://).")
        return

    banner()

    session = build_session(timeout=args.timeout)
    try:
        resp = session.get(url, timeout=session.request_timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[-] Failed to fetch page: {e}")
        return

    soup = BeautifulSoup(resp.content, "html.parser")

    # Emails from main page
    if args.emails:
        emails = extract_emails(resp.text)
        if emails:
            print("[*] Emails found:")
            for em in sorted(emails):
                print(f"    - {em}")
        else:
            print("[*] No emails found.")

    # robots.txt (and collect sitemap references for later)
    robots_txt = None
    robots_disallow = []
    robots_sitemaps = []
    if args.robots or args.sitemap:
        robots_txt, robots_disallow, robots_sitemaps = get_robots(session, url, session.request_timeout)

    if args.robots:
        if robots_txt is None:
            print("[-] robots.txt not reachable")
        else:
            if robots_disallow:
                print("[*] robots.txt Disallow rules:")
                for d in robots_disallow:
                    print(f"    - {d}")
            else:
                print("[*] robots.txt has no Disallow rules.")
            if robots_sitemaps:
                print("[*] robots.txt Sitemaps:")
                for sm in robots_sitemaps:
                    print(f"    - {sm}")
            else:
                print("[*] robots.txt has no Sitemap entries.")

    # sitemaps
    if args.sitemap:
        candidate_sitemaps = list(robots_sitemaps)
        if not candidate_sitemaps:
            candidate_sitemaps = [urljoin(url, "/sitemap.xml")]
        sitemap_urls = set()
        for sm in candidate_sitemaps:
            sitemap_urls.update(fetch_sitemap_urls(session, sm, session.request_timeout))
        if sitemap_urls:
            print(f"[*] Sitemap URLs ({len(sitemap_urls)}):")
            for su in sorted(sitemap_urls):
                print(f"    - {su}")
        else:
            print("[*] No URLs extracted from sitemap(s).")

    # passive subdomains via crt.sh
    if args.subdomains:
        domain = urlparse(url).netloc
        subs = passive_subdomains_crtsh(domain)
        if subs:
            print(f"[*] Passive subdomains ({len(subs)}):")
            for s in sorted(subs):
                print(f"    - {s}")
        else:
            print("[*] No passive subdomains found or crt.sh unavailable.")

    # Existing link discovery and status check from the main page
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if should_skip(href):
            continue
        href = urldefrag(href).url
        full_url = href if is_http_url(href) else urljoin(url, href)
        links.add(full_url)

    if not links:
        print("[*] No links found.")
        return

    method = args.method
    for link in sorted(links):
        try:
            if method == "HEAD":
                r = session.head(link, allow_redirects=True, timeout=session.request_timeout)
                code = r.status_code
            else:
                r = session.get(link, allow_redirects=True, timeout=session.request_timeout, stream=True)
                code = r.status_code
                r.close()
            print(f"[+] {link}\t[{code}]")
        except requests.RequestException as e:
            print(f"[!] {link}\t[error: {e.__class__.__name__}]")


if __name__ == "__main__":
    main()