from __future__ import annotations

import csv
import json
import re
from functools import lru_cache

from ..config import DATA_DIR
from ..matching.llm_client import LLMClient
from ..matching.llm_prompts import company_description_prompt
from ..models import CompanyProfile, clean_text


INDUSTRY_RULES: list[tuple[str, str]] = [
    ("consulting", r"\b(McKinsey|Boston Consulting Group|BCG|Bain|Deloitte|Accenture|PwC|EY|KPMG|Oliver Wyman|Strategy&|Roland Berger|FTI Consulting|Kearney|L\.?E\.?K\.?)\b"),
    ("finance", r"\b(Goldman|Morgan Stanley|J\.?P\.?\s*Morgan|JPMorgan|BlackRock|Blackstone|Point72|Citadel|Bridgewater|Bank|Capital|Investment|Investments|Private Equity|Hedge|UBS|HSBC|Lazard|Evercore|Barclays|Citi|Fidelity|KKR|Apollo|TPG|Warburg|Mubadala|SoftBank)\b"),
    ("tech", r"\b(Google|Alphabet|Meta|Facebook|Microsoft|Apple|Amazon|AWS|OpenAI|Anthropic|NVIDIA|AMD|Palantir|ByteDance|TikTok|Alibaba|Tencent|Baidu|Huawei|Stripe|Airbnb|Uber|SpaceX|Tesla|Databricks|Snowflake|Salesforce|Oracle|IBM|Intel|Samsung|Shopify|Canva|Scale AI|Anduril|DeepMind|Agoda|AeroVect)\b"),
    ("law", r"\b(Law|Legal|LLP|Latham|Skadden|Sullivan\s*&\s*Cromwell|Clifford Chance|Freshfields|Linklaters|White\s*&\s*Case|Kirkland|Debevoise|Gibson Dunn|WilmerHale|Sidley)\b"),
    ("government", r"\b(Government|Ministry|Department|Embassy|Congress|Senate|Parliament|White House|State Department|Foreign Affairs|Treasury|Defense|Defence|Army|Navy|Air Force)\b"),
    ("nonprofit", r"\b(United Nations|UNICEF|UNDP|UNHCR|World Bank|IMF|OECD|WHO|Foundation|Red Cross|Amnesty|Human Rights|Nonprofit|Non-profit|NGO|World Economic Forum)\b"),
    ("academia", r"\b(University|College|School|Institute|Laboratory|Lab|Research|Brookings|RAND|Harvard|Stanford|MIT|Oxford|Cambridge|Tsinghua|Peking)\b"),
    ("healthcare", r"\b(Hospital|Health|Healthcare|Medical|Medicine|Clinic|Pharma|Pfizer|Moderna|Novartis|Roche|Merck|BioNTech|Biotech)\b"),
    ("media", r"\b(New York Times|Washington Post|Journal|News|Media|Reuters|Bloomberg|CNN|BBC|NPR|Forbes|Atlantic|Economist|Financial Times|Politico|Axios)\b"),
    ("energy", r"\b(Energy|Climate|Renewable|Solar|Wind|Carbon|Sustainability|Oil|Gas|Shell|BP|Exxon|Chevron|Equinor|TotalEnergies|Orsted)\b"),
    ("consumer", r"\b(Nike|Adidas|LVMH|Unilever|Procter|Walmart|Target|Costco|Retail|Consumer|Luxury|Fashion|Food|Beverage|Coca-Cola|PepsiCo)\b"),
    ("realestate", r"\b(Real Estate|Infrastructure|Construction|Property|Properties|Brookfield|CBRE|JLL|Hotel|Hospitality)\b"),
    ("education", r"\b(Education|Teach|Teacher|Academy|EdTech|Learning)\b"),
    ("sports", r"\b(AC Milan|FIFA|UEFA|NBA|NFL|MLB|NHL|Olympic|Olympics|Formula 1|F1)\b"),
]


def _company_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean_text(value).lower())


def _one_sentence(value: str, max_chars: int = 260) -> str:
    text = clean_text(value)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentence = clean_text(parts[0] if parts else text)
    if len(parts) > 1 and (len(sentence) < 70 or re.search(r"\b[A-Z]\.$", sentence)):
        sentence = clean_text(f"{sentence} {parts[1]}")
    if len(sentence) <= max_chars:
        return sentence
    return sentence[: max_chars - 1].rsplit(" ", 1)[0].rstrip(",;:") + "."


def _one_word_industry(value: str) -> str:
    text = clean_text(value).lower()
    if not text:
        return ""
    if "needs research" in text or text.startswith("other"):
        return "other"
    if re.search(r"consult|strategy|management consulting", text):
        return "consulting"
    if re.search(r"financial|investment|bank|capital|asset|venture|private equity|insurance", text):
        return "finance"
    if re.search(r"software|internet|technology|it services|semiconductor|ai|computer|data", text):
        return "tech"
    if re.search(r"law|legal", text):
        return "law"
    if re.search(r"government|public policy|defense|military|international affairs", text):
        return "government"
    if re.search(r"nonprofit|non-profit|philanthropy|civic|international trade and development", text):
        return "nonprofit"
    if re.search(r"higher education|research|think tank|education", text):
        return "academia"
    if re.search(r"hospital|health|medical|pharma|biotech", text):
        return "healthcare"
    if re.search(r"media|broadcast|newspaper|publishing|journalism", text):
        return "media"
    if re.search(r"energy|oil|gas|renewable|climate|environment", text):
        return "energy"
    if re.search(r"retail|consumer|food|beverage|apparel|fashion|hospitality|travel", text):
        return "consumer"
    if re.search(r"real estate|construction|infrastructure", text):
        return "realestate"
    if re.search(r"sports|spectator sports", text):
        return "sports"
    return "other"


@lru_cache(maxsize=1)
def _company_cache() -> dict[str, dict[str, str]]:
    cache: dict[str, dict[str, str]] = {}

    audit_path = DATA_DIR / "audit" / "company_enrichment.csv"
    if audit_path.exists():
        with audit_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                company = clean_text(row.get("company_name"))
                key = _company_key(company)
                if not key:
                    continue
                cache[key] = {
                    "company_name": company,
                    "industry": clean_text(row.get("industry")) or "other",
                    "company_description": clean_text(row.get("company_description")),
                    "source_url": clean_text(row.get("source_url")),
                    "method": clean_text(row.get("method")) or "company_enrichment_audit",
                }

    brightdata_path = DATA_DIR / "brightdata_company_enrichment.json"
    if brightdata_path.exists():
        payload = json.loads(brightdata_path.read_text(encoding="utf-8"))
        for item in payload.get("records", []):
            record = item.get("record", {}) if isinstance(item, dict) else {}
            if not isinstance(record, dict):
                continue
            names = [record.get("name", ""), item.get("inputUrl", ""), record.get("url", "")]
            entry = {
                "company_name": clean_text(record.get("name")),
                "industry": _one_word_industry(record.get("industries", "")),
                "company_description": _one_sentence(record.get("about", "")),
                "source_url": clean_text(record.get("website") or record.get("url") or item.get("inputUrl")),
                "method": "brightdata_company_cache",
            }
            for name in names:
                key = _company_key(str(name))
                if key and entry["company_name"]:
                    cache[key] = entry

    intelligence_path = DATA_DIR / "company_intelligence.json"
    if intelligence_path.exists():
        payload = json.loads(intelligence_path.read_text(encoding="utf-8"))
        for item in payload.get("companies", []):
            if not isinstance(item, dict):
                continue
            company = clean_text(item.get("company"))
            key = _company_key(company)
            if not key:
                continue
            existing = cache.get(key, {})
            research_brief = clean_text(item.get("research_brief", ""))
            if "needs follow-up research" in research_brief.lower() or "company name alone" in research_brief.lower():
                research_brief = ""
            cache[key] = {
                "company_name": existing.get("company_name") or company,
                "industry": existing.get("industry") or _one_word_industry(item.get("industry", "")),
                "company_description": existing.get("company_description") or _one_sentence(research_brief),
                "source_url": existing.get("source_url") or clean_text(item.get("linkedin_company_url")),
                "method": existing.get("method") or "company_intelligence_cache",
            }

    return cache


def cached_company_profile(company_name: str) -> CompanyProfile | None:
    company = clean_text(company_name)
    if not company:
        return None
    cache = _company_cache()
    entry = cache.get(_company_key(company))
    if not entry:
        return None
    return CompanyProfile(
        company_name=company,
        industry=entry.get("industry", "") or "other",
        company_description=entry.get("company_description", ""),
        confidence="high" if entry.get("company_description") else "medium",
        method=entry.get("method", "company_cache"),
        source_url=entry.get("source_url", ""),
    )


def classify_industry(company_name: str, role_title: str = "") -> tuple[str, str, str]:
    company = clean_text(company_name)
    if not company:
        return "", "none", "missing_company"
    for industry, pattern in INDUSTRY_RULES:
        if re.search(pattern, company, flags=re.I):
            return industry, "high", "heuristic_company_name_v1"
    return "other", "low", "needs_web_or_llm_research"


def describe_company(company_name: str, industry: str, role_context: str = "", use_llm: bool = False) -> tuple[str, str]:
    company = clean_text(company_name)
    if not company:
        return "", "missing_company"
    if use_llm:
        client = LLMClient()
        if client.available():
            text = clean_text(client.complete_text(company_description_prompt(company, role_context)))
            if text:
                return text, "llm_company_description"
    if industry and industry not in {"other"}:
        return f"{company} is a {industry} organization.", "heuristic_template_v1"
    return "", "needs_web_or_llm_research"


def enrich_company(company_name: str, role_title: str = "", role_context: str = "", use_llm: bool = False) -> CompanyProfile:
    cached = cached_company_profile(company_name)
    if cached:
        return cached

    industry, confidence, method = classify_industry(company_name, role_title)
    description, description_method = describe_company(company_name, industry, role_context, use_llm=use_llm)
    return CompanyProfile(
        company_name=clean_text(company_name),
        industry=industry,
        company_description=description,
        confidence=confidence,
        method=f"{method};{description_method}",
    )
