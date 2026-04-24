import json
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from langchain_ollama import ChatOllama
from tool_generator import generate_tools

# ── CONFIG ─────────────────────────────────────────────────────
OLLAMA_MODEL = "llama3.1"
BASE_DIR = Path(__file__).parent
REGISTRY_PATH = str(BASE_DIR / "api_registry.yaml")
TODAY = datetime.now().strftime("%Y-%m-%d")

# ── LOAD REGISTRY ─────────────────────────────────────────────
def load_registry():
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)

# ── LLM ───────────────────────────────────────────────────────
llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.0)
# Phase 3 returns a JSON object with several keys; avoid truncated output on Ollama defaults.
llm_convert = ChatOllama(model=OLLAMA_MODEL, temperature=0.0, num_predict=512)

# ── JSON PARSER ───────────────────────────────────────────────
def safe_json_parse(text):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


def coerce_date_from_text(text):
    """If a parameter description asks for YYYY-MM-DD, map common phrases — no per-API ids."""
    if not text or not isinstance(text, str):
        return None
    s = text.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    low = s.lower()
    if re.search(r"\btoday\b", low) or "todays" in low:
        return TODAY
    if "tomorrow" in low:
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return None


def merge_coercion_fallback(api, raw_params, llm_out):
    """
    Fill gaps when the LLM omits keys. Uses only registry parameter descriptions
    (e.g. 'yyyy-mm-dd', 'iata'), not specific api ids.
    """
    out = dict(llm_out) if llm_out else {}
    for p in api.get("parameters", []):
        name = p["name"]
        if name in out:
            continue
        if name not in raw_params:
            continue
        raw = raw_params[name]
        if raw is None or raw == "":
            continue
        desc = (p.get("description") or "").lower()
        sraw = str(raw).strip()
        if "yyyy-mm-dd" in desc:
            c = coerce_date_from_text(sraw)
            if c:
                out[name] = c
                continue
        if "iata" in desc and len(sraw) == 3 and sraw.isalpha():
            out[name] = sraw.upper()
            continue
    return out


def merge_passthrough_from_raw(api, raw_params, converted):
    """
    If the model omitted a parameter but raw_params still holds a value, copy it
    through using registry `type` only (string / number / boolean). Works for
    any API — names, emails, free-text filters, etc.
    """
    out = dict(converted) if converted else {}
    for p in api.get("parameters", []):
        name = p["name"]
        if name in out:
            continue
        if name not in raw_params:
            continue
        raw = raw_params[name]
        if raw is None:
            continue
        ptype = (p.get("type") or "string").lower()
        if ptype == "string":
            s = str(raw).strip()
            if s:
                out[name] = s
        elif ptype == "number":
            try:
                s = str(raw).strip().replace(",", "")
                out[name] = float(s) if "." in s else int(s)
            except (ValueError, TypeError):
                pass
        elif ptype == "boolean":
            if isinstance(raw, bool):
                out[name] = raw
            else:
                low = str(raw).strip().lower()
                if low in ("true", "yes", "1"):
                    out[name] = True
                elif low in ("false", "no", "0"):
                    out[name] = False
    return out


# ═══════════════════════════════════════════════════════════════
#  DATA BUILDERS — context fed to LLM at each phase
# ═══════════════════════════════════════════════════════════════

def build_api_catalog(apis):
    """Compact listing of every API with its description (Phase 1 context)."""
    lines = []
    for api in apis:
        lines.append(f"- id: {api['id']}  |  name: {api['name']}")
        lines.append(f"  {api['description'].strip()}")
    return "\n".join(lines)


def build_param_spec(api):
    """Human-readable parameter breakdown for an API (Phase 2 context)."""
    required = [p for p in api.get("parameters", []) if p.get("required")]
    optional = [p for p in api.get("parameters", []) if not p.get("required")]
    lines = []
    if required:
        lines.append("REQUIRED:")
        for p in required:
            lines.append(f"  • {p['name']} ({p['type']}): {p.get('description', '')}")
    if optional:
        lines.append("OPTIONAL:")
        for p in optional:
            lines.append(f"  • {p['name']} ({p['type']}): {p.get('description', '')}")
    return "\n".join(lines)


def build_conversion_examples(api):
    """
    Phase 3 context — examples of how natural language maps to API values.
    Generated dynamically from each parameter's description.
    """
    examples = {
        "iata": (
            "City name → IATA code:\n"
            "    Mumbai→BOM  Delhi→DEL  Bangalore→BLR  Hyderabad→HYD\n"
            "    Chennai→MAA  Kolkata→CCU  Dubai→DXB  London→LHR\n"
            "    New York→JFK  Singapore→SIN  Goa→GOI  Jaipur→JAI"
        ),
        "date": (
            f"Date → YYYY-MM-DD  (today is {TODAY}):\n"
            "    'April 12' → 2026-04-12   'tomorrow' → compute from today\n"
            "    '12-04' → 2026-04-12   '12/04/2026' → 2026-04-12"
        ),
        "seat": (
            "Seat class → lowercase:\n"
            "    'economy'/'eco'/'cheap' → economy\n"
            "    'business'/'biz'/'premium' → business"
        ),
        "boolean": "Boolean-ish → true/false:  'yes'→true  'no'→false",
    }

    used = set()
    for p in api.get("parameters", []):
        desc = p.get("description", "").lower()
        if "iata" in desc and "iata" not in used:
            used.add("iata")
        if "yyyy-mm-dd" in desc and "date" not in used:
            used.add("date")
        if "economy or business" in desc and "seat" not in used:
            used.add("seat")
        if p.get("type") == "boolean" and "boolean" not in used:
            used.add("boolean")

    if not used:
        return "No special conversions needed — pass values as-is."
    return "\n".join(examples[k] for k in used)


# ═══════════════════════════════════════════════════════════════
#  PHASE 1 — Intent Detection
# ═══════════════════════════════════════════════════════════════

def phase1_detect_intent(user_input, api_catalog, history):
    history_ctx = ""
    if history:
        recent = history[-6:]
        history_ctx = "Conversation so far:\n" + "\n".join(
            f"  {m['role'].upper()}: {m['content']}" for m in recent
        ) + "\n\n"

    prompt = f"""{history_ctx}You are an Automation API Assistant.

Available APIs:
{api_catalog}

User said: "{user_input}"

Pick the single BEST matching API. Consider the action verb carefully
(search/find ≠ book/create ≠ cancel ≠ update ≠ get/view).

If the user states a goal in general terms but the message does not contain
concrete values (IDs, dates, codes, names-as-filters) that a narrow
"get one by id" style API would need, prefer a broader list/search/filter API
when the catalog includes one whose description fits lookup without those identifiers.

Respond with ONLY this JSON — nothing else:
{{"api_id": "<id or null>", "confidence": "high|medium|low|none", "reason": "<one-line explanation>"}}"""

    data = safe_json_parse(llm.invoke(prompt).content)
    return data if data else {"api_id": None, "confidence": "none", "reason": "could not parse"}


# ═══════════════════════════════════════════════════════════════
#  PHASE 2 — Parameter Collection
# ═══════════════════════════════════════════════════════════════

def _required_param_names(api):
    return {p["name"] for p in api.get("parameters", []) if p.get("required")}


def _optional_param_names(api):
    return {p["name"] for p in api.get("parameters", []) if not p.get("required")}


def _strip_optional_params(api, params):
    """Remove registry-marked optional keys (e.g. when user says skip)."""
    for p in api.get("parameters", []):
        if not p.get("required"):
            params.pop(p["name"], None)


def phase2_extract_params(user_input, api, already, allowed_names=None, phase=None):
    """
    Extract parameters from natural language. If allowed_names is set, only
    those registry parameters may appear in the output — used so the first
    message after API confirm never pre-fills optional filters from intent text.
    """
    params = api.get("parameters", [])
    if allowed_names is not None:
        if not allowed_names:
            return {}
        params = [p for p in params if p["name"] in allowed_names]

    param_defs = json.dumps([
        {"name": p["name"], "type": p.get("type", "string"),
         "description": p.get("description", ""),
         "required": p.get("required", False),
         **({"enum": p["enum"]} if p.get("enum") else {})}
        for p in params
    ], indent=2)

    already_json = json.dumps(already, indent=2) if already else "{}"

    scope = ""
    if allowed_names is not None:
        scope = f"""
You may ONLY output keys from this exact set: {sorted(allowed_names)}.
Do not output any other parameter name."""

    optional_ctx = ""
    if phase == "optional_offer":
        optional_ctx = """
Context: The assistant just asked whether to add optional filters. This message
is the user's answer. Extract every concrete filter value they give (person
names, emails, amounts, codes). Patterns like "only name Jane Doe", "name is X",
or "I know only name X" mean the name-type parameter should be the actual
name span (e.g. "Jane Doe"), not the words "name" or "only"."""

    confirm_ctx = ""
    if phase == "confirm_edit":
        confirm_ctx = """
Context: The user is correcting the upcoming API call before it runs. The text
may include several of their recent lines (newest at the bottom). Pull any
parameter values they clearly stated in any of those lines, not only the last
sentence, if they refer back to a name/email/etc. they gave earlier."""

    prompt = f"""Extract parameter values for this API call. You only have the
parameter definitions below (from the API registry) — use each parameter's
description to decide what KIND of value is allowed. Do not assume extra
domain rules beyond those descriptions.

API: {api['id']} — {api['name']}

Parameter definitions (name, type, description, required):
{param_defs}

Already collected: {already_json}

User said: "{user_input}"
{scope}
{optional_ctx}
{confirm_ctx}

Rules:
- A parameter gets a value only if the user clearly supplied a concrete value
  that fits that parameter's description (including any format or examples
  implied there).
- If a parameter has an "enum" list, its value MUST be one of those exact
  strings (case-insensitive). Never invent, translate, or paraphrase enum
  values; if the user did not clearly name one, omit the parameter.
- Do NOT treat intent phrasing or topic words as values: e.g. words that only
  describe what they want to do ("details", "info", "list", typos of resource
  type names, or generic nouns that repeat the API's domain) are NOT values
  unless the description explicitly allows that shape.
- Do NOT fill a parameter by grabbing a substring of the sentence that is
  clearly part of "I want to …" rather than an actual identifier or filter value.
- Plural or singular resource-type words (the kind of thing the API returns,
  e.g. the domain noun in the endpoint) are NEVER valid filter values unless
  the user is clearly giving a real person's name or other concrete token
  described by that parameter.
- Keep extracted values in natural language when needed (do NOT convert
  city→IATA or reformat dates here).
- Do NOT guess. If unsure whether a span is a real parameter value, omit it.
- Return ONLY a JSON object of newly found {{param_name: value}} pairs.
- Return {{}} if nothing new was found."""

    parsed = safe_json_parse(llm.invoke(prompt).content) or {}
    return _validate_and_filter_enums(api, parsed)


def get_missing_params(api, collected):
    req = [p for p in api.get("parameters", []) if p.get("required") and p["name"] not in collected]
    opt = [p for p in api.get("parameters", []) if not p.get("required") and p["name"] not in collected]
    return req, opt


def _format_param_line(p):
    """One bullet line describing a parameter, with enum + default if any."""
    line = f"  • {p['name']}: {p.get('description', p['name']).strip()}"
    if p.get("enum"):
        allowed = ", ".join(str(v) for v in p["enum"])
        line += f"\n      Allowed values: {allowed}"
    if "default" in p:
        line += f"\n      Default if skipped: {p['default']}"
    return line


def format_param_ask(required_missing, optional_missing, include_optional=True):
    lines = []
    if required_missing:
        lines.append("Please provide the following:")
        for p in required_missing:
            lines.append(_format_param_line(p))
    if include_optional and optional_missing:
        lines.append("\nYou can also optionally provide:")
        for p in optional_missing:
            lines.append(_format_param_line(p))
    return "\n".join(lines)


def format_optional_offer(api, opt_missing, had_required):
    """
    Copy shown when we reach the optional-filter step. If the API has NO
    required params, say so honestly — don't pretend the user just completed
    a required section.
    """
    if had_required:
        header = "All required details collected!\n\nWould you like to add any optional filters?"
    else:
        header = (
            "This API has no required parameters — only optional filters.\n\n"
            "Do you want to add any of these? (say 'skip' to proceed with defaults)"
        )
    body = "\n".join(_format_param_line(p) for p in opt_missing)
    hint = "\n\n(provide values, or say 'skip' to use the defaults)"
    return f"{header}\n{body}{hint}"


def _validate_and_filter_enums(api, params):
    """
    Drop any extracted value that doesn't match the parameter's `enum`
    (case-insensitive compare). Returns a cleaned dict so the LLM can't
    sneak a topic word into an enum-typed field.
    """
    cleaned = {}
    enum_map = {p["name"]: p["enum"] for p in api.get("parameters", []) if p.get("enum")}
    for name, value in params.items():
        allowed = enum_map.get(name)
        if allowed is None:
            cleaned[name] = value
            continue
        if value is None:
            continue
        sval = str(value).strip()
        match = next(
            (a for a in allowed if str(a).lower() == sval.lower()),
            None,
        )
        if match is not None:
            cleaned[name] = match
    return cleaned


def _drop_unmentioned_enums(api, params, source_text):
    """
    Reject any enum parameter whose chosen value is not literally present
    (case-insensitive substring match) in the user's source text.

    This is the deterministic guard against LLM hallucination — e.g. the
    model picks "Database" just because it's first in the enum list, even
    though the user only said "i want connection profiles". Without this,
    a valid-but-unmentioned enum value would slip through.
    """
    if not source_text or not params:
        return params
    text_low = source_text.lower()
    enum_names = {p["name"] for p in api.get("parameters", []) if p.get("enum")}
    cleaned = {}
    for name, value in params.items():
        if name in enum_names and value is not None:
            sval = str(value).strip().lower()
            if sval and sval not in text_low:
                continue
        cleaned[name] = value
    return cleaned


# ═══════════════════════════════════════════════════════════════
#  PHASE 3 — Natural Language → API Parameters
# ═══════════════════════════════════════════════════════════════

def phase3_convert_params(api, raw_params):
    examples = build_conversion_examples(api)

    specs = json.dumps([
        {"name": p["name"], "type": p.get("type", "string"),
         "description": p.get("description", ""), "raw_value": raw_params[p["name"]]}
        for p in api.get("parameters", []) if p["name"] in raw_params
    ], indent=2)

    prompt = f"""Convert these raw user values into the correct format for the API.
Use each parameter's description to judge whether raw_value is actually the
right KIND of value for that parameter. The registry is the only source of
truth for what each parameter means.

API: {api['id']}  ({api['method']} {api['endpoint']})

Conversion examples (generic shapes; apply only where relevant):
{examples}

Today's date: {TODAY}

Values to convert:
{specs}

Rules:
- Apply conversion examples where they match the parameter description.
- Keep values already in the correct format as-is.
- If raw_value is clearly NOT the type of value described for that parameter
  (e.g. a random word or intent phrase instead of an ID/code/date/email as
  described), omit that parameter entirely from your JSON — do not pass garbage through.
- A bare plural/singular domain noun naming the resource type (not a real
  person name, email, code, or date as the description requires) is invalid —
  omit that parameter.
- When examples in a parameter description show identifier patterns, only
  include the parameter if raw_value plausibly matches that kind of value.
- You MUST output one key for EVERY entry under "Values to convert" with the
  correct API value whenever raw_value is mappable (cities→IATA, dates→YYYY-MM-DD,
  already-valid codes/dates copied as-is). Only omit a key if raw_value is
  clearly wrong for that parameter's description.
- For plain string parameters (name fragments, email, free-text filters), copy
  the trimmed string through when it matches what the description asks for
  (partial name, exact email, etc.); do not drop real names or emails.
- Return ONLY a JSON object {{param_name: converted_value}}."""

    parsed = safe_json_parse(llm_convert.invoke(prompt).content)
    if not parsed or not isinstance(parsed, dict):
        return {}
    return parsed


def apply_conversion_and_reconcile(api, raw_params):
    """
    Run Phase 3 conversion, merge description-driven fallbacks, then drop only
    optional raw keys the pipeline did not convert. Never discard required
    parameters the LLM forgot — that caused infinite 'still need date' loops.
    """
    llm_part = phase3_convert_params(api, raw_params)
    converted = merge_coercion_fallback(api, raw_params, llm_part)
    converted = merge_passthrough_from_raw(api, raw_params, converted)
    optional_names = _optional_param_names(api)
    for k in list(raw_params.keys()):
        if k not in converted and k in optional_names:
            raw_params.pop(k, None)
    for k, v in converted.items():
        raw_params[k] = v
    req_miss, _ = get_missing_params(api, converted)
    return converted, req_miss


def format_confirmation(api, converted):
    """
    Show every parameter the server will receive: values the user gave,
    plus registry defaults for anything they skipped. Makes the confirmation
    screen match exactly what tool_generator will send on the wire.
    """
    lines = [f"  API  : {api['name']}", f"  Call : {api['method']} {api['endpoint']}"]
    for p in api.get("parameters", []):
        name = p["name"]
        tag = "required" if p.get("required") else "optional"
        if name in converted and converted[name] not in (None, ""):
            lines.append(f"  • {name} = {converted[name]}  ({tag})")
        elif "default" in p:
            lines.append(f"  • {name} = {p['default']}  ({tag}, default)")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  PHASE 4 — Execute & Explain in Natural Language
# ═══════════════════════════════════════════════════════════════

def phase4_explain(api, raw_response, original_query):
    prompt = f"""You are a helpful Automation API Assistant.
Explain the following API response in clear, friendly natural language.

API: {api['name']} ({api['id']})
User's request: "{original_query}"

Response:
{raw_response}

Rules:
- Present information clearly using bullet points or short tables where helpful
- Surface the most relevant fields from the response (names, types, IDs, statuses)
- If the response is a list, summarise the count and highlight the top items
- If there's an error or non-2xx status, explain what went wrong simply
- Use ONLY data from the API response — never invent information
- Be concise but complete"""

    return llm.invoke(prompt).content


# ═══════════════════════════════════════════════════════════════
#  MAIN CHAT LOOP — 4-phase state machine
# ═══════════════════════════════════════════════════════════════

STATES = {
    "IDLE":             0,
    "PHASE1_CONFIRM":   1,
    "PHASE2_COLLECT":   2,
    "PHASE2_OPTIONAL":  3,
    "PHASE3_CONFIRM":   4,
}

def chat():
    registry = load_registry()
    apis = registry["apis"]

    tools = generate_tools(REGISTRY_PATH)
    tool_map = {t.name: t for t in tools}
    api_map = {a["id"]: a for a in apis}
    api_catalog = build_api_catalog(apis)

    print("\n🤖  Automation API Assistant")
    print("═" * 42)
    print("Ask me to run any of the registered")
    print("automation APIs. I'll handle login,")
    print("parameter collection, and confirmation.")
    print("Type 'exit' to quit.\n")

    history = []
    state = "IDLE"
    current_api = None
    raw_params = {}
    converted_params = {}
    original_query = ""

    def say(msg):
        print(f"\n🤖 {msg}")
        history.append({"role": "assistant", "content": msg})

    def reset():
        nonlocal state, current_api, raw_params, converted_params, original_query
        state = "IDLE"
        current_api = None
        raw_params = {}
        converted_params = {}
        original_query = ""

    def transition_to_phase3():
        nonlocal state, converted_params
        api = api_map[current_api]
        print("\n⚙️  Converting your input to API parameters...")
        converted, req_miss = apply_conversion_and_reconcile(api, raw_params)
        converted_params = converted
        if req_miss:
            state = "PHASE2_COLLECT"
            say(
                "I couldn't treat part of that as a valid value for this API "
                "(see each parameter's description in the registry).\n\n"
                + format_param_ask(req_miss, [], include_optional=False)
            )
            return
        state = "PHASE3_CONFIRM"
        confirmation = format_confirmation(api, converted_params)
        say(f"Here's what I'll send:\n\n{confirmation}\n\n   Confirm? (yes / no / correct a value)")

    # ── loop ──────────────────────────────────────────────
    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye"):
            print("\n👋 Goodbye!")
            break

        history.append({"role": "user", "content": user_input})

        if user_input.lower() in ("start over", "reset", "cancel", "nevermind", "new"):
            reset()
            say("No problem! What would you like to do?")
            continue

        # ─────────────────────────────────────────────────
        # PHASE 1 — Intent Detection
        # ─────────────────────────────────────────────────
        if state == "IDLE":
            original_query = user_input
            print("\n🔍 Identifying what you need...")

            intent = phase1_detect_intent(user_input, api_catalog, history)
            api_id = intent.get("api_id")

            if not api_id or api_id not in api_map:
                reason = intent.get("reason", "Could you be more specific?")
                say(
                    f"I'm not sure which action you need. {reason}\n\n"
                    "   Try describing the automation task (e.g. 'list centralized\n"
                    "   connection profiles of type Database')."
                )
                continue

            current_api = api_id
            api = api_map[api_id]
            say(
                f'I think you want: "{api["name"]}"\n'
                f'   → {api["description"].strip()}\n\n'
                f"   Is that right? (yes / no)"
            )
            state = "PHASE1_CONFIRM"
            continue

        # ─────────────────────────────────────────────────
        # PHASE 1 — Confirm API choice
        # ─────────────────────────────────────────────────
        if state == "PHASE1_CONFIRM":
            low = user_input.lower()

            if low in ("yes", "y", "yeah", "sure", "ok", "proceed", "go ahead", "correct"):
                api = api_map[current_api]
                raw_params = {}

                if not api.get("parameters"):
                    converted_params = {}
                    transition_to_phase3()
                    continue

                # Only pull REQUIRED params from the first message. Optional
                # filters are asked next (or skipped) so intent text cannot
                # become bogus optional values like name=passengers.
                req_only = _required_param_names(api)
                raw_params = phase2_extract_params(original_query, api, {}, allowed_names=req_only)
                raw_params = _drop_unmentioned_enums(api, raw_params, original_query)
                req_miss, opt_miss = get_missing_params(api, raw_params)

                if req_miss:
                    prefix = ""
                    if raw_params:
                        prefix = (
                            "I picked up some details from your message:\n"
                            f"{json.dumps(raw_params, indent=2)}\n\n"
                        )
                    say(prefix + format_param_ask(req_miss, opt_miss, include_optional=False))
                    state = "PHASE2_COLLECT"
                elif opt_miss:
                    had_required = bool(_required_param_names(api))
                    say(format_optional_offer(api, opt_miss, had_required))
                    state = "PHASE2_OPTIONAL"
                else:
                    transition_to_phase3()
                continue

            if low in ("no", "n", "nope", "wrong"):
                reset()
                say("No problem. Tell me what you'd like to do instead.")
                continue

            # Treat as a correction — re-detect
            original_query = user_input
            print("\n🔍 Re-evaluating...")
            intent = phase1_detect_intent(user_input, api_catalog, history)
            new_id = intent.get("api_id")

            if new_id and new_id in api_map:
                current_api = new_id
                api = api_map[new_id]
                say(
                    f'How about: "{api["name"]}"?\n'
                    f'   → {api["description"].strip()}\n\n'
                    f"   Is that right? (yes / no)"
                )
            else:
                reset()
                say("I couldn't match that. Could you describe what you need?")
            continue

        # ─────────────────────────────────────────────────
        # PHASE 2 — Collect required parameters
        # ─────────────────────────────────────────────────
        if state == "PHASE2_COLLECT":
            api = api_map[current_api]
            extracted = phase2_extract_params(user_input, api, raw_params)
            extracted = _drop_unmentioned_enums(api, extracted, user_input)
            raw_params.update(extracted)

            req_miss, opt_miss = get_missing_params(api, raw_params)

            if req_miss:
                say(format_param_ask(req_miss, [], include_optional=False))
                continue

            if opt_miss:
                state = "PHASE2_OPTIONAL"
                say(format_optional_offer(api, opt_miss, had_required=True))
                continue

            transition_to_phase3()
            continue

        # ─────────────────────────────────────────────────
        # PHASE 2 — Optional parameters
        # ─────────────────────────────────────────────────
        if state == "PHASE2_OPTIONAL":
            api = api_map[current_api]
            low_opt = user_input.lower().strip()
            if low_opt in ("skip", "no", "none", "nah", "n", "no thanks"):
                _strip_optional_params(api, raw_params)
                transition_to_phase3()
                continue

            opt_only = _optional_param_names(api)
            extracted = phase2_extract_params(
                user_input,
                api,
                raw_params,
                allowed_names=opt_only,
                phase="optional_offer",
            )
            extracted = _drop_unmentioned_enums(api, extracted, user_input)

            # Ambiguous affirmatives like "yes", "yes i want to" mean the user
            # intends to add a filter but hasn't actually provided a value yet —
            # re-ask instead of silently proceeding with nothing.
            ambiguous_yes = low_opt in (
                "yes", "y", "yeah", "sure", "ok", "yep", "yup",
            ) or low_opt.startswith(("yes ", "yeah ", "yep "))
            if not extracted and ambiguous_yes:
                _, opt_miss = get_missing_params(api, raw_params)
                say(
                    "Sure — please specify the value you'd like to use:\n"
                    + "\n".join(_format_param_line(p) for p in opt_miss)
                    + "\n\n(or say 'skip' to proceed without it)"
                )
                continue

            raw_params.update(extracted)
            transition_to_phase3()
            continue

        # ─────────────────────────────────────────────────
        # PHASE 3 — Confirm converted parameters
        # ─────────────────────────────────────────────────
        if state == "PHASE3_CONFIRM":
            low = user_input.lower()

            if low in ("yes", "y", "yeah", "sure", "ok", "go", "do it", "proceed", "call it"):
                api = api_map[current_api]

                print("\n⏳ Calling the API...")
                try:
                    result = tool_map[current_api].invoke(json.dumps(converted_params))
                    print("\n📡 Got a response — let me summarise...\n")
                    explanation = phase4_explain(api, result, original_query)
                    say(explanation)
                except Exception as e:
                    say(f"Something went wrong: {e}")

                reset()
                print("\n" + "─" * 42)
                print("What else can I help you with?")
                continue

            if low in ("no", "n", "nope", "cancel", "abort"):
                reset()
                say("Cancelled. What would you like to do instead?")
                continue

            # Treat as a parameter correction (re-scan recent user lines so
            # values like a name from an earlier message are not lost).
            api = api_map[current_api]
            recent_user = [
                m["content"]
                for m in history
                if m.get("role") == "user"
            ][-8:]
            correction_blob = "\n".join(recent_user)
            extracted = phase2_extract_params(
                correction_blob, api, raw_params, phase="confirm_edit"
            )
            extracted = _drop_unmentioned_enums(api, extracted, correction_blob)
            if extracted:
                raw_params.update(extracted)
                print("\n⚙️  Updating parameters...")
                converted, req_miss = apply_conversion_and_reconcile(api, raw_params)
                converted_params = converted
                if req_miss:
                    state = "PHASE2_COLLECT"
                    say(
                        "That still doesn't match what this API expects.\n\n"
                        + format_param_ask(req_miss, [], include_optional=False)
                    )
                else:
                    confirmation = format_confirmation(api, converted_params)
                    say(
                        f"Updated! Here's the revised call:\n\n{confirmation}\n\n"
                        f"   Confirm? (yes / no)"
                    )
            else:
                say("Please say 'yes' to proceed, 'no' to cancel,\nor provide a correction (e.g., 'change origin to Mumbai').")
            continue

    # end while


# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    chat()
