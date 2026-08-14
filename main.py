
import argparse
import json
import logging
import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin


BASE_URL = "https://www.hellowork.com"
SEARCH_URL = BASE_URL + "/fr-fr/emploi/recherche.html?k=php&l=paris"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PersonalJobResearch/1.0)"
}

logger = logging.getLogger("hellowork_scraper")


def setup_logger(log_file):
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def get_page(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_job_posting_data(soup):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            return data
    return {}


def format_salary(base_salary):
    if not base_salary:
        return ""
    value = base_salary.get("value", {})
    currency = base_salary.get("currency", "")
    min_value = value.get("minValue")
    max_value = value.get("maxValue")
    unit = value.get("unitText", "")

    if min_value and max_value:
        amount = f"{min_value} - {max_value}"
    elif min_value or max_value:
        amount = str(min_value or max_value)
    else:
        return ""

    return " ".join(p for p in [amount, currency, f"/ {unit}" if unit else ""] if p).strip()


def extract_job(url):
    soup = get_page(url)
    title = soup.select_one('[data-cy="jobTitle"]')

    job_data = get_job_posting_data(soup)

    company = job_data.get("hiringOrganization", {}).get("name", "")
    salary = format_salary(job_data.get("baseSalary"))

    description_html = job_data.get("description", "")
    description = BeautifulSoup(description_html, "html.parser").get_text("\n", strip=True)

    return {
        "titre": title.get_text(" ", strip=True) if title else job_data.get("title", ""),
        "entreprise": company,
        "salaire": salary,
        "description": description,
        "url": url,
        "date_recuperation": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def get_job_urls(search_url):
    soup = get_page(search_url)

    urls = []

    for link in soup.select("a[href]"):
        href = link.get("href")

        if href and "/fr-fr/emplois/" in href:
            url = urljoin(BASE_URL, href)
            if url not in urls:
                urls.append(url)
    return urls


def save_job(job, filename):
    with open(filename, "a", encoding="utf-8") as file:

        file.write("="*80 +"\n")

        file.write(f"TITRE: {job['titre']}\n")
        file.write(f"ENTREPRISE: {job['entreprise']}\n")
        file.write(f"SALAIRE: {job['salaire']}\n")
        file.write(f"URL: {job['url']}\n")
        file.write(f"DATE RECUPERATION: {job['date_recuperation']}\n")
        file.write("\nDESCRIPTION:\n")
        file.write(job["description"])
        file.write("\n\n")


def load_saved_urls(filename):
    urls = set()
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("URL: "):
                    urls.add(line[len("URL: "):].strip())
    return urls


def load_url_list(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as file:
        return {line.strip() for line in file if line.strip()}


def save_urls(urls, filename):
    existing = load_url_list(filename)

    with open(filename, "a", encoding="utf-8") as file:
        for url in urls:
            if url not in existing:
                file.write(url + "\n")


def append_rejected_url(url, filename):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(url + "\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Scraper d'offres HelloWork")
    parser.add_argument(
        "--output-dir",
        default="./offres/",
        help="Dossier de destination des fichiers d'offres (défaut : ./offres/)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Réinitialise le fichier offres.txt avant de lancer le scraping"
    )
    parser.add_argument(
        "--log-file",
        default="scraper.log",
        help="Chemin du fichier de log (défaut : scraper.log)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logger(args.log_file)
    os.makedirs(args.output_dir, exist_ok=True)

    filename = os.path.join(args.output_dir, "offres.txt")
    rejects_filename = os.path.join(args.output_dir, "rejects.txt")
    if args.reset:
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(rejects_filename):
            os.remove(rejects_filename)

    urls_filename = os.path.join(
        args.output_dir,
        datetime.now().strftime("offres-%Y%m%d.txt")
    )

    logger.info("Démarrage du scraping sur %s", SEARCH_URL)

    job_urls = get_job_urls(SEARCH_URL)
    logger.info("%d offres trouvées", len(job_urls))
    save_urls(job_urls, urls_filename)

    saved_urls = load_saved_urls(filename)
    rejected_urls = load_url_list(rejects_filename)
    new_urls = []
    for url in job_urls:
        if url in saved_urls:
            logger.info("Déjà scrapé, ignoré : %s", url)
        elif url in rejected_urls:
            logger.info("Déjà rejeté, ignoré : %s", url)
        else:
            new_urls.append(url)

    logger.info(
        "%d nouvelles offres à récupérer (%d déjà en base, %d déjà rejetées)",
        len(new_urls), len(saved_urls), len(rejected_urls)
    )

    for url in new_urls:
        try:
            logger.info("Récupération : %s", url)
            job = extract_job(url)

            if "alternance" in job["titre"].lower():
                logger.info("Offre en alternance rejetée : %s (%s)", url, job["titre"])
                append_rejected_url(url, rejects_filename)
            else:
                save_job(job, filename)
                logger.info("Offre enregistrée : %s", url)

            time.sleep(2)
        except requests.RequestException as e:
            logger.error("Erreur réseau sur %s : %s", url, e)
        except Exception as e:
            logger.error("Erreur sur %s : %s", url, e)

    logger.info("FIN")

    
if __name__ == '__main__':
    main()
