# Scrapper Hellowork

Scraper Python qui récupère les offres d'emploi correspondant à une recherche sur [HelloWork](https://www.hellowork.com) (titre, entreprise, salaire, description) et les enregistre dans des fichiers texte.

## Prérequis

```bash
pip install requests beautifulsoup4
```

## Utilisation

```bash
python3 main.py
```

### Options disponibles

```
$ ./main.py -h
usage: main.py [-h] [--output-dir OUTPUT_DIR] [--reset] [--log-file LOG_FILE]

Scraper d'offres HelloWork

options:
  -h, --help            show this help message and exit
  --output-dir OUTPUT_DIR
                        Dossier de destination des fichiers d'offres (défaut :
                        ./offres/)
  --reset               Réinitialise le fichier offres.txt avant de lancer le
                        scraping
  --log-file LOG_FILE   Chemin du fichier de log (défaut : scraper.log)
```

### Exemples d'appels

Lancement simple, avec les valeurs par défaut :

```bash
python3 main.py
```

Réinitialiser `offres.txt` et `rejects.txt` avant de relancer le scraping :

```bash
python3 main.py --reset
```

Choisir un dossier de destination pour les fichiers générés (par défaut `./offres/`) :

```bash
python3 main.py --output-dir ./mes_offres
```

Choisir le fichier de log (par défaut `scraper.log`) :

```bash
python3 main.py --log-file ./offres/scraper.log
```

Combiner plusieurs options :

```bash
python3 main.py --output-dir ./mes_offres --log-file ./mes_offres/scraper.log --reset
```

## Fichiers générés

Dans le dossier de sortie (`--output-dir`, `./offres/` par défaut) :

- `offres.txt` — fichier général contenant le détail de toutes les offres récupérées (titre, entreprise, salaire, description, URL, date de récupération). Les offres déjà présentes ne sont jamais dupliquées.
- `rejects.txt` — URLs des offres rejetées (ex : alternance), pour ne pas les rescanner aux exécutions suivantes.
- `offres-YYYYMMDD.txt` — liste des URLs d'offres trouvées le jour de l'exécution.

Le fichier de log (`--log-file`, `scraper.log` par défaut) trace le déroulement de chaque exécution (offres trouvées, ignorées, rejetées, enregistrées, erreurs).
