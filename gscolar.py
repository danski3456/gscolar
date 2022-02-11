#!./.venv/bin/python3
# vim ft=python

import re
import click
import json
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

year_re = re.compile("(\d{4})")
citation_re = re.compile("Cited by (\d+)")

@click.group()
def cli():
    pass

def extarct_article_data(raw_html: str) -> dict:

    soup = BeautifulSoup(raw_html, 'html.parser')

    articles = soup.find_all("div", {"class": "gs_r gs_or gs_scl"})
    outputs = []
    for j, article in enumerate(articles):
        output = {}
        try:
            title = article.find_all("h3", {"class": "gs_rt"})[0]
            article_id = title.a.get("id")
            link = title.a.get("href")
            title = title.a.text
            output["article_id"] = article_id
            output["link"] = link
            output["title"] = title
        except Exception as e:
            print(f"Failed to get title for {j}")
            continue

        try:
            subtitle = article.find_all("div", {"class": "gs_a"})[0].text.replace("…", "")
            authors = subtitle.split(" - ")[0].strip()
            output["authors"] = authors.replace(",", ";")
        except Exception as e:
            output["authors"] = "Unknwon"
            print(f"Failed to get authors for {j}")

        try:
            subtitle = article.find_all("div", {"class": "gs_a"})[0].text.replace("…", "")
            year = year_re.search(subtitle)[1]
            output["year"] = year
        except Exception as e:
            output["year"] = 1900
            print(f"Failed to get year for {j}")

        try:
            link_to_file = article.find_all("div", {"class": "gs_ggsd"})[0]
            link_to_file = link_to_file.a.get("href")
            output["link_to_file"] = link_to_file
        except Exception as e:
            print(f"Failed to get link to file for {j}")
            output["link_to_file"] = ""

        try:
            elem = article.find_all("div", {"class": "gs_fl"})
            for citations in elem:
                if len(citations["class"]) == 1:
                    break

            citations = citations.find_all("a", string=re.compile("Cited by"))[0].text
            citations = citation_re.search(citations)[1]
            output["citations"] = citations
        except Exception as e:
            print(f"Failed to get citations for {j}")
            output["citations"] = 0

        outputs.append(output)

    return outputs

user_agent =  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'

def jsonl_query(query):
    if isinstance(query, tuple):
        query = " ".join(query)
    return Path(query.replace(" ", "-")).with_suffix(".jsonl")


@click.command()
@click.argument("query", type=str, nargs=-1)
@click.option("--numpages", "-p", type=int, default=2)
@click.option("--sleep", "-s", type=int, default=2)
def download(query, numpages, sleep):

    # Preparing query
    output_file = jsonl_query(query)
    query = " ".join(query)
    safe_query = requests.utils.quote(query)

    # Check if lines have been scrapped
    traversed_file = Path(".traversed.txt")
    traversed_file.touch(exist_ok=True)
    with open(traversed_file, "r") as fh:
        traversed = [x.strip() for x in fh.readlines()]

    url = "https://scholar.google.com/scholar?start={num}&q={query}&hl=en&as_sdt=0,7"
    headers = {'User-Agent': user_agent}


    json_file = Path(query.replace(" ", "-")).with_suffix(".jsonl")

    for page in range(numpages):

        num = page * 10
        url_ = url.format(num=num, query = safe_query)
        if url_ not in traversed:
            time.sleep(sleep)
            print(f"Downling data from {num}")
            r = requests.get(url_, headers=headers)
            if r.status_code == 200:
                with open(traversed_file, "a") as fh: fh.write(url_ + "\n")
                raw = r.text
                parsed_articles = extarct_article_data(raw)
                with open(output_file, "a") as fh: 
                    for item in parsed_articles:
                        json.dump(item, fh)
                        fh.write("\n")
            else:
                print("Error ocurred")
        else:
            print(f"Skipping data from {num}")


@click.command()
@click.argument('filename', type=click.Path(exists=True))
def get_csv(filename):

    output_file = Path(filename).with_suffix(".csv")

    articles = []
    seen = []
    with open(filename, "r") as fh:
        for line in fh.readlines():
            item = json.loads(line)
            if item["article_id"] not in seen:
                seen.append(item["article_id"])
                articles.append(item)

    articles = sorted(
        articles,
        key=lambda x: (-int(x["citations"]), int(x["year"]))
    )

    ORDER = [
        "title",
        "status",
        "citations",
        "year",
        "authors",
        "link",
        "link_to_file",
    ]

    with open(output_file, "w") as fh:
        header = ",".join(ORDER)
        fh.write(header + "\n")
        for item in articles:
            line = map(str, [item.get(k, "") for k in ORDER])
            line = ",".join([x.replace(",", ";") for x in line])
            fh.write(line + "\n")

cli.add_command(download)
cli.add_command(get_csv)

if __name__ == "__main__":
    cli()
