"""Consulta empresarial en el servicio publico del SII de Chile.

La secuencia de consulta se basa en el proyecto MIT `sagmor/sii_chile`, pero
esta implementacion es propia, acotada a personas juridicas y ejecutada solo
desde el servidor. El SII puede cambiar o interrumpir el servicio sin aviso.
"""

from base64 import b64decode
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re
import threading

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


CAPTCHA_URL = "https://zeus.sii.cl/cvc_cgi/stc/CViewCaptcha.cgi"
LOOKUP_URL = "https://zeus.sii.cl/cvc_cgi/stc/getstc"
TIMEOUT_SECONDS = 8
CACHE_TTL = timedelta(hours=24)


class SIIError(Exception):
    """Error base de la integracion."""


class SIIInvalidRUT(SIIError):
    """RUT invalido o no correspondiente a una persona juridica."""


class SIINotFound(SIIError):
    """El SII no devolvio antecedentes para el RUT."""


class SIIUnavailable(SIIError):
    """El servicio externo no respondio de forma util."""


@dataclass(frozen=True)
class SIICompany:
    rut: str
    razon_social: str
    actividades: tuple[dict, ...]
    inicio_actividades: bool
    consultado: datetime


_cache: dict[str, SIICompany] = {}
_cache_lock = threading.Lock()


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _clean_rut(value: str) -> str:
    return re.sub(r"[^0-9kK]", "", value or "").upper()


def _valid_rut(value: str) -> bool:
    rut = _clean_rut(value)
    if len(rut) < 8 or not rut[:-1].isdigit():
        return False
    total, factor = 0, 2
    for digit in reversed(rut[:-1]):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    rest = 11 - total % 11
    expected = "0" if rest == 11 else "K" if rest == 10 else str(rest)
    return rut[-1] == expected


def _format_rut(value: str) -> str:
    rut = _clean_rut(value)
    return f"{int(rut[:-1]):,}".replace(",", ".") + f"-{rut[-1]}"


def _legal_entity_rut(value: str) -> bool:
    rut = _clean_rut(value)
    return _valid_rut(rut) and int(rut[:-1]) >= 50_000_000


def _next_text_after_label(soup: BeautifulSoup, pattern: str) -> str:
    label = soup.find(string=lambda text: bool(text and re.search(pattern, text, re.I)))
    if not label:
        return ""
    current = label.parent
    for candidate in current.find_all_next(["div", "td"], limit=5):
        value = candidate.get_text(" ", strip=True)
        if value and not re.search(pattern, value, re.I):
            return re.sub(r"\s+", " ", value)[:180]
    return ""


def _parse_response(html: str, rut: str) -> SIICompany:
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    razon_social = _next_text_after_label(soup, r"Nombre\s+o\s+Raz[oó]n\s+Social")
    if not razon_social:
        match = re.search(
            r"Nombre\s+o\s+Raz[oó]n\s+Social\s*:\s*(.+?)\s+RUT\s+Contribuyente",
            page_text,
            re.I,
        )
        razon_social = re.sub(r"\s+", " ", match.group(1)).strip()[:180] if match else ""
    if not razon_social:
        raise SIINotFound("El RUT no registra antecedentes consultables.")

    activities = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows or "Actividades" not in rows[0].get_text(" ", strip=True):
            continue
        for row in rows[1:]:
            columns = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
            if len(columns) >= 2 and columns[0]:
                activities.append(
                    {
                        "giro": re.sub(r"\s+", " ", columns[0])[:180],
                        "codigo": re.sub(r"\D", "", columns[1])[:10],
                    }
                )
        break
    has_start = bool(re.search(r"presenta\s+Inicio\s+de\s+Actividades\s*:\s*SI", page_text, re.I))
    return SIICompany(
        rut=_format_rut(rut),
        razon_social=razon_social,
        actividades=tuple(activities[:10]),
        inicio_actividades=has_start,
        consultado=_utcnow(),
    )


def lookup_company(rut: str) -> SIICompany:
    cleaned = _clean_rut(rut)
    if not _legal_entity_rut(cleaned):
        raise SIIInvalidRUT("Solo se consultan RUT de personas juridicas validos.")
    with _cache_lock:
        cached = _cache.get(cleaned)
        if cached and cached.consultado > _utcnow() - CACHE_TTL:
            return cached

    try:
        with requests.Session() as client:
            client.headers.update(
                {
                    "User-Agent": "NexoTP/1.0 (+https://github.com/JuanPrevals/NexoTP)",
                    "Referer": "https://zeus.sii.cl/cvc/stc/stc.html",
                }
            )
            client.mount(
                "https://",
                HTTPAdapter(
                    max_retries=Retry(
                        total=2,
                        connect=2,
                        read=1,
                        backoff_factor=0.3,
                        status_forcelist=(502, 503, 504),
                        allowed_methods=frozenset({"POST"}),
                    )
                ),
            )
            captcha_response = client.post(
                CAPTCHA_URL,
                data={"oper": 0},
                timeout=TIMEOUT_SECONDS,
            )
            captcha_response.raise_for_status()
            encoded_captcha = captcha_response.json()["txtCaptcha"]
            captcha_code = b64decode(encoded_captcha)[36:40].decode("ascii")
            response = client.post(
                LOOKUP_URL,
                data={
                    "RUT": cleaned[:-1],
                    "DV": cleaned[-1],
                    "PRG": "STC",
                    "OPC": "NOR",
                    "txt_code": captcha_code,
                    "txt_captcha": encoded_captcha,
                },
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
    except (KeyError, ValueError, UnicodeError, requests.RequestException) as exc:
        raise SIIUnavailable("El SII no esta disponible temporalmente.") from exc

    result = _parse_response(response.text, cleaned)
    with _cache_lock:
        _cache[cleaned] = result
    return result
