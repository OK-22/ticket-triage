# Ticket Triage Service

A small machine learning service for IT help desk tickets. Send it the text of a ticket and it returns a category, a confidence score, and the most relevant knowledge-base article. It runs as a FastAPI web service, is tested automatically, and is built into a container image by a GitHub Actions pipeline.

## What it does
| Endpoint | Purpose |
|---|---|
| `GET /health` | Shows the service is up, the categories it knows, and how many articles are loaded |
| `POST /classify` | Returns the category, confidence, the top three scores, and a `low_confidence` flag |
| `POST /suggest` | Does the same, and adds the best-matching knowledge-base articles |

Example:
```
$ curl -s -X POST localhost:8000/suggest -H 'Content-Type: application/json' \
    -d '{"text":"please reset the password for jsmith, he is on leave"}'
{"category":"password_reset","confidence":0.986,"low_confidence":false,
 "scores":{"password_reset":0.986,"account_access":0.003,"software_issue":0.003},
 "articles":[{"file":"kb-04-domain-password-reset-helpdesk.md",
              "title":"KB-04: Reset a domain user's password as help desk (delegated rights)",
              "score":0.173}]}
```
The six categories are `password_reset`, `account_access`, `network_connectivity`, `software_issue`, `hardware_issue`, and `email_problem`.

## How it works
- **Training data:** 720 synthetic tickets generated from templates, with typos, greetings, and casing changes added (`triage/generate_data.py`). This is not real ticket data.
- **Model:** TF-IDF features (single words and pairs) feeding a logistic regression (`triage/train.py`).
- **Evaluation:** a separate set of 48 hand-written tickets in `data/handwritten_test.csv`, eight per category, written in different wording from the templates. The model was trained once and measured once on this set.
- **Article search:** plain TF-IDF similarity between the ticket and the markdown files in `kb/`. Articles below a minimum similarity are not returned.

## Results
| Measure | Value |
|---|---|
| Accuracy on the 48 hand-written tickets | **0.875 (42 of 48)** |
| Cross-validation accuracy on the synthetic data | 0.999 (not meaningful: the data comes from templates) |

| Category | Precision | Recall | F1 |
|---|---|---|---|
| account_access | 0.889 | 1.0 | 0.941 |
| email_problem | 1.0 | 0.75 | 0.857 |
| hardware_issue | 0.857 | 0.75 | 0.8 |
| network_connectivity | 0.889 | 1.0 | 0.941 |
| password_reset | 1.0 | 0.75 | 0.857 |
| software_issue | 0.727 | 1.0 | 0.842 |

The gap between 0.999 on synthetic data and 0.875 on hand-written tickets is the point of keeping a separate test set: a model can look perfect on data that looks like its training data.

**The six mistakes**
- "How do I change my login credentials? the old one stopped working after the weekend" was labeled `hardware_issue` instead of `password_reset`.
- "Can someone unlock my user? I keep getting access denied at the login screen" was labeled `account_access` instead of `password_reset`.
- "Desktop will not boot, just shows a blinking cursor" was labeled `network_connectivity` instead of `hardware_issue`.
- "Speakers on my pc have no sound even though the volume is up" was labeled `software_issue` instead of `hardware_issue`.
- "I sent an email to a customer and it bounced back with an error" was labeled `software_issue` instead of `email_problem`.
- "People say they never get my replies, maybe they land in junk" was labeled `software_issue` instead of `email_problem`.

Each mistake is a ticket that uses words the templates never used. The `low_confidence` flag (confidence below 0.5, an uncalibrated threshold chosen in advance) marked 6 of the 48 tickets, and 3 of those 6 were the mistakes. The other 3 mistakes were not flagged.

## Evidence from the pipeline and a separate machine
**Pipeline run #1 (commit 303a93f, branch main): passed in 1 minute 13 seconds.** The test job trained the model and got 0.875 accuracy with the same confusion matrix as an earlier run on a different machine, so training is reproducible with its fixed seed. The image job built and pushed the container image in 19 seconds.

**Published image, pulled and run on a separate Ubuntu server.** `/health` listed the six categories and `"kb_articles":4`. Four sample tickets sent to `/suggest`:

| Ticket | Category (confidence) | Top article (similarity) |
|---|---|---|
| I forgot my password and cannot log in | password_reset (0.993) | KB-01 (0.138) |
| new hire starting Monday needs an account and a laptop | account_access (0.97) | KB-02 (0.102) |
| ssh to the dev server keeps timing out | network_connectivity (0.857) | KB-03 (0.14) |
| my laptop will not turn on | hardware_issue (0.982) | none, the list was empty |

In the three tickets with a matching article, the right article ranked first. The laptop ticket matched no article and returned an empty list, which is the intended behavior. This is four examples, not an evaluation of the search. The similarity scores are low (0.07 to 0.14), and the minimum score is lenient, so weaker matches also appeared as second and third results for two of the tickets.

## Run it
```
pip install -r requirements.txt -r requirements-dev.txt
python -m triage.train
pytest -q
uvicorn app.main:app --port 8000
```
With Docker, which trains the model while the image is built:
```
docker build -t ticket-triage .
docker run --rm -p 8000:8000 ticket-triage
```
Interactive documentation is generated at http://localhost:8000/docs.

## The pipeline
| Job | What it does |
|---|---|
| test | Installs dependencies, trains the model, writes the results into the run summary, and runs the tests |
| image | On `main`, builds the container image (which trains its own model) and pushes it to `ghcr.io` with a `latest` tag and a commit tag |

## Knowledge base
`kb/` holds the articles the service can suggest, as markdown files. The first line starting with `# ` is used as the title. Add articles and rebuild the image to include them.

## Limits
- The training data is synthetic, and the test set is small (48 tickets) and written by hand, so the 0.875 figure is a rough guide, not a precise measure.
- Six categories only, and no handling of tickets that fit none of them beyond the confidence flag.
- Article search is lexical. It matches shared words, not meaning, so synonyms can be missed. Its scores are low and its cutoff is lenient, so lower-ranked results are often weak matches. A relative cutoff (only keep results scoring close to the best one) would be a sensible next step.
- No authentication, rate limiting, or monitoring. It is a learning project, not a production service.
