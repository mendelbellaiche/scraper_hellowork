#!/usr/bin/env python3

import argparse
import json
import logging
import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlencode


BASE_URL = "https://www.hellowork.com"
LOCATION = "paris"

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


def build_search_url(keyword):
    query = urlencode({"k": keyword, "l": LOCATION})
    return f"{BASE_URL}/fr-fr/emploi/recherche.html?{query}"


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


def extract_job(url, keywords):
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
        "mots_cles": keywords,
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


def load_jobs(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read().strip()
        if not content:
            return []
        return json.loads(content)


def save_job(job, filename):
    jobs = load_jobs(filename)
    jobs.append(job)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(jobs, file, ensure_ascii=False, indent=2)


def append_imported_url(url, filename):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(url + "\n")


def load_url_list(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as file:
        return {line.strip() for line in file if line.strip()}


def save_urls(urls, keyword, filename):
    existing = load_url_list(filename)

    with open(filename, "a", encoding="utf-8") as file:
        for url in urls:
            line = f"{url} | {keyword}"
            if line not in existing:
                file.write(line + "\n")


def append_rejected_url(url, filename):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(url + "\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Scraper d'offres HelloWork")
    parser.add_argument(
        "-k", "--keyword",
        action="append",
        default=None,
        help="Mot-clé de recherche (ex : php). Peut être répété pour rechercher plusieurs "
             "mots-clés (ex : -k php -k java). La recherche est toujours limitée à Paris. "
             "Si absent, il sera demandé pendant l'exécution."
    )
    parser.add_argument(
        "--output-dir",
        default="./offres/",
        help="Dossier de destination des fichiers d'offres (défaut : ./offres/)"
    )
    parser.add_argument(
        "--reset",
        nargs="?",
        const="offres",
        default=None,
        choices=["offres", "all"],
        help="Réinitialise le fichier offres.json avant de lancer le scraping. "
             "Utiliser --reset all pour supprimer aussi rejects.txt et imported.txt "
             "(défaut si l'option est présente sans valeur : offres.json uniquement)"
    )
    parser.add_argument(
        "--log-file",
        default="scraper.log",
        help="Chemin du fichier de log (défaut : scraper.log)"
    )
    return parser.parse_args()


KEYWORD_EXAMPLES = ["php", "java", "python", "devops", "data engineer"]


def prompt_keyword():
    print(f"Exemples de recherche : {', '.join(KEYWORD_EXAMPLES)}")
    while True:
        keyword = input("Mot-clé de recherche : ").strip()
        if keyword:
            return keyword
        print("Le mot-clé ne peut pas être vide.")


def main():
    args = parse_args()
    setup_logger(args.log_file)
    os.makedirs(args.output_dir, exist_ok=True)

    keywords = args.keyword or [prompt_keyword()]

    filename = os.path.join(args.output_dir, "offres.json")
    rejects_filename = os.path.join(args.output_dir, "rejects.txt")
    imported_filename = os.path.join(args.output_dir, "imported.txt")
    if args.reset:
        if os.path.exists(filename):
            os.remove(filename)
        if args.reset == "all":
            if os.path.exists(rejects_filename):
                os.remove(rejects_filename)
            if os.path.exists(imported_filename):
                os.remove(imported_filename)

    urls_filename = os.path.join(
        args.output_dir,
        datetime.now().strftime("offres-%Y%m%d.txt")
    )

    job_urls = []
    url_keywords = {}
    for keyword in keywords:
        search_url = build_search_url(keyword)
        logger.info("Démarrage du scraping sur %s", search_url)

        keyword_urls = get_job_urls(search_url)
        logger.info("%d offres trouvées pour '%s'", len(keyword_urls), keyword)
        save_urls(keyword_urls, keyword, urls_filename)

        for url in keyword_urls:
            if url not in job_urls:
                job_urls.append(url)
            url_keywords.setdefault(url, []).append(keyword)

    saved_urls = load_url_list(imported_filename)
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
            job = extract_job(url, url_keywords.get(url, []))

            if "alternance" in job["titre"].lower():
                logger.info("Offre en alternance rejetée : %s (%s)", url, job["titre"])
                append_rejected_url(url, rejects_filename)
            else:
                save_job(job, filename)
                append_imported_url(url, imported_filename)
                logger.info("Offre enregistrée : %s", url)

            time.sleep(2)
        except requests.RequestException as e:
            logger.error("Erreur réseau sur %s : %s", url, e)
        except Exception as e:
            logger.error("Erreur sur %s : %s", url, e)

    logger.info("FIN")

    
if __name__ == '__main__':
    main()
