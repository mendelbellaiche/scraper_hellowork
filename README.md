# Scrapper Hellowork

Scraper Python qui récupère les offres d'emploi correspondant à une recherche sur [HelloWork](https://www.hellowork.com) (titre, entreprise, salaire, description) et les enregistre dans des fichiers texte.

## Prérequis

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4
```

## Utilisation

La recherche est toujours limitée à Paris. Le mot-clé (`-k`/`--keyword`) peut être passé en argument ; s'il est absent, le script le demande pendant l'exécution en proposant des exemples (`php`, `java`, `python`, `devops`, `data engineer`, ...).

```bash
python3 main.py -k php
```

```bash
$ python3 main.py
Exemples de recherche : php, java, python, devops, data engineer
Mot-clé de recherche : php
```

### Options disponibles

```
$ ./main.py -h
usage: main.py [-h] [-k KEYWORD] [--output-dir OUTPUT_DIR] [--reset]
               [--log-file LOG_FILE]

Scraper d'offres HelloWork

options:
  -h, --help            show this help message and exit
  -k, --keyword KEYWORD
                        Mot-clé de recherche (ex : php). Peut être répété
                        pour rechercher plusieurs mots-clés (ex : -k php
                        -k java). La recherche est toujours limitée à
                        Paris. Si absent, il sera demandé pendant
                        l'exécution.
  --output-dir OUTPUT_DIR
                        Dossier de destination des fichiers d'offres (défaut :
                        ./offres/)
  --reset               Réinitialise uniquement le fichier offres.json avant
                        de lancer le scraping (rejects.txt et imported.txt
                        sont conservés)
  --log-file LOG_FILE   Chemin du fichier de log (défaut : scraper.log)
```

### Exemples d'appels

Lancement simple, avec un mot-clé :

```bash
python3 main.py -k php
```

Rechercher un autre mot-clé (ex : devops) :

```bash
python3 main.py --keyword devops
```

Rechercher plusieurs mots-clés en une seule exécution (`-k` peut être répété) :

```bash
python3 main.py -k php -k java -k devops
```

Réinitialiser uniquement `offres.json` avant de relancer le scraping (`rejects.txt` et `imported.txt` sont conservés, donc les offres déjà vues ne sont pas re-scrapées) :

```bash
python3 main.py -k php --reset
```

Choisir un dossier de destination pour les fichiers générés (par défaut `./offres/`) :

```bash
python3 main.py -k php --output-dir ./mes_offres
```

Choisir le fichier de log (par défaut `scraper.log`) :

```bash
python3 main.py -k php --log-file ./offres/scraper.log
```

Combiner plusieurs options :

```bash
python3 main.py -k php --output-dir ./mes_offres --log-file ./mes_offres/scraper.log --reset
```

## Fichiers générés

Dans le dossier de sortie (`--output-dir`, `./offres/` par défaut) :

- `offres.txt` — fichier général contenant le détail de toutes les offres récupérées (titre, entreprise, salaire, description, URL, date de récupération). Les offres déjà présentes ne sont jamais dupliquées.
- `rejects.txt` — URLs des offres rejetées (ex : alternance), pour ne pas les rescanner aux exécutions suivantes.
- `offres-YYYYMMDD.txt` — liste des URLs d'offres trouvées le jour de l'exécution, au format `<url> | <mot-clé>`.

Le fichier de log (`--log-file`, `scraper.log` par défaut) trace le déroulement de chaque exécution (offres trouvées, ignorées, rejetées, enregistrées, erreurs).
